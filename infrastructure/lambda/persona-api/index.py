"""
Persona API Lambda Function

Handles persona management API requests through API Gateway.
Supports CRUD operations for personas and triggers persona agent workflows.
"""
import os
import json
import logging
import uuid
from datetime import datetime
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
PERSONAS_TABLE = os.environ.get('PERSONAS_TABLE', 'brandpoint-personas')
STEP_FUNCTION_NAME = os.environ.get('STEP_FUNCTION_NAME', '')

# Clients
dynamodb = boto3.resource('dynamodb')
sfn_client = boto3.client('stepfunctions')
sts_client = boto3.client('sts')
personas_table = dynamodb.Table(PERSONAS_TABLE)

# Construct Step Function ARN at runtime to avoid circular dependency
_step_function_arn_cache = None

def get_step_function_arn():
    """Construct Step Function ARN at runtime."""
    global _step_function_arn_cache
    if _step_function_arn_cache:
        return _step_function_arn_cache

    if not STEP_FUNCTION_NAME:
        return None

    region = os.environ.get('AWS_REGION', 'us-east-1')
    account_id = sts_client.get_caller_identity()['Account']
    _step_function_arn_cache = f"arn:aws:states:{region}:{account_id}:stateMachine:{STEP_FUNCTION_NAME}"
    return _step_function_arn_cache


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def handler(event, context):
    """
    Handle persona API requests.

    API Gateway Event:
        - GET /personas - List all personas
        - GET /personas/{personaId} - Get persona details
        - POST /personas - Create new persona
        - PUT /personas/{personaId} - Update persona
        - DELETE /personas/{personaId} - Delete persona
        - POST /personas/{personaId}/execute - Execute persona agent
        - GET /personas/{personaId}/results - Get persona results
    """
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '')
    path_params = event.get('pathParameters', {}) or {}
    body = json.loads(event.get('body', '{}')) if event.get('body') else {}
    query_params = event.get('queryStringParameters', {}) or {}

    persona_id = path_params.get('personaId', '')

    logger.info(f"Persona API: {http_method} {path}")

    try:
        # Route based on path and method
        if path == '/personas' or path == '/personas/':
            if http_method == 'GET':
                return list_personas(query_params)
            elif http_method == 'POST':
                return create_persona(body)

        elif '/execute' in path:
            return execute_persona(persona_id, body)

        elif '/results' in path:
            return get_persona_results(persona_id, query_params)

        elif persona_id:
            if http_method == 'GET':
                return get_persona(persona_id)
            elif http_method == 'PUT':
                return update_persona(persona_id, body)
            elif http_method == 'DELETE':
                return delete_persona(persona_id)

        return api_response(404, {'error': 'Not found'})

    except ValueError as e:
        return api_response(400, {'error': str(e)})
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return api_response(500, {'error': 'Database error'})
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return api_response(500, {'error': 'Internal server error'})


def list_personas(query_params: dict) -> dict:
    """List all personas with optional filtering."""
    brand_id = query_params.get('brandId', '')
    client_id = query_params.get('clientId', '')
    limit = min(int(query_params.get('limit', 50)), 100)

    # Build filter expression
    filter_parts = []
    expression_values = {}

    if brand_id:
        filter_parts.append('brandId = :brandId')
        expression_values[':brandId'] = brand_id

    if client_id:
        filter_parts.append('clientId = :clientId')
        expression_values[':clientId'] = client_id

    scan_kwargs = {'Limit': limit}
    if filter_parts:
        scan_kwargs['FilterExpression'] = ' AND '.join(filter_parts)
        scan_kwargs['ExpressionAttributeValues'] = expression_values

    response = personas_table.scan(**scan_kwargs)
    items = response.get('Items', [])

    return api_response(200, {
        'personas': json.loads(json.dumps(items, cls=DecimalEncoder)),
        'count': len(items)
    })


def get_persona(persona_id: str) -> dict:
    """Get persona by ID."""
    response = personas_table.get_item(Key={'personaId': persona_id})
    item = response.get('Item')

    if not item:
        return api_response(404, {'error': 'Persona not found'})

    return api_response(200, {
        'persona': json.loads(json.dumps(item, cls=DecimalEncoder))
    })


