"""
Execute Query Lambda Function

Executes a search query against various AI engines (ChatGPT, Perplexity, Gemini, Claude).
The specific engine is determined by the ENGINE environment variable.
"""
import os
import json
import logging
import time
import boto3
import requests
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
ENGINE = os.environ.get('ENGINE', 'chatgpt')
SECRET_NAME = os.environ.get('SECRET_NAME', '')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')

# Clients
secrets_client = boto3.client('secretsmanager')
bedrock_client = boto3.client('bedrock-runtime')

# Cache for API keys
_api_key_cache = {}


def handler(event, context):
    """
    Execute a query against an AI engine.

    Input:
        {
            "query": "is joining the army worth it in 2025",
            "persona": {...},
            "engine": "chatgpt"  # Optional, uses ENV if not provided
        }

    Output:
        {
            "response": "...",
            "engine": "chatgpt",
            "query": "...",
            "latencyMs": 1234,
            "success": true
        }
    """
    query = event.get('query')
    engine = event.get('engine', ENGINE)
    persona = event.get('persona', {})

    if not query:
        raise ValueError("query is required")

    logger.info(f"Executing query on {engine}: {query[:50]}...")

    start_time = time.time()

    try:
        # Route to appropriate engine
        if engine == 'chatgpt':
            response = execute_chatgpt(query)
        elif engine == 'perplexity':
            response = execute_perplexity(query)
        elif engine == 'gemini':
            response = execute_gemini(query)
        elif engine == 'claude':
            response = execute_claude(query)
        else:
            raise ValueError(f"Unknown engine: {engine}")

        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Query executed successfully on {engine} in {latency_ms}ms")

        return {
            'response': response,
            'engine': engine,
            'query': query,
            'latencyMs': latency_ms,
            'success': True
        }

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Error executing query on {engine}: {e}")

        return {
            'response': None,
            'engine': engine,
            'query': query,
            'latencyMs': latency_ms,
            'success': False,
            'error': str(e)
        }


def get_api_key(secret_name: str) -> str:
    """Retrieve API key from Secrets Manager with caching."""
    if secret_name in _api_key_cache:
        return _api_key_cache[secret_name]

    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        api_key = secret.get('apiKey', '')
        _api_key_cache[secret_name] = api_key
        return api_key
    except ClientError as e:
        logger.error(f"Error retrieving secret {secret_name}: {e}")
        raise


def execute_chatgpt(query: str) -> str:
    """Execute query against OpenAI ChatGPT API."""
    api_key = get_api_key(SECRET_NAME)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'gpt-4-turbo-preview',
        'messages': [
            {
                'role': 'user',
                'content': query
            }
        ],
        'max_tokens': 2048,
        'temperature': 0.7
    }

    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers,
        json=data,
        timeout=60
    )
    response.raise_for_status()

    result = response.json()
    return result['choices'][0]['message']['content']


def execute_perplexity(query: str) -> str:
    """Execute query against Perplexity API."""
    api_key = get_api_key(SECRET_NAME)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'llama-3.1-sonar-large-128k-online',
        'messages': [
            {
                'role': 'user',
                'content': query
            }
        ],
        'max_tokens': 2048,
        'temperature': 0.7
    }

    response = requests.post(
        'https://api.perplexity.ai/chat/completions',
        headers=headers,
        json=data,
        timeout=60
    )
    response.raise_for_status()

    result = response.json()
    return result['choices'][0]['message']['content']


def execute_gemini(query: str) -> str:
    """Execute query against Google Gemini API."""
    api_key = get_api_key(SECRET_NAME)

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        'contents': [
            {
                'parts': [
                    {'text': query}
                ]
            }
        ],
        'generationConfig': {
            'maxOutputTokens': 2048,
            'temperature': 0.7
        }
    }

    response = requests.post(
        f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}',
        headers=headers,
        json=data,
        timeout=60
    )
    response.raise_for_status()

    result = response.json()
    return result['candidates'][0]['content']['parts'][0]['text']


def execute_claude(query: str) -> str:
    """Execute query against Claude via AWS Bedrock."""
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "temperature": 0.7,
        "messages": [
            {"role": "user", "content": query}
        ]
    }

    response = bedrock_client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']
