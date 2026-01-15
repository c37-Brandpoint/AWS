"""
Health Check Lambda Function

Provides health status for the Brandpoint API and its dependencies.
Used by API Gateway /health endpoint and CloudWatch monitoring.
"""
import os
import json
import logging
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
PERSONAS_TABLE = os.environ.get('PERSONAS_TABLE', 'brandpoint-personas')
RESULTS_TABLE = os.environ.get('RESULTS_TABLE', 'brandpoint-query-results')
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT', '')
NEPTUNE_ENDPOINT = os.environ.get('NEPTUNE_ENDPOINT', '')

# Clients
dynamodb = boto3.client('dynamodb')


def handler(event, context):
    """
    Handle health check requests.

    API Gateway Event:
        - GET /health - Basic health check
        - GET /health/detailed - Detailed dependency checks

    Output:
        {
            "status": "healthy",
            "timestamp": "...",
            "version": "1.0.0",
            "dependencies": {...}
        }
    """
    path = event.get('path', '/health')
    query_params = event.get('queryStringParameters', {}) or {}

    detailed = '/detailed' in path or query_params.get('detailed', '').lower() == 'true'

    logger.info(f"Health check: detailed={detailed}")

    timestamp = datetime.utcnow().isoformat() + 'Z'

    # Basic health response
    health_response = {
        'status': 'healthy',
        'timestamp': timestamp,
        'version': os.environ.get('VERSION', '1.0.0'),
        'environment': os.environ.get('ENVIRONMENT', 'development'),
        'region': os.environ.get('AWS_REGION', 'us-east-1')
    }

    if detailed:
        # Check all dependencies
        dependencies = check_dependencies()
        health_response['dependencies'] = dependencies

        # Determine overall status
        unhealthy_count = sum(1 for d in dependencies.values() if d['status'] != 'healthy')
        if unhealthy_count > 0:
            if unhealthy_count == len(dependencies):
                health_response['status'] = 'unhealthy'
            else:
                health_response['status'] = 'degraded'

    # Return appropriate status code
    status_code = 200
    if health_response['status'] == 'unhealthy':
        status_code = 503
    elif health_response['status'] == 'degraded':
        status_code = 207  # Multi-Status

    return api_response(status_code, health_response)


def check_dependencies() -> dict:
    """Check health of all dependencies."""
    dependencies = {}

    # Check DynamoDB tables
    dependencies['dynamodb_personas'] = check_dynamodb(PERSONAS_TABLE)
    dependencies['dynamodb_results'] = check_dynamodb(RESULTS_TABLE)

    # Check OpenSearch
    if OPENSEARCH_ENDPOINT:
        dependencies['opensearch'] = check_opensearch()
    else:
        dependencies['opensearch'] = {
            'status': 'not_configured',
            'message': 'OpenSearch endpoint not configured'
        }

    # Check Neptune
    if NEPTUNE_ENDPOINT:
        dependencies['neptune'] = check_neptune()
    else:
        dependencies['neptune'] = {
            'status': 'not_configured',
            'message': 'Neptune endpoint not configured'
        }

    # Check Bedrock
    dependencies['bedrock'] = check_bedrock()

    # Check Secrets Manager
    dependencies['secrets_manager'] = check_secrets_manager()

    return dependencies


def check_dynamodb(table_name: str) -> dict:
    """Check DynamoDB table health."""
    try:
        response = dynamodb.describe_table(TableName=table_name)
        table_status = response['Table']['TableStatus']

        if table_status == 'ACTIVE':
            return {
                'status': 'healthy',
                'table': table_name,
                'tableStatus': table_status,
                'itemCount': response['Table'].get('ItemCount', 0)
            }
        else:
            return {
                'status': 'degraded',
                'table': table_name,
                'tableStatus': table_status,
                'message': f'Table status is {table_status}'
            }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        return {
            'status': 'unhealthy',
            'table': table_name,
            'error': error_code,
            'message': str(e)
        }


def check_opensearch() -> dict:
    """Check OpenSearch cluster health."""
    try:
        # Use requests to check OpenSearch health
        # In production, use OpenSearch client
        from opensearchpy import OpenSearch, RequestsHttpConnection
        from requests_aws4auth import AWS4Auth

        credentials = boto3.Session().get_credentials()
        region = os.environ.get('AWS_REGION', 'us-east-1')

        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            'es',
            session_token=credentials.token
        )

        client = OpenSearch(
            hosts=[{'host': OPENSEARCH_ENDPOINT.replace('https://', ''), 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=5
        )

        health = client.cluster.health()

        status = 'healthy' if health['status'] == 'green' else (
            'degraded' if health['status'] == 'yellow' else 'unhealthy'
        )

        return {
            'status': status,
            'clusterStatus': health['status'],
            'numberOfNodes': health.get('number_of_nodes', 0),
            'activeShards': health.get('active_shards', 0)
        }

    except ImportError:
        return {
            'status': 'degraded',
            'message': 'OpenSearch client not available'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }


def check_neptune() -> dict:
    """Check Neptune cluster health."""
    try:
        from gremlin_python.driver import client, serializer

        gremlin = client.Client(
            f'wss://{NEPTUNE_ENDPOINT}:8182/gremlin',
            'g',
            message_serializer=serializer.GraphSONSerializersV2d0()
        )

        # Simple query to check connectivity
        result = gremlin.submit('g.V().count()').all().result()

        return {
            'status': 'healthy',
            'vertexCount': result[0] if result else 0
        }

    except ImportError:
        return {
            'status': 'degraded',
            'message': 'Gremlin client not available'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }


def check_bedrock() -> dict:
    """Check Bedrock availability."""
    try:
        bedrock = boto3.client('bedrock-runtime')
        # Just check if we can create the client
        return {
            'status': 'healthy',
            'message': 'Bedrock client initialized'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }


def check_secrets_manager() -> dict:
    """Check Secrets Manager availability."""
    try:
        secrets = boto3.client('secretsmanager')
        # List secrets to verify access (limit to 1)
        secrets.list_secrets(MaxResults=1)
        return {
            'status': 'healthy',
            'message': 'Secrets Manager accessible'
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            return {
                'status': 'degraded',
                'message': 'Limited access to Secrets Manager'
            }
        return {
            'status': 'unhealthy',
            'error': error_code
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }


def api_response(status_code: int, body: dict) -> dict:
    """Format API Gateway response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        },
        'body': json.dumps(body)
    }
