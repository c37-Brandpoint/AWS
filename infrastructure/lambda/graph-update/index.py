"""
Graph Update Lambda Function

Updates the Neptune knowledge graph with entity relationships
discovered from content analysis.
"""
import os
import json
import logging
from datetime import datetime
import boto3
from gremlin_python.driver import client, serializer
from gremlin_python.driver.protocol import GremlinServerError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
NEPTUNE_ENDPOINT = os.environ.get('NEPTUNE_ENDPOINT', '')
NEPTUNE_PORT = int(os.environ.get('NEPTUNE_PORT', '8182'))

# Gremlin client (lazy initialization)
_gremlin_client = None


def get_gremlin_client():
    """Get or create Gremlin client."""
    global _gremlin_client
    if _gremlin_client is None:
        _gremlin_client = client.Client(
            f'wss://{NEPTUNE_ENDPOINT}:{NEPTUNE_PORT}/gremlin',
            'g',
            message_serializer=serializer.GraphSONSerializersV2d0()
        )
    return _gremlin_client


def handler(event, context):
    """
    Update knowledge graph with new entities and relationships.

    Input:
        {
            "contentId": "...",
            "brandId": "...",
            "entities": {
                "brands": ["brand1", "brand2"],
                "topics": ["topic1", "topic2"],
                "sentiments": [{"target": "brand1", "sentiment": "positive"}]
            },
            "relationships": [
                {"source": "brand1", "target": "topic1", "type": "MENTIONED_WITH"},
                {"source": "content_id", "target": "brand1", "type": "MENTIONS"}
            ]
        }

    Output:
        {
            "nodesCreated": 5,
            "edgesCreated": 3,
            "success": true
        }
    """
    content_id = event.get('contentId', '')
    brand_id = event.get('brandId', '')
    entities = event.get('entities', {})
    relationships = event.get('relationships', [])

    if not content_id:
        raise ValueError("contentId is required")

    logger.info(f"Updating graph for content: {content_id}")

    gremlin = get_gremlin_client()
    nodes_created = 0
    edges_created = 0

    try:
        # Create or update content node
        create_content_node(gremlin, content_id, brand_id)
        nodes_created += 1

        # Create brand nodes
        for brand in entities.get('brands', []):
            if create_brand_node(gremlin, brand):
                nodes_created += 1

        # Create topic nodes
        for topic in entities.get('topics', []):
            if create_topic_node(gremlin, topic):
                nodes_created += 1

        # Create sentiment relationships
        for sentiment_data in entities.get('sentiments', []):
            target = sentiment_data.get('target')
            sentiment = sentiment_data.get('sentiment', 'neutral')
            if target:
                create_sentiment_edge(gremlin, content_id, target, sentiment)
                edges_created += 1

        # Create explicit relationships
        for rel in relationships:
            source = rel.get('source')
            target = rel.get('target')
            rel_type = rel.get('type', 'RELATED_TO')
            weight = rel.get('weight', 1.0)

            if source and target:
                create_edge(gremlin, source, target, rel_type, weight)
                edges_created += 1

        # Create content-to-brand edge
        if brand_id:
            create_edge(gremlin, content_id, brand_id, 'ABOUT', 1.0)
            edges_created += 1

        logger.info(f"Graph updated: {nodes_created} nodes, {edges_created} edges")

        return {
            'contentId': content_id,
            'nodesCreated': nodes_created,
            'edgesCreated': edges_created,
            'success': True
        }

    except GremlinServerError as e:
        logger.error(f"Gremlin error: {e}")
        return {
            'contentId': content_id,
            'nodesCreated': nodes_created,
            'edgesCreated': edges_created,
            'success': False,
            'error': str(e)
        }


def create_content_node(gremlin, content_id: str, brand_id: str):
    """Create or update content node."""
    query = """
    g.V().has('content', 'id', content_id)
        .fold()
        .coalesce(
            unfold(),
            addV('content')
                .property('id', content_id)
                .property('brandId', brand_id)
                .property('createdAt', timestamp)
        )
        .property('updatedAt', timestamp)
    """
    timestamp = datetime.utcnow().isoformat()
    gremlin.submit(query, {
        'content_id': content_id,
        'brand_id': brand_id,
        'timestamp': timestamp
    }).all().result()


def create_brand_node(gremlin, brand_name: str) -> bool:
    """Create brand node if it doesn't exist."""
    brand_id = normalize_id(brand_name)
    query = """
    g.V().has('brand', 'id', brand_id)
        .fold()
        .coalesce(
            unfold().property('mentionCount', __.values('mentionCount').math('_ + 1')),
            addV('brand')
                .property('id', brand_id)
                .property('name', brand_name)
                .property('mentionCount', 1)
                .property('createdAt', timestamp)
        )
    """
    timestamp = datetime.utcnow().isoformat()
    result = gremlin.submit(query, {
        'brand_id': brand_id,
        'brand_name': brand_name,
        'timestamp': timestamp
    }).all().result()
    return len(result) > 0


def create_topic_node(gremlin, topic_name: str) -> bool:
    """Create topic node if it doesn't exist."""
    topic_id = normalize_id(topic_name)
    query = """
    g.V().has('topic', 'id', topic_id)
        .fold()
        .coalesce(
            unfold().property('mentionCount', __.values('mentionCount').math('_ + 1')),
            addV('topic')
                .property('id', topic_id)
                .property('name', topic_name)
                .property('mentionCount', 1)
                .property('createdAt', timestamp)
        )
    """
    timestamp = datetime.utcnow().isoformat()
    result = gremlin.submit(query, {
        'topic_id': topic_id,
        'topic_name': topic_name,
        'timestamp': timestamp
    }).all().result()
    return len(result) > 0


def create_sentiment_edge(gremlin, source_id: str, target_name: str, sentiment: str):
    """Create sentiment edge between content and entity."""
    target_id = normalize_id(target_name)
    sentiment_score = {'positive': 1.0, 'neutral': 0.0, 'negative': -1.0}.get(sentiment, 0.0)

    query = """
    g.V().has('content', 'id', source_id).as('source')
        .V().has('id', target_id).as('target')
        .coalesce(
            select('source').outE('HAS_SENTIMENT').where(inV().as('target')),
            addE('HAS_SENTIMENT').from('source').to('target')
        )
        .property('sentiment', sentiment)
        .property('score', sentiment_score)
        .property('timestamp', timestamp)
    """
    timestamp = datetime.utcnow().isoformat()
    gremlin.submit(query, {
        'source_id': source_id,
        'target_id': target_id,
        'sentiment': sentiment,
        'sentiment_score': sentiment_score,
        'timestamp': timestamp
    }).all().result()


def create_edge(gremlin, source_id: str, target_id: str, edge_type: str, weight: float):
    """Create or update edge between nodes."""
    source_normalized = normalize_id(source_id)
    target_normalized = normalize_id(target_id)

    query = """
    g.V().has('id', source_id).as('source')
        .V().has('id', target_id).as('target')
        .coalesce(
            select('source').outE(edge_type).where(inV().as('target')),
            addE(edge_type).from('source').to('target')
        )
        .property('weight', weight)
        .property('timestamp', timestamp)
    """
    timestamp = datetime.utcnow().isoformat()
    gremlin.submit(query, {
        'source_id': source_normalized,
        'target_id': target_normalized,
        'edge_type': edge_type,
        'weight': weight,
        'timestamp': timestamp
    }).all().result()


def normalize_id(text: str) -> str:
    """Normalize text to use as ID."""
    return text.lower().replace(' ', '_').replace('-', '_')
