"""
Graph Query Lambda Function

Queries the Neptune knowledge graph for entity relationships,
brand connections, and topic analysis.
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
    Query knowledge graph.

    Input:
        {
            "queryType": "brand_connections|topic_analysis|entity_graph|competitive_landscape",
            "brandId": "...",
            "params": {...}
        }

    Output varies by queryType.
    """
    query_type = event.get('queryType', 'brand_connections')
    brand_id = event.get('brandId', '')
    params = event.get('params', {})

    logger.info(f"Graph query: type={query_type}, brand={brand_id}")

    gremlin = get_gremlin_client()

    try:
        if query_type == 'brand_connections':
            return query_brand_connections(gremlin, brand_id, params)
        elif query_type == 'topic_analysis':
            return query_topic_analysis(gremlin, brand_id, params)
        elif query_type == 'entity_graph':
            return query_entity_graph(gremlin, brand_id, params)
        elif query_type == 'competitive_landscape':
            return query_competitive_landscape(gremlin, brand_id, params)
        elif query_type == 'sentiment_trends':
            return query_sentiment_trends(gremlin, brand_id, params)
        elif query_type == 'content_relationships':
            content_id = params.get('contentId')
            return query_content_relationships(gremlin, content_id, params)
        else:
            raise ValueError(f"Unknown query type: {query_type}")

    except GremlinServerError as e:
        logger.error(f"Gremlin error: {e}")
        return {
            'success': False,
            'error': str(e),
            'queryType': query_type
        }


def query_brand_connections(gremlin, brand_id: str, params: dict) -> dict:
    """Find entities and topics connected to a brand."""
    depth = params.get('depth', 2)
    limit = params.get('limit', 50)

    # Query for connected entities
    query = """
    g.V().has('brand', 'id', brand_id)
        .repeat(both().simplePath())
        .times(depth)
        .dedup()
        .limit(limit)
        .project('id', 'label', 'name', 'type')
            .by(id())
            .by(label())
            .by(coalesce(values('name'), constant('')))
            .by(label())
    """

    results = gremlin.submit(query, {
        'brand_id': normalize_id(brand_id),
        'depth': depth,
        'limit': limit
    }).all().result()

    # Query for edges
    edge_query = """
    g.V().has('brand', 'id', brand_id)
        .bothE()
        .limit(100)
        .project('source', 'target', 'type', 'weight')
            .by(outV().values('id'))
            .by(inV().values('id'))
            .by(label())
            .by(coalesce(values('weight'), constant(1.0)))
    """

    edges = gremlin.submit(edge_query, {
        'brand_id': normalize_id(brand_id)
    }).all().result()

    return {
        'success': True,
        'queryType': 'brand_connections',
        'brandId': brand_id,
        'nodes': results,
        'edges': edges,
        'nodeCount': len(results),
        'edgeCount': len(edges)
    }


def query_topic_analysis(gremlin, brand_id: str, params: dict) -> dict:
    """Analyze topics associated with a brand."""
    limit = params.get('limit', 20)

    query = """
    g.V().has('brand', 'id', brand_id)
        .out('MENTIONED_WITH', 'RELATED_TO')
        .hasLabel('topic')
        .groupCount()
        .by('name')
        .order(local)
        .by(values, desc)
        .limit(local, limit)
    """

    topic_counts = gremlin.submit(query, {
        'brand_id': normalize_id(brand_id),
        'limit': limit
    }).all().result()

    # Get topic details
    topics = []
    if topic_counts:
        for topic_name, count in topic_counts[0].items():
            topics.append({
                'name': topic_name,
                'mentionCount': count,
                'relevanceScore': min(count / 10, 1.0)  # Normalize
            })

    return {
        'success': True,
        'queryType': 'topic_analysis',
        'brandId': brand_id,
        'topics': sorted(topics, key=lambda x: x['mentionCount'], reverse=True),
        'totalTopics': len(topics)
    }


