"""
Store Results Lambda Function

Stores persona agent execution results to DynamoDB and optionally
syncs to the Hub API for external consumption.
"""
import os
import json
import logging
import uuid
from datetime import datetime
from decimal import Decimal
import boto3
import requests
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
RESULTS_TABLE = os.environ.get('RESULTS_TABLE', 'brandpoint-query-results')
HUB_API_URL = os.environ.get('HUB_API_URL', '')
HUB_API_SECRET = os.environ.get('HUB_API_SECRET', '')

# Clients
dynamodb = boto3.resource('dynamodb')
secrets_client = boto3.client('secretsmanager')
results_table = dynamodb.Table(RESULTS_TABLE)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def handler(event, context):
    """
    Store analysis results.

    Input:
        {
            "overallVisibility": 0.45,
            "queryResults": [...],
            "engineBreakdown": {...},
            "insights": [...],
            "persona": {...},
            "brandContext": {...},
            "executionId": "uuid"
        }

    Output:
        {
            "resultId": "uuid",
            "stored": true,
            "syncedToHub": true/false
        }
    """
    execution_id = event.get('executionId', str(uuid.uuid4()))
    overall_visibility = event.get('overallVisibility', 0.0)
    query_results = event.get('queryResults', [])
    engine_breakdown = event.get('engineBreakdown', {})
    insights = event.get('insights', [])
    persona = event.get('persona', {})
    brand_context = event.get('brandContext', {})

    brand_id = brand_context.get('brandId', persona.get('brandId', 'unknown'))
    client_id = brand_context.get('clientId', '')

    logger.info(f"Storing results for execution: {execution_id}")

    result_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + 'Z'

    # Prepare result record
    result_record = {
        'resultId': result_id,
        'executionId': execution_id,
        'brandId': brand_id,
        'clientId': client_id,
        'timestamp': timestamp,
        'overallVisibility': Decimal(str(overall_visibility)),
        'queryCount': len(query_results),
        'insights': insights,
        'engineBreakdown': json.loads(json.dumps(engine_breakdown), parse_float=Decimal),
        'personaId': persona.get('personaId', ''),
        'personaName': persona.get('name', ''),
        'ttl': int(datetime.utcnow().timestamp()) + (90 * 24 * 60 * 60)  # 90 days
    }

    # Store summary in DynamoDB
    try:
        results_table.put_item(Item=result_record)
        logger.info(f"Stored result summary: {result_id}")
    except ClientError as e:
        logger.error(f"Error storing result: {e}")
        raise

    # Store individual query results
    store_query_results(execution_id, query_results)

    # Sync to Hub API if configured
    synced_to_hub = False
    if HUB_API_URL:
        synced_to_hub = sync_to_hub(result_record, query_results)

    return {
        'resultId': result_id,
        'executionId': execution_id,
        'stored': True,
        'syncedToHub': synced_to_hub,
        'timestamp': timestamp
    }


def store_query_results(execution_id: str, query_results: list):
    """Store individual query results."""
    if not query_results:
        return

    # Use batch write for efficiency
    with results_table.batch_writer() as batch:
        for i, result in enumerate(query_results):
            item = {
                'resultId': f"{execution_id}#query#{i}",
                'executionId': execution_id,
                'recordType': 'query_result',
                'query': result.get('query', ''),
                'engine': result.get('engine', ''),
                'brandMentioned': result.get('brandMentioned', False),
                'visibilityScore': Decimal(str(result.get('visibilityScore', 0))),
                'sentiment': result.get('sentiment', 'neutral'),
                'position': result.get('position'),
                'mentionContext': result.get('mentionContext'),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'ttl': int(datetime.utcnow().timestamp()) + (90 * 24 * 60 * 60)
            }
            batch.put_item(Item=item)

    logger.info(f"Stored {len(query_results)} query results")


def sync_to_hub(result_record: dict, query_results: list) -> bool:
    """Sync results to Hub API."""
    try:
        # Get Hub API key
        api_key = get_hub_api_key()
        if not api_key:
            logger.warning("Hub API key not configured, skipping sync")
            return False

        headers = {
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'resultId': result_record['resultId'],
            'executionId': result_record['executionId'],
            'brandId': result_record['brandId'],
            'clientId': result_record['clientId'],
            'timestamp': result_record['timestamp'],
            'overallVisibility': float(result_record['overallVisibility']),
            'queryCount': result_record['queryCount'],
            'insights': result_record['insights'],
            'engineBreakdown': json.loads(json.dumps(result_record['engineBreakdown'], cls=DecimalEncoder)),
            'queryResults': query_results
        }

        response = requests.post(
            f"{HUB_API_URL}/api/AiPrediction/persona-results",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code in [200, 201]:
            logger.info(f"Successfully synced to Hub API")
            return True
        else:
            logger.warning(f"Hub API returned status {response.status_code}: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error syncing to Hub API: {e}")
        return False


def get_hub_api_key() -> str:
    """Retrieve Hub API key from Secrets Manager."""
    if not HUB_API_SECRET:
        return ''

    try:
        response = secrets_client.get_secret_value(SecretId=HUB_API_SECRET)
        secret = json.loads(response['SecretString'])
        return secret.get('apiKey', '')
    except ClientError as e:
        logger.error(f"Error retrieving Hub API secret: {e}")
        return ''
