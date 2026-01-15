"""
Analyze Visibility Lambda Function

Analyzes AI engine responses to determine brand visibility, mentions,
sentiment, and generates visibility scores.
"""
import os
import json
import logging
import re
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')

# Bedrock client
bedrock = boto3.client('bedrock-runtime')


def handler(event, context):
    """
    Analyze AI responses for brand visibility.

    Input:
        {
            "results": [
                {
                    "query": "...",
                    "engineResults": [
                        {"engine": "chatgpt", "response": "...", "success": true},
                        {"engine": "perplexity", "response": "...", "success": true}
                    ]
                }
            ],
            "persona": {...},
            "brandContext": {
                "brandId": "us-army",
                "clientId": "123"
            }
        }

    Output:
        {
            "overallVisibility": 0.45,
            "queryResults": [...],
            "engineBreakdown": {...},
            "insights": [...]
        }
    """
    results = event.get('results', [])
    persona = event.get('persona', {})
    brand_context = event.get('brandContext', {})

    brand_id = brand_context.get('brandId', persona.get('brandId', ''))

    logger.info(f"Analyzing visibility for brand: {brand_id}")

    if not results:
        return {
            'overallVisibility': 0.0,
            'queryResults': [],
            'engineBreakdown': {},
            'insights': ['No results to analyze']
        }

    # Analyze each query result
    query_results = []
    engine_scores = {'chatgpt': [], 'perplexity': [], 'gemini': [], 'claude': []}

    for query_result in results:
        engine_results = query_result.get('engineResults', [])
        query = query_result.get('query', '')

        for engine_result in engine_results:
            engine = engine_result.get('engine', '')
            response = engine_result.get('response', '')
            success = engine_result.get('success', False)

            if not success or not response:
                continue

            # Analyze this response
            analysis = analyze_response(response, brand_id, query)

            query_results.append({
                'query': query,
                'engine': engine,
                'brandMentioned': analysis['brand_mentioned'],
                'visibilityScore': analysis['visibility_score'],
                'sentiment': analysis['sentiment'],
                'mentionContext': analysis['mention_context'],
                'position': analysis['position']
            })

            engine_scores[engine].append(analysis['visibility_score'])

    # Calculate engine breakdown
    engine_breakdown = {}
    for engine, scores in engine_scores.items():
        if scores:
            engine_breakdown[engine] = {
                'averageVisibility': sum(scores) / len(scores),
                'mentionRate': sum(1 for s in scores if s > 0) / len(scores),
                'queryCount': len(scores)
            }

    # Calculate overall visibility
    all_scores = [r['visibilityScore'] for r in query_results]
    overall_visibility = sum(all_scores) / len(all_scores) if all_scores else 0.0

    # Generate insights using LLM
    insights = generate_insights(query_results, brand_id, engine_breakdown)

    logger.info(f"Analysis complete. Overall visibility: {overall_visibility:.2%}")

    return {
        'overallVisibility': overall_visibility,
        'queryResults': query_results,
        'engineBreakdown': engine_breakdown,
        'insights': insights,
        'totalQueries': len(query_results),
        'brandId': brand_id
    }


def analyze_response(response: str, brand_id: str, query: str) -> dict:
    """
    Analyze a single AI response for brand visibility.
    """
    response_lower = response.lower()
    brand_lower = brand_id.lower()

    # Check for brand mention
    brand_mentioned = brand_lower in response_lower

    # Check for variations
    brand_variations = get_brand_variations(brand_id)
    for variation in brand_variations:
        if variation.lower() in response_lower:
            brand_mentioned = True
            break

    # Calculate visibility score
    visibility_score = 0.0
    mention_context = None
    position = None

    if brand_mentioned:
        # Find position of mention
        first_mention = response_lower.find(brand_lower)
        if first_mention == -1:
            for variation in brand_variations:
                first_mention = response_lower.find(variation.lower())
                if first_mention != -1:
                    break

        response_length = len(response)

        if first_mention != -1:
            # Score based on position (earlier = better)
            position_score = 1.0 - (first_mention / response_length)

            # Count mentions
            mention_count = response_lower.count(brand_lower)
            for variation in brand_variations:
                mention_count += response_lower.count(variation.lower())

            mention_score = min(mention_count * 0.1, 0.3)

            # Base visibility score
            visibility_score = 0.5 + (position_score * 0.3) + mention_score

            # Determine position category
            if first_mention < response_length * 0.2:
                position = 'prominent'
            elif first_mention < response_length * 0.5:
                position = 'middle'
            else:
                position = 'late'

            # Extract context around mention
            context_start = max(0, first_mention - 100)
            context_end = min(len(response), first_mention + 150)
            mention_context = response[context_start:context_end].strip()

    # Determine sentiment
    sentiment = analyze_sentiment(response, brand_mentioned)

    return {
        'brand_mentioned': brand_mentioned,
        'visibility_score': round(visibility_score, 3),
        'sentiment': sentiment,
        'mention_context': mention_context,
        'position': position
    }