def query_entity_graph(gremlin, brand_id: str, params: dict) -> dict:
    """Get full entity graph for a brand."""
    max_nodes = params.get('maxNodes', 100)

    # Get all connected nodes
    node_query = """
    g.V().has('brand', 'id', brand_id)
        .emit()
        .repeat(both().simplePath())
        .times(2)
        .dedup()
        .limit(max_nodes)
        .project('id', 'label', 'name', 'properties')
            .by(values('id'))
            .by(label())
            .by(coalesce(values('name'), values('id')))
            .by(valueMap())
    """

    nodes = gremlin.submit(node_query, {
        'brand_id': normalize_id(brand_id),
        'max_nodes': max_nodes
    }).all().result()

    # Get edges between these nodes
    if nodes:
        node_ids = [n['id'] for n in nodes]
        edge_query = """
        g.V().has('id', within(node_ids))
            .bothE()
            .where(otherV().has('id', within(node_ids)))
            .dedup()
            .project('id', 'source', 'target', 'label', 'weight')
                .by(id())
                .by(outV().values('id'))
                .by(inV().values('id'))
                .by(label())
                .by(coalesce(values('weight'), constant(1.0)))
        """

        edges = gremlin.submit(edge_query, {
            'node_ids': node_ids
        }).all().result()
    else:
        edges = []

    return {
        'success': True,
        'queryType': 'entity_graph',
        'brandId': brand_id,
        'graph': {
            'nodes': nodes,
            'edges': edges
        },
        'nodeCount': len(nodes),
        'edgeCount': len(edges)
    }


def query_competitive_landscape(gremlin, brand_id: str, params: dict) -> dict:
    """Analyze competitive landscape for a brand."""
    # Find other brands mentioned in similar contexts
    query = """
    g.V().has('brand', 'id', brand_id)
        .in('ABOUT', 'MENTIONS')
        .hasLabel('content')
        .out('ABOUT', 'MENTIONS')
        .hasLabel('brand')
        .where(neq(brand_id))
        .groupCount()
        .by('id')
    """

    competitor_counts = gremlin.submit(query, {
        'brand_id': normalize_id(brand_id)
    }).all().result()

    competitors = []
    if competitor_counts:
        for comp_id, count in competitor_counts[0].items():
            # Get competitor details
            detail_query = """
            g.V().has('brand', 'id', comp_id)
                .project('id', 'name', 'mentionCount')
                    .by(values('id'))
                    .by(coalesce(values('name'), values('id')))
                    .by(coalesce(values('mentionCount'), constant(0)))
            """
            details = gremlin.submit(detail_query, {'comp_id': comp_id}).all().result()

            if details:
                competitors.append({
                    'brandId': comp_id,
                    'name': details[0].get('name', comp_id),
                    'coMentionCount': count,
                    'totalMentions': details[0].get('mentionCount', 0)
                })

    return {
        'success': True,
        'queryType': 'competitive_landscape',
        'brandId': brand_id,
        'competitors': sorted(competitors, key=lambda x: x['coMentionCount'], reverse=True),
        'competitorCount': len(competitors)
    }


def query_sentiment_trends(gremlin, brand_id: str, params: dict) -> dict:
    """Analyze sentiment trends for a brand."""
    query = """
    g.V().has('brand', 'id', brand_id)
        .inE('HAS_SENTIMENT')
        .project('sentiment', 'score', 'timestamp', 'contentId')
            .by(values('sentiment'))
            .by(values('score'))
            .by(values('timestamp'))
            .by(outV().values('id'))
    """

    sentiments = gremlin.submit(query, {
        'brand_id': normalize_id(brand_id)
    }).all().result()

    # Aggregate sentiment data
    sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    total_score = 0

    for s in sentiments:
        sentiment = s.get('sentiment', 'neutral')
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        total_score += s.get('score', 0)

    avg_score = total_score / len(sentiments) if sentiments else 0

    return {
        'success': True,
        'queryType': 'sentiment_trends',
        'brandId': brand_id,
        'sentimentCounts': sentiment_counts,
        'averageScore': round(avg_score, 3),
        'totalAnalyzed': len(sentiments),
        'sentiments': sentiments[:50]  # Limit returned details
    }


def query_content_relationships(gremlin, content_id: str, params: dict) -> dict:
    """Get all relationships for a specific content item."""
    if not content_id:
        raise ValueError("contentId is required")

    query = """
    g.V().has('content', 'id', content_id)
        .bothE()
        .project('direction', 'type', 'target', 'targetLabel', 'weight')
            .by(choose(outV().has('id', content_id), constant('outgoing'), constant('incoming')))
            .by(label())
            .by(otherV().values('id'))
            .by(otherV().label())
            .by(coalesce(values('weight'), constant(1.0)))
    """

    relationships = gremlin.submit(query, {
        'content_id': content_id
    }).all().result()

    return {
        'success': True,
        'queryType': 'content_relationships',
        'contentId': content_id,
        'relationships': relationships,
        'relationshipCount': len(relationships)
    }


def normalize_id(text: str) -> str:
    """Normalize text to use as ID."""
    return text.lower().replace(' ', '_').replace('-', '_')
