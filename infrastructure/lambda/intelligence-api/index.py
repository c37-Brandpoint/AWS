"""
Intelligence API Lambda Function

Handles intelligence engine API requests through API Gateway.
Provides access to graph queries, similarity search, and insights.
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
SIMILARITY_SEARCH_FUNCTION = os.environ.get('SIMILARITY_SEARCH_FUNCTION', '')
GRAPH_QUERY_FUNCTION = os.environ.get('GRAPH_QUERY_FUNCTION', '')
INSIGHTS_GENERATOR_FUNCTION = os.environ.get('INSIGHTS_GENERATOR_FUNCTION', '')
CONTENT_INGESTION_FUNCTION = os.environ.get('CONTENT_INGESTION_FUNCTION', '')

# Clients
lambda_client = boto3.client('lambda')


def handler(event, context):
    """
    Handle intelligence API requests.

    API Gateway Event:
        - POST /intelligence/search - Similarity search
        - POST /intelligence/graph - Graph queries
        - POST /intelligence/insights - Generate insights
        - POST /intelligence/ingest - Ingest content
        - GET /intelligence/entities/{entityId} - Get entity details
        - GET /intelligence/topics - List trending topics
    """
    http_method = event.get('httpMethod', 'POST')
    path = event.get('path', '')
    path_params = event.get('pathParameters', {}) or {}
    body = json.loads(event.get('body', '{}')) if event.get('body') else {}
    query_params = event.get('queryStringParameters', {}) or {}

    logger.info(f"Intelligence API: {http_method} {path}")

    try:
        if '/search' in path:
            return handle_search(body)
        elif '/graph' in path:
            return handle_graph_query(body)
        elif '/insights' in path:
            return handle_insights(body)
        elif '/ingest' in path:
            return handle_ingest(body)
        elif '/entities/' in path:
            entity_id = path_params.get('entityId', '')
            return get_entity(entity_id)
        elif '/topics' in path:
            return get_trending_topics(query_params)
        elif '/competitive' in path:
            return handle_competitive_analysis(body)
        else:
            return api_response(404, {'error': 'Not found'})

    except ValueError as e:
        return api_response(400, {'error': str(e)})
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return api_response(500, {'error': 'Internal server error'})


def handle_search(body: dict) -> dict:
    """Handle similarity search requests."""
    query = body.get('query', '')
    brand_id = body.get('brandId', '')
    content_type = body.get('contentType', '')
    k = body.get('k', 10)
    filters = body.get('filters', {})

    if not query:
        raise ValueError("query is required")

    if not SIMILARITY_SEARCH_FUNCTION:
        return api_response(503, {'error': 'Search service not configured'})

    # Invoke similarity search Lambda
    result = invoke_lambda(SIMILARITY_SEARCH_FUNCTION, {
        'query': query,
        'brandId': brand_id,
        'contentType': content_type,
        'k': k,
        'filters': filters
    })

    return api_response(200, {
        'results': result.get('results', []),
        'totalFound': result.get('totalFound', 0),
        'query': query,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


def handle_graph_query(body: dict) -> dict:
    """Handle graph query requests."""
    query_type = body.get('queryType', 'brand_connections')
    brand_id = body.get('brandId', '')
    params = body.get('params', {})

    if not brand_id and query_type not in ['content_relationships']:
        raise ValueError("brandId is required")

    if not GRAPH_QUERY_FUNCTION:
        return api_response(503, {'error': 'Graph service not configured'})

    # Invoke graph query Lambda
    result = invoke_lambda(GRAPH_QUERY_FUNCTION, {
        'queryType': query_type,
        'brandId': brand_id,
        'params': params
    })

    return api_response(200, {
        **result,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


def handle_insights(body: dict) -> dict:
    """Handle insights generation requests."""
    insight_type = body.get('insightType', 'visibility')
    brand_id = body.get('brandId', '')
    data = body.get('data', {})

    if not brand_id:
        raise ValueError("brandId is required")

    if not INSIGHTS_GENERATOR_FUNCTION:
        return api_response(503, {'error': 'Insights service not configured'})

    # If no data provided, gather data from other services
    if not data:
        data = gather_insight_data(brand_id, insight_type)

    # Invoke insights generator Lambda
    result = invoke_lambda(INSIGHTS_GENERATOR_FUNCTION, {
        'insightType': insight_type,
        'brandId': brand_id,
        'data': data
    })

    return api_response(200, result)


def handle_ingest(body: dict) -> dict:
    """Handle content ingestion requests."""
    content = body.get('content', '')
    content_type = body.get('contentType', 'article')
    brand_id = body.get('brandId', '')
    metadata = body.get('metadata', {})

    if not content:
        raise ValueError("content is required")

    if not CONTENT_INGESTION_FUNCTION:
        return api_response(503, {'error': 'Ingestion service not configured'})

    # Invoke content ingestion Lambda
    result = invoke_lambda(CONTENT_INGESTION_FUNCTION, {
        'content': content,
        'contentType': content_type,
        'brandId': brand_id,
        'title': body.get('title', ''),
        'sourceUrl': body.get('sourceUrl', ''),
        'author': body.get('author', ''),
        'publishedDate': body.get('publishedDate'),
        'metadata': metadata,
        'tags': body.get('tags', [])
    })

    return api_response(201, {
        'message': 'Content ingested successfully',
        'contentId': result.get('contentId'),
        'indexed': result.get('indexed', True),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


def get_entity(entity_id: str) -> dict:
    """Get entity details from graph."""
    if not entity_id:
        raise ValueError("entityId is required")

    if not GRAPH_QUERY_FUNCTION:
        return api_response(503, {'error': 'Graph service not configured'})

    # Query entity from graph
    result = invoke_lambda(GRAPH_QUERY_FUNCTION, {
        'queryType': 'entity_graph',
        'brandId': entity_id,
        'params': {'maxNodes': 1}
    })

    if result.get('nodeCount', 0) == 0:
        return api_response(404, {'error': 'Entity not found'})

    return api_response(200, {
        'entity': result.get('graph', {}).get('nodes', [{}])[0],
        'relationships': result.get('graph', {}).get('edges', [])
    })


def get_trending_topics(query_params: dict) -> dict:
    """Get trending topics."""
    brand_id = query_params.get('brandId', '')
    limit = min(int(query_params.get('limit', 20)), 50)

    if not GRAPH_QUERY_FUNCTION:
        return api_response(503, {'error': 'Graph service not configured'})

    # Query topics from graph
    result = invoke_lambda(GRAPH_QUERY_FUNCTION, {
        'queryType': 'topic_analysis',
        'brandId': brand_id if brand_id else 'all',
        'params': {'limit': limit}
    })

    return api_response(200, {
        'topics': result.get('topics', []),
        'totalTopics': result.get('totalTopics', 0),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


def handle_competitive_analysis(body: dict) -> dict:
    """Handle competitive analysis requests."""
    brand_id = body.get('brandId', '')

    if not brand_id:
        raise ValueError("brandId is required")

    if not GRAPH_QUERY_FUNCTION:
        return api_response(503, {'error': 'Graph service not configured'})

    # Get competitive landscape from graph
    result = invoke_lambda(GRAPH_QUERY_FUNCTION, {
        'queryType': 'competitive_landscape',
        'brandId': brand_id,
        'params': {}
    })

    return api_response(200, {
        'brandId': brand_id,
        'competitors': result.get('competitors', []),
        'competitorCount': result.get('competitorCount', 0),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


def gather_insight_data(brand_id: str, insight_type: str) -> dict:
    """Gather data needed for insight generation."""
    data = {}

    # Get graph data
    if GRAPH_QUERY_FUNCTION:
        try:
            graph_result = invoke_lambda(GRAPH_QUERY_FUNCTION, {
                'queryType': 'entity_graph',
                'brandId': brand_id,
                'params': {'maxNodes': 50}
            })
            data['graphData'] = graph_result
        except Exception as e:
            logger.warning(f"Failed to get graph data: {e}")

        if insight_type == 'competitive':
            try:
                comp_result = invoke_lambda(GRAPH_QUERY_FUNCTION, {
                    'queryType': 'competitive_landscape',
                    'brandId': brand_id,
                    'params': {}
                })
                data['competitors'] = comp_result.get('competitors', [])
            except Exception as e:
                logger.warning(f"Failed to get competitive data: {e}")

    # Get similar content
    if SIMILARITY_SEARCH_FUNCTION and insight_type == 'content':
        try:
            search_result = invoke_lambda(SIMILARITY_SEARCH_FUNCTION, {
                'query': brand_id,
                'brandId': brand_id,
                'k': 20
            })
            data['similarContent'] = search_result.get('results', [])
        except Exception as e:
            logger.warning(f"Failed to get similar content: {e}")

    return data


def invoke_lambda(function_name: str, payload: dict) -> dict:
    """Invoke a Lambda function and return the result."""
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    result = json.loads(response['Payload'].read())

    if response.get('FunctionError'):
        raise Exception(f"Lambda error: {result}")

    return result


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
