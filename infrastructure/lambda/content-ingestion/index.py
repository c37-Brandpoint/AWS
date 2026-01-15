"""
Content Ingestion Lambda Function

Ingests content into the Intelligence Engine by generating embeddings
and storing them in OpenSearch for vector similarity search.
"""
import os
import json
import logging
import hashlib
from datetime import datetime
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

        # Ensure index exists
        ensure_index_exists(_opensearch_client)

    return _opensearch_client


def ensure_index_exists(client):
    """Create index with k-NN mapping if it doesn't exist."""
    if not client.indices.exists(index=OPENSEARCH_INDEX):
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                },
                "number_of_shards": 2,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "content_id": {"type": "keyword"},
                    "content_hash": {"type": "keyword"},
                    "content_type": {"type": "keyword"},
                    "brand_id": {"type": "keyword"},
                    "client_id": {"type": "keyword"},
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "content_preview": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1536,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 24
                            }
                        }
                    },
                    "source_url": {"type": "keyword"},
                    "author": {"type": "keyword"},
                    "published_date": {"type": "date"},
                    "ingested_at": {"type": "date"},
                    "metadata": {"type": "object", "enabled": False},
                    "sentiment_score": {"type": "float"},
                    "word_count": {"type": "integer"},
                    "tags": {"type": "keyword"}
                }
            }
        }
        client.indices.create(index=OPENSEARCH_INDEX, body=index_body)
        logger.info(f"Created index: {OPENSEARCH_INDEX}")


def handler(event, context):
    """
    Ingest content into OpenSearch.

    Input:
        {
            "content": "...",
            "contentType": "article|social|review|competitor",
            "title": "...",
            "brandId": "...",
            "clientId": "...",
            "sourceUrl": "...",
            "author": "...",
            "publishedDate": "...",
            "metadata": {...},
            "tags": ["tag1", "tag2"]
        }

    Output:
        {
            "contentId": "...",
            "indexed": true,
            "embedding_dimensions": 1536
        }
    """
    content = event.get('content', '')
    content_type = event.get('contentType', 'article')
    title = event.get('title', '')
    brand_id = event.get('brandId', '')
    client_id = event.get('clientId', '')
    source_url = event.get('sourceUrl', '')
    author = event.get('author', '')
    published_date = event.get('publishedDate')
    metadata = event.get('metadata', {})
    tags = event.get('tags', [])

    if not content:
        raise ValueError("content is required")

    logger.info(f"Ingesting {content_type} content for brand: {brand_id}")

    # Generate content hash for deduplication
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    content_id = f"{brand_id}#{content_hash[:16]}"

    # Check for duplicates
    client = get_opensearch_client()
    if check_duplicate(client, content_hash):
        logger.info(f"Duplicate content detected: {content_id}")
        return {
            'contentId': content_id,
            'indexed': False,
            'duplicate': True,
            'message': 'Content already exists'
        }

    # Generate embedding
    embedding = generate_embedding(content)

    # Calculate basic features
    word_count = len(content.split())
    sentiment_score = calculate_basic_sentiment(content)

    # Prepare document
    document = {
        'content_id': content_id,
        'content_hash': content_hash,
        'content_type': content_type,
        'brand_id': brand_id,
        'client_id': client_id,
        'title': title,
        'content': content,
        'content_preview': content[:500] if len(content) > 500 else content,
        'embedding': embedding,
        'source_url': source_url,
        'author': author,
        'published_date': published_date,
        'ingested_at': datetime.utcnow().isoformat(),
        'metadata': metadata,
        'sentiment_score': sentiment_score,
        'word_count': word_count,
        'tags': tags
    }

    # Index document
    response = client.index(
        index=OPENSEARCH_INDEX,
        id=content_id,
        body=document,
        refresh=True
    )

    logger.info(f"Indexed content: {content_id}, result: {response['result']}")

    return {
        'contentId': content_id,
        'indexed': True,
        'embeddingDimensions': len(embedding),
        'wordCount': word_count,
        'sentimentScore': sentiment_score
    }


def check_duplicate(client, content_hash: str) -> bool:
    """Check if content already exists."""
    try:
        query = {
            "query": {
                "term": {"content_hash": content_hash}
            }
        }
        response = client.search(index=OPENSEARCH_INDEX, body=query, size=1)
        return response['hits']['total']['value'] > 0
    except Exception as e:
        logger.warning(f"Error checking duplicate: {e}")
        return False


def generate_embedding(content: str) -> list:
    """Generate embedding using Bedrock Titan."""
    max_chars = 8000
    truncated_content = content[:max_chars] if len(content) > max_chars else content

    try:
        body = {"inputText": truncated_content}

        response = bedrock.invoke_model(
            modelId=BEDROCK_EMBEDDING_MODEL,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response['body'].read())
        return response_body.get('embedding', [0.0] * 1536)

    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return [0.0] * 1536


def calculate_basic_sentiment(content: str) -> float:
    """Calculate basic sentiment score."""
    content_lower = content.lower()

    positive_words = ['good', 'great', 'excellent', 'amazing', 'best', 'love', 'recommend', 'happy']
    negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'poor', 'avoid', 'disappointed']

    positive = sum(1 for w in positive_words if w in content_lower)
    negative = sum(1 for w in negative_words if w in content_lower)

    total = positive + negative
    if total == 0:
        return 0.0
    return round((positive - negative) / total, 3)
