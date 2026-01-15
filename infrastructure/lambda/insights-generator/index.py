"""
Insights Generator Lambda Function

Generates strategic insights using LLM analysis of aggregated
intelligence data from OpenSearch and Neptune.
"""
import os
import json
import logging
from datetime import datetime
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')

# Clients
bedrock = boto3.client('bedrock-runtime')


def handler(event, context):
    """
    Generate insights from intelligence data.

    Input:
        {
            "insightType": "visibility|competitive|content|recommendations",
            "brandId": "...",
            "data": {
                "visibilityResults": [...],
                "graphData": {...},
                "similarContent": [...],
                "historicalTrends": {...}
            }
        }

    Output:
        {
            "insights": [...],
            "recommendations": [...],
            "summary": "..."
        }
    """
    insight_type = event.get('insightType', 'visibility')
    brand_id = event.get('brandId', '')
    data = event.get('data', {})

    logger.info(f"Generating {insight_type} insights for brand: {brand_id}")

    if insight_type == 'visibility':
        return generate_visibility_insights(brand_id, data)
    elif insight_type == 'competitive':
        return generate_competitive_insights(brand_id, data)
    elif insight_type == 'content':
        return generate_content_insights(brand_id, data)
    elif insight_type == 'recommendations':
        return generate_recommendations(brand_id, data)
    else:
        raise ValueError(f"Unknown insight type: {insight_type}")


def generate_visibility_insights(brand_id: str, data: dict) -> dict:
    """Generate visibility-focused insights."""
    visibility_results = data.get('visibilityResults', [])
    engine_breakdown = data.get('engineBreakdown', {})
    historical = data.get('historicalTrends', {})

    # Prepare context for LLM
    context = f"""
Analyze the following AI visibility data for brand "{brand_id}":

Current Visibility Scores by Engine:
{json.dumps(engine_breakdown, indent=2)}

Recent Query Results Summary:
- Total queries analyzed: {len(visibility_results)}
- Queries with brand mention: {sum(1 for r in visibility_results if r.get('brandMentioned'))}
- Average visibility score: {sum(r.get('visibilityScore', 0) for r in visibility_results) / len(visibility_results) if visibility_results else 0:.2%}

Position Distribution:
- Prominent mentions: {sum(1 for r in visibility_results if r.get('position') == 'prominent')}
- Middle mentions: {sum(1 for r in visibility_results if r.get('position') == 'middle')}
- Late mentions: {sum(1 for r in visibility_results if r.get('position') == 'late')}

Sentiment Distribution:
- Positive: {sum(1 for r in visibility_results if r.get('sentiment') == 'positive')}
- Neutral: {sum(1 for r in visibility_results if r.get('sentiment') == 'neutral')}
- Negative: {sum(1 for r in visibility_results if r.get('sentiment') == 'negative')}

Historical context: {json.dumps(historical, indent=2) if historical else 'No historical data available'}
"""

    prompt = f"""Based on the visibility data provided, generate actionable insights.

{context}

Provide your analysis in the following JSON format:
{{
    "keyFindings": ["finding1", "finding2", "finding3"],
    "strengthAreas": ["strength1", "strength2"],
    "improvementAreas": ["area1", "area2"],
    "engineSpecificInsights": {{"engine": "insight"}},
    "recommendedActions": ["action1", "action2", "action3"],
    "riskFactors": ["risk1", "risk2"],
    "summary": "2-3 sentence executive summary"
}}

Respond only with the JSON object, no additional text."""

    response = invoke_bedrock(prompt)
    insights = parse_json_response(response)

    return {
        'insightType': 'visibility',
        'brandId': brand_id,
        'generatedAt': datetime.utcnow().isoformat() + 'Z',
        **insights
    }


def generate_competitive_insights(brand_id: str, data: dict) -> dict:
    """Generate competitive landscape insights."""
    competitors = data.get('competitors', [])
    graph_data = data.get('graphData', {})
    market_data = data.get('marketData', {})

    context = f"""
Analyze the competitive landscape for brand "{brand_id}":

Competitors identified (by co-mention frequency):
{json.dumps(competitors[:10], indent=2)}

Brand relationship network:
- Connected entities: {graph_data.get('nodeCount', 0)}
- Relationship strength: {graph_data.get('edgeCount', 0)} connections

Market positioning data: {json.dumps(market_data, indent=2) if market_data else 'Not available'}
"""

    prompt = f"""Analyze the competitive landscape and provide strategic insights.

{context}

Provide your analysis in the following JSON format:
{{
    "competitivePosition": "description of current position",
    "mainCompetitors": ["competitor1", "competitor2"],
    "competitorStrengths": {{"competitor": ["strength1", "strength2"]}},
    "differentiationOpportunities": ["opportunity1", "opportunity2"],
    "marketGaps": ["gap1", "gap2"],
    "competitiveThreats": ["threat1", "threat2"],
    "recommendedStrategies": ["strategy1", "strategy2"],
    "summary": "2-3 sentence executive summary"
}}

Respond only with the JSON object, no additional text."""

    response = invoke_bedrock(prompt)
    insights = parse_json_response(response)

    return {
        'insightType': 'competitive',
        'brandId': brand_id,
        'generatedAt': datetime.utcnow().isoformat() + 'Z',
        **insights
    }


