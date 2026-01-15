"""
Common utilities for Brandpoint AI Platform Lambda functions.
"""
import json
import os
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

# AWS Clients (lazy initialization)
_clients = {}


def get_client(service_name: str, region: str = None):
    """Get or create a boto3 client."""
    key = f"{service_name}:{region}"
    if key not in _clients:
        _clients[key] = boto3.client(service_name, region_name=region)
    return _clients[key]


def get_resource(service_name: str, region: str = None):
    """Get or create a boto3 resource."""
    key = f"{service_name}:resource:{region}"
    if key not in _clients:
        _clients[key] = boto3.resource(service_name, region_name=region)
    return _clients[key]


def get_secret(secret_name: str) -> Dict[str, Any]:
    """Retrieve a secret from AWS Secrets Manager."""
    client = get_client('secretsmanager')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        logger.error(f"Error retrieving secret {secret_name}: {e}")
        raise


def invoke_bedrock(
    model_id: str,
    prompt: str,
    system_prompt: str = None,
    max_tokens: int = 4096,
    temperature: float = 0.7
) -> str:
    """Invoke a Bedrock model and return the response text."""
    client = get_client('bedrock-runtime')

    messages = [{"role": "user", "content": prompt}]

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": messages,
        "temperature": temperature
    }

    if system_prompt:
        body["system"] = system_prompt

    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']


def invoke_bedrock_embeddings(model_id: str, text: str) -> list:
    """Generate embeddings using Bedrock Titan."""
    client = get_client('bedrock-runtime')

    body = {
        "inputText": text
    }

    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(response['body'].read())
    return response_body['embedding']


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def json_response(status_code: int, body: Any, headers: Dict = None) -> Dict:
    """Create an API Gateway response."""
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }
    if headers:
        response['headers'].update(headers)
    return response


def parse_event_body(event: Dict) -> Dict:
    """Parse the body from an API Gateway event."""
    body = event.get('body', '{}')
    if isinstance(body, str):
        return json.loads(body) if body else {}
    return body


def get_path_parameter(event: Dict, param: str) -> Optional[str]:
    """Get a path parameter from an API Gateway event."""
    params = event.get('pathParameters', {}) or {}
    return params.get(param)


def get_query_parameter(event: Dict, param: str, default: Any = None) -> Any:
    """Get a query string parameter from an API Gateway event."""
    params = event.get('queryStringParameters', {}) or {}
    return params.get(param, default)


def now_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def generate_id(prefix: str = '') -> str:
    """Generate a unique ID."""
    import uuid
    unique = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    return f"{prefix}{timestamp}-{unique}" if prefix else f"{timestamp}-{unique}"