def create_persona(body: dict) -> dict:
    """Create new persona."""
    required_fields = ['name', 'brandId']
    for field in required_fields:
        if field not in body:
            raise ValueError(f"{field} is required")

    persona_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + 'Z'

    persona = {
        'personaId': persona_id,
        'name': body['name'],
        'brandId': body['brandId'],
        'clientId': body.get('clientId', ''),
        'description': body.get('description', ''),
        'demographics': body.get('demographics', {}),
        'interests': body.get('interests', []),
        'painPoints': body.get('painPoints', []),
        'searchBehavior': body.get('searchBehavior', {}),
        'preferredEngines': body.get('preferredEngines', ['chatgpt', 'perplexity', 'gemini', 'claude']),
        'queryTemplates': body.get('queryTemplates', []),
        'isActive': body.get('isActive', True),
        'createdAt': timestamp,
        'updatedAt': timestamp
    }

    personas_table.put_item(Item=persona)

    logger.info(f"Created persona: {persona_id}")

    return api_response(201, {
        'persona': persona,
        'message': 'Persona created successfully'
    })


def update_persona(persona_id: str, body: dict) -> dict:
    """Update existing persona."""
    # Check if persona exists
    existing = personas_table.get_item(Key={'personaId': persona_id})
    if not existing.get('Item'):
        return api_response(404, {'error': 'Persona not found'})

    # Build update expression
    update_parts = []
    expression_names = {}
    expression_values = {':updatedAt': datetime.utcnow().isoformat() + 'Z'}

    updatable_fields = [
        'name', 'description', 'demographics', 'interests', 'painPoints',
        'searchBehavior', 'preferredEngines', 'queryTemplates', 'isActive'
    ]

    for field in updatable_fields:
        if field in body:
            update_parts.append(f"#{field} = :{field}")
            expression_names[f"#{field}"] = field
            expression_values[f":{field}"] = body[field]

    update_parts.append("#updatedAt = :updatedAt")
    expression_names["#updatedAt"] = "updatedAt"

    response = personas_table.update_item(
        Key={'personaId': persona_id},
        UpdateExpression='SET ' + ', '.join(update_parts),
        ExpressionAttributeNames=expression_names,
        ExpressionAttributeValues=expression_values,
        ReturnValues='ALL_NEW'
    )

    logger.info(f"Updated persona: {persona_id}")

    return api_response(200, {
        'persona': json.loads(json.dumps(response['Attributes'], cls=DecimalEncoder)),
        'message': 'Persona updated successfully'
    })


def delete_persona(persona_id: str) -> dict:
    """Delete persona."""
    # Check if persona exists
    existing = personas_table.get_item(Key={'personaId': persona_id})
    if not existing.get('Item'):
        return api_response(404, {'error': 'Persona not found'})

    personas_table.delete_item(Key={'personaId': persona_id})

    logger.info(f"Deleted persona: {persona_id}")

    return api_response(200, {
        'message': 'Persona deleted successfully',
        'personaId': persona_id
    })


def execute_persona(persona_id: str, body: dict) -> dict:
    """Execute persona agent workflow."""
    step_function_arn = get_step_function_arn()
    if not step_function_arn:
        return api_response(503, {'error': 'Workflow execution not configured'})

    # Get persona
    response = personas_table.get_item(Key={'personaId': persona_id})
    persona = response.get('Item')

    if not persona:
        return api_response(404, {'error': 'Persona not found'})

    # Prepare workflow input
    execution_input = {
        'personaId': persona_id,
        'persona': json.loads(json.dumps(persona, cls=DecimalEncoder)),
        'brandContext': body.get('brandContext', {}),
        'options': body.get('options', {}),
        'requestedAt': datetime.utcnow().isoformat() + 'Z'
    }

    # Start Step Functions execution
    execution_name = f"persona-{persona_id[:8]}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    try:
        sfn_response = sfn_client.start_execution(
            stateMachineArn=step_function_arn,
            name=execution_name,
            input=json.dumps(execution_input)
        )

        logger.info(f"Started execution: {sfn_response['executionArn']}")

        return api_response(202, {
            'message': 'Persona agent execution started',
            'executionArn': sfn_response['executionArn'],
            'executionName': execution_name,
            'personaId': persona_id,
            'startedAt': sfn_response['startDate'].isoformat()
        })

    except ClientError as e:
        logger.error(f"Failed to start execution: {e}")
        return api_response(500, {'error': 'Failed to start workflow execution'})


def get_persona_results(persona_id: str, query_params: dict) -> dict:
    """Get execution results for a persona."""
    # This would query the results table
    # For now, return a stub
    limit = min(int(query_params.get('limit', 10)), 50)

    return api_response(200, {
        'personaId': persona_id,
        'results': [],
        'message': 'Query results table for actual results'
    })


def api_response(status_code: int, body: dict) -> dict:
    """Format API Gateway response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key'
        },
        'body': json.dumps(body)
    }