def generate_content_insights(brand_id: str, data: dict) -> dict:
    """Generate content strategy insights."""
    similar_content = data.get('similarContent', [])
    topic_analysis = data.get('topicAnalysis', {})
    content_metrics = data.get('contentMetrics', {})

    context = f"""
Analyze content patterns for brand "{brand_id}":

Top associated topics:
{json.dumps(topic_analysis.get('topics', [])[:15], indent=2)}

Similar content found: {len(similar_content)} pieces
Content types distribution: {json.dumps(content_metrics.get('typeDistribution', {}), indent=2)}

Average content metrics:
- Word count: {content_metrics.get('avgWordCount', 'N/A')}
- Sentiment: {content_metrics.get('avgSentiment', 'N/A')}
"""

    prompt = f"""Analyze the content patterns and provide strategic insights.

{context}

Provide your analysis in the following JSON format:
{{
    "dominantTopics": ["topic1", "topic2", "topic3"],
    "contentGaps": ["gap1", "gap2"],
    "topPerformingContentTypes": ["type1", "type2"],
    "topicOpportunities": ["opportunity1", "opportunity2"],
    "contentRecommendations": ["recommendation1", "recommendation2"],
    "audienceInterests": ["interest1", "interest2"],
    "trendingThemes": ["theme1", "theme2"],
    "summary": "2-3 sentence executive summary"
}}

Respond only with the JSON object, no additional text."""

    response = invoke_bedrock(prompt)
    insights = parse_json_response(response)

    return {
        'insightType': 'content',
        'brandId': brand_id,
        'generatedAt': datetime.utcnow().isoformat() + 'Z',
        **insights
    }


def generate_recommendations(brand_id: str, data: dict) -> dict:
    """Generate comprehensive recommendations."""
    visibility = data.get('visibilityResults', [])
    competitors = data.get('competitors', [])
    content = data.get('contentAnalysis', {})
    historical = data.get('historicalTrends', {})

    context = f"""
Generate strategic recommendations for brand "{brand_id}" based on:

Visibility Performance:
- Overall visibility score: {data.get('overallVisibility', 0):.2%}
- Best performing engine: {data.get('bestEngine', 'Unknown')}
- Areas needing improvement: {data.get('improvementAreas', [])}

Competitive Position:
- Main competitors: {[c.get('name', c.get('brandId')) for c in competitors[:5]]}
- Market differentiation: {data.get('differentiation', 'Not analyzed')}

Content Strategy:
- Top topics: {content.get('topTopics', [])}
- Content gaps: {content.get('gaps', [])}

Historical Performance:
{json.dumps(historical, indent=2) if historical else 'No historical data'}
"""

    prompt = f"""Based on the comprehensive data provided, generate prioritized strategic recommendations.

{context}

Provide your recommendations in the following JSON format:
{{
    "immediateActions": [
        {{"action": "description", "priority": "high/medium/low", "impact": "expected impact", "effort": "low/medium/high"}}
    ],
    "shortTermStrategies": [
        {{"strategy": "description", "timeline": "1-4 weeks", "expectedOutcome": "outcome"}}
    ],
    "longTermInitiatives": [
        {{"initiative": "description", "timeline": "1-3 months", "expectedOutcome": "outcome"}}
    ],
    "contentCalendarSuggestions": ["suggestion1", "suggestion2"],
    "keyMetricsToTrack": ["metric1", "metric2"],
    "riskMitigation": ["action1", "action2"],
    "executiveSummary": "3-4 sentence summary of the most critical recommendations"
}}

Respond only with the JSON object, no additional text."""

    response = invoke_bedrock(prompt)
    insights = parse_json_response(response)

    return {
        'insightType': 'recommendations',
        'brandId': brand_id,
        'generatedAt': datetime.utcnow().isoformat() + 'Z',
        **insights
    }


def invoke_bedrock(prompt: str) -> str:
    """Invoke Bedrock Claude model."""
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 0.3,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']


def parse_json_response(response: str) -> dict:
    """Parse JSON from LLM response."""
    try:
        # Try to extract JSON from response
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]

        return json.loads(response.strip())
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON response: {e}")
        return {
            'rawResponse': response,
            'parseError': str(e)
        }