def get_brand_variations(brand_id: str) -> list:
    """Get common variations of brand name."""
    variations = [brand_id]

    # Add common transformations
    variations.append(brand_id.replace('-', ' '))
    variations.append(brand_id.replace('_', ' '))
    variations.append(brand_id.title())
    variations.append(brand_id.upper())

    # Handle common brand name patterns
    if 'army' in brand_id.lower():
        variations.extend(['U.S. Army', 'US Army', 'United States Army', 'Army'])
    if 'navy' in brand_id.lower():
        variations.extend(['U.S. Navy', 'US Navy', 'United States Navy', 'Navy'])

    return list(set(variations))


def analyze_sentiment(response: str, brand_mentioned: bool) -> str:
    """Simple sentiment analysis."""
    if not brand_mentioned:
        return 'neutral'

    positive_words = ['great', 'excellent', 'recommended', 'best', 'top', 'leading',
                      'trusted', 'reliable', 'quality', 'innovative', 'advantage']
    negative_words = ['avoid', 'problem', 'issue', 'concern', 'risk', 'negative',
                      'worst', 'poor', 'bad', 'unreliable', 'disadvantage']

    response_lower = response.lower()

    positive_count = sum(1 for word in positive_words if word in response_lower)
    negative_count = sum(1 for word in negative_words if word in response_lower)

    if positive_count > negative_count + 1:
        return 'positive'
    elif negative_count > positive_count + 1:
        return 'negative'
    return 'neutral'


def generate_insights(query_results: list, brand_id: str, engine_breakdown: dict) -> list:
    """Generate insights about visibility patterns."""
    insights = []

    if not query_results:
        return ['No query results to analyze']

    # Calculate metrics
    mention_rate = sum(1 for r in query_results if r['brandMentioned']) / len(query_results)
    avg_visibility = sum(r['visibilityScore'] for r in query_results) / len(query_results)

    # Overall visibility insight
    if avg_visibility >= 0.6:
        insights.append(f"Strong visibility: {brand_id} appears prominently in {mention_rate:.0%} of AI responses")
    elif avg_visibility >= 0.3:
        insights.append(f"Moderate visibility: {brand_id} mentioned in {mention_rate:.0%} of responses, but not always prominently")
    else:
        insights.append(f"Low visibility: {brand_id} rarely appears in AI responses ({mention_rate:.0%})")

    # Engine-specific insights
    if engine_breakdown:
        best_engine = max(engine_breakdown.keys(),
                         key=lambda e: engine_breakdown[e].get('averageVisibility', 0))
        worst_engine = min(engine_breakdown.keys(),
                          key=lambda e: engine_breakdown[e].get('averageVisibility', 0))

        if engine_breakdown[best_engine]['averageVisibility'] > engine_breakdown[worst_engine]['averageVisibility'] + 0.2:
            insights.append(f"Best performance on {best_engine}, weakest on {worst_engine}")

    # Position insights
    prominent_count = sum(1 for r in query_results if r.get('position') == 'prominent')
    if prominent_count > 0:
        insights.append(f"Featured prominently in {prominent_count} responses")

    # Sentiment insight
    sentiments = [r.get('sentiment', 'neutral') for r in query_results if r['brandMentioned']]
    if sentiments:
        positive_rate = sentiments.count('positive') / len(sentiments)
        if positive_rate >= 0.6:
            insights.append("Sentiment is predominantly positive when mentioned")
        elif sentiments.count('negative') / len(sentiments) >= 0.3:
            insights.append("Some negative sentiment detected - review mention contexts")

    return insights
