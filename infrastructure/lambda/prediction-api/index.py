"""
Prediction API Lambda Function

Handles prediction requests through the API Gateway.
Invokes SageMaker endpoints for ML inference.
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
SAGEMAKER_ENDPOINT = os.environ.get('SAGEMAKER_ENDPOINT', 'brandpoint-prediction')
FEATURE_EXTRACTION_FUNCTION = os.environ.get('FEATURE_EXTRACTION_FUNCTION', '')

# Clients
sagemaker_runtime = boto3.client('sagemaker-runtime')
lambda_client = boto3.client('lambda')


def handler(event, context):
    """
    Handle prediction API requests.

    API Gateway Event:
        - POST /prediction/visibility - Predict visibility score
        - POST /prediction/sentiment - Predict sentiment
        - POST /prediction/engagement - Predict engagement
        - GET /prediction/models - List available models
    """
    http_method = event.get('httpMethod', 'POST')
    path = event.get('path', '')
    body = json.loads(event.get('body', '{}')) if event.get('body') else {}
    query_params = event.get('queryStringParameters', {}) or {}

    logger.info(f"Prediction API: {http_method} {path}")

    try:
        if path.endswith('/visibility'):
            return predict_visibility(body)
        elif path.endswith('/sentiment'):
            return predict_sentiment(body)
        elif path.endswith('/engagement'):
            return predict_engagement(body)
        elif path.endswith('/models'):
            return list_models()
        elif path.endswith('/batch'):
            return batch_predict(body)
        else:
            return api_response(404, {'error': 'Not found'})

    except ValueError as e:
        return api_response(400, {'error': str(e)})
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return api_response(500, {'error': 'Internal server error'})


def predict_visibility(body: dict) -> dict:
    """Predict brand visibility score for content."""
    content = body.get('content', '')
    brand_id = body.get('brandId', '')
    metadata = body.get('metadata', {})

    if not content:
        raise ValueError("content is required")

    # Extract features
    features = extract_features(content, metadata)

    # Invoke SageMaker endpoint
    prediction = invoke_endpoint(
        endpoint_name=SAGEMAKER_ENDPOINT,
        payload={
            'features': features,
            'predictionType': 'visibility'
        }
    )

    return api_response(200, {
        'prediction': {
            'visibilityScore': prediction.get('score', 0),
            'confidence': prediction.get('confidence', 0),
            'factors': prediction.get('factors', []),
            'recommendations': prediction.get('recommendations', [])
        },
        'brandId': brand_id,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


def predict_sentiment(body: dict) -> dict:
    """Predict sentiment of content."""
    content = body.get('content', '')
    target_entity = body.get('targetEntity', '')

    if not content:
        raise ValueError("content is required")

    # Extract features
    features = extract_features(content, {'targetEntity': target_entity})

    # Invoke SageMaker endpoint
    prediction = invoke_endpoint(
        endpoint_name=SAGEMAKER_ENDPOINT,
        payload={
            'features': features,
            'predictionType': 'sentiment'
        }
    )

    return api_response(200, {
        'prediction': {
            'sentiment': prediction.get('sentiment', 'neutral'),
            'sentimentScore': prediction.get('score', 0),
            'confidence': prediction.get('confidence', 0),
            'aspects': prediction.get('aspects', [])
        },
        'targetEntity': target_entity,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


def predict_engagement(body: dict) -> dict:
    """Predict engagement potential for content."""
    content = body.get('content', '')
    content_type = body.get('contentType', 'article')
    platform = body.get('platform', 'general')

    if not content:
        raise ValueError("content is required")

    # Extract features
    features = extract_features(content, {
        'contentType': content_type,
        'platform': platform
    })

    # Invoke SageMaker endpoint
    prediction = invoke_endpoint(
        endpoint_name=SAGEMAKER_ENDPOINT,
        payload={
            'features': features,
            'predictionType': 'engagement'
        }
    )

    return api_response(200, {
        'prediction': {
            'engagementScore': prediction.get('score', 0),
            'confidence': prediction.get('confidence', 0),
            'engagementFactors': prediction.get('factors', []),
            'optimizations': prediction.get('optimizations', [])
        },
        'contentType': content_type,
        'platform': platform,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


def batch_predict(body: dict) -> dict:
    """Handle batch prediction requests."""
    items = body.get('items', [])
    prediction_type = body.get('predictionType', 'visibility')

    if not items:
        raise ValueError("items array is required")
    if len(items) > 100:
        raise ValueError("Maximum 100 items per batch")

    results = []
    for item in items:
        try:
            content = item.get('content', '')
            if not content:
                results.append({
                    'id': item.get('id'),
                    'error': 'content is required'
                })
                continue

            features = extract_features(content, item.get('metadata', {}))
            prediction = invoke_endpoint(
                endpoint_name=SAGEMAKER_ENDPOINT,
                payload={
                    'features': features,
                    'predictionType': prediction_type
                }
            )

            results.append({
                'id': item.get('id'),
                'prediction': prediction
            })

        except Exception as e:
            results.append({
                'id': item.get('id'),
                'error': str(e)
            })

    return api_response(200, {
        'results': results,
        'totalProcessed': len(results),
        'successCount': sum(1 for r in results if 'prediction' in r),
        'errorCount': sum(1 for r in results if 'error' in r),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


def list_models() -> dict:
    """List available prediction models."""
    models = [
        {
            'id': 'visibility-v1',
            'name': 'Visibility Predictor',
            'description': 'Predicts brand visibility score in AI responses',
            'inputType': 'text',
            'outputType': 'score'
        },
        {
            'id': 'sentiment-v1',
            'name': 'Sentiment Analyzer',
            'description': 'Analyzes sentiment towards target entities',
            'inputType': 'text',
            'outputType': 'classification'
        },
        {
            'id': 'engagement-v1',
            'name': 'Engagement Predictor',
            'description': 'Predicts content engagement potential',
            'inputType': 'text',
            'outputType': 'score'
        }
    ]

    return api_response(200, {
        'models': models,
        'defaultEndpoint': SAGEMAKER_ENDPOINT
    })


def extract_features(content: str, metadata: dict) -> dict:
    """Extract features using feature extraction Lambda."""
    if FEATURE_EXTRACTION_FUNCTION:
        try:
            response = lambda_client.invoke(
                FunctionName=FEATURE_EXTRACTION_FUNCTION,
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'content': content,
                    'contentType': metadata.get('contentType', 'article'),
                    'metadata': metadata
                })
            )

            result = json.loads(response['Payload'].read())
            return result.get('features', {})

        except Exception as e:
            logger.warning(f"Feature extraction failed, using basic features: {e}")

    # Fallback to basic features
    return {
        'wordCount': len(content.split()),
        'charCount': len(content),
        'contentPreview': content[:500]
    }


def invoke_endpoint(endpoint_name: str, payload: dict) -> dict:
    """Invoke SageMaker endpoint."""
    try:
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )

        result = json.loads(response['Body'].read())
        return result

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ModelError':
            logger.error(f"Model error: {e}")
            return {'score': 0, 'confidence': 0, 'error': 'Model error'}
        raise


def api_response(status_code: int, body: dict) -> dict:
    """Format API Gateway response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key'
        },
        'body': json.dumps(body)
    }
