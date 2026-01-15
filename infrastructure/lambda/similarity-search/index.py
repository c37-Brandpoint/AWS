"""
Similarity Search Lambda Function

Performs k-NN vector similarity search on OpenSearch
to find semantically similar content.
"""
import os
import json
import logging
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT', '')
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX', 'content-embeddings')
BEDROCK_EMBEDDING_MODEL = os.environ.get('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v2:0')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Clients
bedrock = boto3.client('bedrock-runtime')
credentials = boto3.Session().get_credentials()

# OpenSearch client (lazy initialization)
_opensearch_client = None


def get_opensearch_client():
    """Get or create OpenSearch client."""
    global _opensearch_client
    if _opensearch_client is None:
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            AWS_REGION,
            'es',
            session_token=credentials.token
        )

        _opensearch_client = OpenSearch(
            hosts=[{'host': OPENSEARCH_ENDPOINT.replace('https://', ''), 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

    return _opensearch_client


def handler(event, context):
    """
    Perform similarity search.

    Input:
        {
            "query": "text to find similar content for",
            "brandId": "optional brand filter",
            "contentType": "optional type filter",
            "k": 10,
            "minScore": 0.7,
            "filters": {...}
        }

        OR

        {
            "embedding": [...],  # Pre-computed embedding vector
            "brandId": "...",
            "k": 10
        }

    Output:
        {
            "results": [
                {
                    "contentId": "...",
                    "title": "...",
                    "preview": "...",
                    "score": 0.95,
                    "contentType": "...",
                    "metadata": {...}
                }
            ],
            "totalFound": 10
        }
    """
    query_text = event.get('query', '')
    embedding = event.get('embedding', [])
    brand_id = event.get('brandId', '')
    content_type = event.get('contentType', '')
    k = min(event.get('k', 10), 100)  # Cap at 100
    min_score = event.get('minScore', 0.5)
    filters = event.get('filters', {})

    # Generate embedding if query text provided
    if query_text and not embedding:
        embedding = generate_embedding(query_text)
    elif not embedding:
        raise ValueError("Either query or embedding is required")

    logger.info(f"Similarity search: k={k}, brandId={brand_id}, contentType={content_type}")

    client = get_opensearch_client()

    # Build query
    search_query = build_knn_query(embedding, k, brand_id, content_type, filters, min_score)

    # Execute search
    response = client.search(
        index=OPENSEARCH_INDEX,
        body=search_query
    )

    # Process results
    results = []
    for hit in response['hits']['hits']:
        source = hit['_source']
        results.append({
            'contentId': source.get('content_id', hit['_id']),
            'title': source.get('title', ''),
            'preview': source.get('content_preview', ''),
            'score': round(hit['_score'], 4),
            'contentType': source.get('content_type', ''),
            'brandId': source.get('brand_id', ''),
            'sourceUrl': source.get('source_url', ''),
            'author': source.get('author', ''),
            'publishedDate': source.get('published_date', ''),
            'ingestedAt': source.get('ingested_at', ''),
            'sentimentScore': source.get('sentiment_score', 0),
            'wordCount': source.get('word_count', 0),
            'tags': source.get('tags', [])
        })

    total_found = response['hits']['total']['value']
    logger.info(f"Found {total_found} similar documents, returning {len(results)}")

    return {
        'results': results,
        'totalFound': total_found,
        'k': k,
        'queryType': 'text' if query_text else 'embedding'
    }


def build_knn_query(embedding: list, k: int, brand_id: str, content_type: str,
                    filters: dict, min_score: float) -> dict:
    """Build k-NN query with optional filters."""
    # Build filter clauses
    filter_clauses = []

    if brand_id:
        filter_clauses.append({"term": {"brand_id": brand_id}})

    if content_type:
        filter_clauses.append({"term": {"content_type": content_type}})

    # Add custom filters
    if filters.get('tags'):
        filter_clauses.append({"terms": {"tags": filters['tags']}})

    if filters.get('dateFrom'):
        filter_clauses.append({
            "range": {
                "published_date": {"gte": filters['dateFrom']}
            }
        })

    if filters.get('dateTo'):
        filter_clauses.append({
            "range": {
                "published_date": {"lte": filters['dateTo']}
            }
        })

    if filters.get('minWordCount'):
        filter_clauses.append({
            "range": {
                "word_count": {"gte": filters['minWordCount']}
            }
        })

    # Build k-NN query
    if filter_clauses:
        query = {
            "size": k,
            "min_score": min_score,
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": embedding,
                                    "k": k * 2  # Fetch more to account for filtering
                                }
                            }
                        }
                    ],
                    "filter": filter_clauses
                }
            },
            "_source": {
                "excludes": ["embedding"]  # Don't return the embedding vector
            }
        }
    else:
        query = {
            "size": k,
            "min_score": min_score,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": embedding,
                        "k": k
                    }
                }
            },
            "_source": {
                "excludes": ["embedding"]
            }
        }

    return query


def generate_embedding(text: str) -> list:
    """Generate embedding using Bedrock Titan."""
    max_chars = 8000
    truncated_text = text[:max_chars] if len(text) > max_chars else text

    try:
        body = {"inputText": truncated_text}

        response = bedrock.invoke_model(
            modelId=BEDROCK_EMBEDDING_MODEL,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response['body'].read())
        return response_body.get('embedding', [])

    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise


def search_by_content_id(content_id: str, k: int = 10) -> dict:
    """Find similar content by content ID."""
    client = get_opensearch_client()

    # First, get the embedding for the content
    response = client.get(index=OPENSEARCH_INDEX, id=content_id)
    embedding = response['_source'].get('embedding', [])

    if not embedding:
        raise ValueError(f"No embedding found for content: {content_id}")

    # Now search for similar
    return handler({
        'embedding': embedding,
        'k': k
    }, None)
