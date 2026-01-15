"""
Load Persona Lambda Function

Retrieves a persona definition from DynamoDB for use in the persona agent workflow.
"""
import os
import logging
import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
PERSONAS_TABLE = os.environ.get('PERSONAS_TABLE', 'brandpoint-ai-dev-personas')

# DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(PERSONAS_TABLE)


def handler(event, context):
    """
    Load a persona definition from DynamoDB.

    Input:
        {
            "personaId": "us-army-prospect-male-18-24"
        }

    Output:
        {
            "personaId": "us-army-prospect-male-18-24",
            "clientId": "123",
            "brandId": "us-army",
            "demographics": {...},
            "psychographics": {...},
            "queryPatterns": {...}
        }
    """
    logger.info(f"Loading persona: {event}")

    persona_id = event.get('personaId')

    if not persona_id:
        raise ValueError("personaId is required")

    # Handle special case for scheduled execution
    if persona_id == 'scheduled-execution' and event.get('executeAll'):
        return load_all_active_personas()

    # Load single persona
    try:
        response = table.get_item(
            Key={'personaId': persona_id}
        )

        if 'Item' not in response:
            raise ValueError(f"Persona '{persona_id}' not found")

        persona = response['Item']
        logger.info(f"Successfully loaded persona: {persona_id}")

        return persona

    except Exception as e:
        logger.error(f"Error loading persona {persona_id}: {e}")
        raise


def load_all_active_personas():
    """
    Load all active personas for scheduled batch execution.

    Returns a list of personas to be processed.
    """
    logger.info("Loading all active personas for scheduled execution")

    try:
        # Scan for all active personas
        response = table.scan(
            FilterExpression='#status = :active',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':active': 'active'}
        )

        personas = response.get('Items', [])

        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression='#status = :active',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':active': 'active'},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            personas.extend(response.get('Items', []))

        logger.info(f"Loaded {len(personas)} active personas")

        return {
            'personas': personas,
            'count': len(personas),
            'executionMode': 'batch'
        }

    except Exception as e:
        logger.error(f"Error loading active personas: {e}")
        raise
