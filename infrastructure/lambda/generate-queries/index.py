"""
Generate Queries Lambda Function

Uses Bedrock Claude to generate persona-specific search queries
that simulate how real users would query AI assistants.
"""
import os
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')

# Bedrock client
bedrock = boto3.client('bedrock-runtime')


def handler(event, context):
    """
    Generate persona-based queries using Bedrock Claude.

    Input:
        {
            "persona": {
                "personaId": "us-army-prospect-male-18-24",
                "demographics": {...},
                "psychographics": {...},
                "queryPatterns": {...}
            },
            "queryCount": 5
        }

    Output:
        {
            "queries": ["query1", "query2", ...],
            "personaId": "...",
            "generatedAt": "..."
        }
    """
    logger.info(f"Generating queries for persona: {event.get('persona', {}).get('personaId')}")

    persona = event.get('persona', {})
    query_count = event.get('queryCount', 5)

    if not persona:
        raise ValueError("persona is required")

    # Build the prompt
    prompt = build_query_generation_prompt(persona, query_count)
    system_prompt = build_system_prompt(persona)

    try:
        # Invoke Bedrock Claude
        response = invoke_claude(system_prompt, prompt)

        # Parse the generated queries
        queries = parse_queries(response)

        logger.info(f"Generated {len(queries)} queries for persona {persona.get('personaId')}")

        return {
            'queries': queries,
            'personaId': persona.get('personaId'),
            'queryCount': len(queries),
            'generatedAt': get_timestamp()
        }

    except Exception as e:
        logger.error(f"Error generating queries: {e}")
        raise


def build_system_prompt(persona: dict) -> str:
    """Build the system prompt for query generation."""
    demographics = persona.get('demographics', {})
    psychographics = persona.get('psychographics', {})
    query_patterns = persona.get('queryPatterns', {})

    age_range = demographics.get('ageRange', [25, 35])
    gender = demographics.get('gender', 'person')

    return f"""You are simulating a {age_range[0]}-{age_range[1]} year old {gender} who is searching for information.

Character traits:
- Education: {demographics.get('education', 'average')}
- Location: {demographics.get('location', 'United States')}
- Interests: {', '.join(psychographics.get('interests', ['general topics']))}
- Concerns: {', '.join(psychographics.get('concerns', ['finding accurate information']))}

Speaking style: {query_patterns.get('speakingStyle', 'casual')}
Patterns to use: {', '.join(query_patterns.get('typicalQuestions', ['how to', 'what is']))}
Patterns to AVOID: {', '.join(query_patterns.get('avoidedPatterns', ['formal language']))}

Generate search queries exactly as this person would type them into an AI assistant like ChatGPT or Perplexity.
Be authentic - use their natural language patterns, including casual phrasing, slang if appropriate, and realistic typos or abbreviations they might use."""


def build_query_generation_prompt(persona: dict, query_count: int) -> str:
    """Build the user prompt for query generation."""
    brand_id = persona.get('brandId', '')
    target_queries = persona.get('targetQueries', [])

    topic_context = ""
    if brand_id:
        topic_context = f"The topics should relate to {brand_id} and what this person might want to know about it."

    examples = ""
    if target_queries:
        examples = f"\n\nExample queries this persona might ask:\n" + "\n".join(f"- {q}" for q in target_queries[:3])

    return f"""Generate exactly {query_count} search queries that this persona would naturally type into an AI assistant.

{topic_context}

Requirements:
1. Each query should sound authentic to this persona's voice and concerns
2. Queries should be the kind someone would actually type, not formal questions
3. Include a mix of question types (how-to, comparison, opinion-seeking, factual)
4. Do NOT use formal or corporate language
5. Do NOT include numbering or explanations - just the raw queries
{examples}

Output only the queries, one per line, no numbering, no explanations:"""


def invoke_claude(system_prompt: str, user_prompt: str) -> str:
    """Invoke Bedrock Claude and return the response."""
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "temperature": 0.8,  # Higher temperature for more creative/varied queries
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
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


def parse_queries(response: str) -> list:
    """Parse the generated queries from Claude's response."""
    # Split by newlines and clean up
    lines = response.strip().split('\n')
    queries = []

    for line in lines:
        # Clean up each line
        query = line.strip()

        # Remove any numbering (1. or 1) or - prefix)
        if query and query[0].isdigit():
            # Remove "1. " or "1) " patterns
            parts = query.split(' ', 1)
            if len(parts) > 1 and (parts[0].endswith('.') or parts[0].endswith(')')):
                query = parts[1].strip()

        if query.startswith('- '):
            query = query[2:].strip()

        # Only include non-empty queries
        if query and len(query) > 5:
            queries.append(query)

    return queries


def get_timestamp() -> str:
    """Get current UTC timestamp."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
