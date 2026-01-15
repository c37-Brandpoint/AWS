"""
Feature Extraction Lambda Function

Extracts features from content for ML model inference.
Used by the Intelligence Engine for content analysis.
"""
import os
import json
import logging
import re
from datetime import datetime
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'amazon.titan-embed-text-v2:0')

# Clients
bedrock = boto3.client('bedrock-runtime')


def handler(event, context):
    """
    Extract features from content.

    Input:
        {
            "content": "...",
            "contentType": "article|social|review",
            "metadata": {...}
        }

    Output:
        {
            "features": {
                "embedding": [...],
                "textFeatures": {...},
                "contentMetrics": {...}
            }
        }
    """
    content = event.get('content', '')
    content_type = event.get('contentType', 'article')
    metadata = event.get('metadata', {})

    if not content:
        raise ValueError("content is required")

    logger.info(f"Extracting features for {content_type} content, length: {len(content)}")

    # Extract text-based features
    text_features = extract_text_features(content)

    # Extract content metrics
    content_metrics = extract_content_metrics(content, content_type)

    # Generate embedding vector
    embedding = generate_embedding(content)

    # Extract entity features
    entity_features = extract_entity_features(content)

    # Extract sentiment features
    sentiment_features = extract_sentiment_features(content)

    return {
        'features': {
            'embedding': embedding,
            'embeddingDimension': len(embedding),
            'textFeatures': text_features,
            'contentMetrics': content_metrics,
            'entityFeatures': entity_features,
            'sentimentFeatures': sentiment_features,
            'contentType': content_type,
            'extractedAt': datetime.utcnow().isoformat() + 'Z'
        }
    }


def extract_text_features(content: str) -> dict:
    """Extract basic text features."""
    words = content.split()
    sentences = re.split(r'[.!?]+', content)
    paragraphs = content.split('\n\n')

    # Calculate readability metrics
    avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
    avg_sentence_length = len(words) / len(sentences) if sentences else 0

    # Extract key phrases (simple approach)
    word_freq = {}
    for word in words:
        word_lower = word.lower().strip('.,!?;:')
        if len(word_lower) > 3:
            word_freq[word_lower] = word_freq.get(word_lower, 0) + 1

    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        'wordCount': len(words),
        'sentenceCount': len([s for s in sentences if s.strip()]),
        'paragraphCount': len([p for p in paragraphs if p.strip()]),
        'avgWordLength': round(avg_word_length, 2),
        'avgSentenceLength': round(avg_sentence_length, 2),
        'uniqueWords': len(set(w.lower() for w in words)),
        'topWords': [{'word': w, 'count': c} for w, c in top_words],
        'hasUrls': bool(re.search(r'https?://', content)),
        'hasEmails': bool(re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', content)),
        'hasMentions': bool(re.search(r'@\w+', content)),
        'hasHashtags': bool(re.search(r'#\w+', content))
    }


def extract_content_metrics(content: str, content_type: str) -> dict:
    """Extract content-type specific metrics."""
    metrics = {
        'characterCount': len(content),
        'contentType': content_type
    }

    if content_type == 'article':
        # Article-specific metrics
        metrics['hasHeadings'] = bool(re.search(r'^#+\s|<h[1-6]>', content, re.MULTILINE))
        metrics['hasLists'] = bool(re.search(r'^[\-\*]\s|^\d+\.\s', content, re.MULTILINE))
        metrics['hasQuotes'] = bool(re.search(r'^>\s|"[^"]{20,}"', content, re.MULTILINE))
        metrics['estimatedReadTime'] = len(content.split()) // 200  # ~200 WPM

    elif content_type == 'social':
        # Social media specific metrics
        metrics['mentionCount'] = len(re.findall(r'@\w+', content))
        metrics['hashtagCount'] = len(re.findall(r'#\w+', content))
        metrics['urlCount'] = len(re.findall(r'https?://\S+', content))
        metrics['emojiCount'] = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]', content))

    elif content_type == 'review':
        # Review specific metrics
        metrics['hasRating'] = bool(re.search(r'\d+(/\d+|\s*stars?|\s*out of)', content, re.IGNORECASE))
        metrics['hasProsAndCons'] = bool(re.search(r'pros?|cons?|advantages?|disadvantages?', content, re.IGNORECASE))

    return metrics


def generate_embedding(content: str) -> list:
    """Generate embedding vector using Bedrock Titan."""
    # Truncate content if too long (Titan has input limits)
    max_chars = 8000
    truncated_content = content[:max_chars] if len(content) > max_chars else content

    try:
        body = {
            "inputText": truncated_content
        }

        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response['body'].read())
        embedding = response_body.get('embedding', [])

        logger.info(f"Generated embedding with {len(embedding)} dimensions")
        return embedding

    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        # Return zero vector as fallback
        return [0.0] * 1536


def extract_entity_features(content: str) -> dict:
    """Extract named entity features."""
    # Simple entity extraction (production would use NER model)
    entities = {
        'organizations': [],
        'locations': [],
        'persons': [],
        'dates': [],
        'urls': []
    }

    # Extract URLs
    urls = re.findall(r'https?://\S+', content)
    entities['urls'] = urls[:10]

    # Extract dates
    date_patterns = [
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b'
    ]
    for pattern in date_patterns:
        dates = re.findall(pattern, content, re.IGNORECASE)
        entities['dates'].extend(dates)
    entities['dates'] = list(set(entities['dates']))[:10]

    # Extract capitalized phrases (potential organizations/names)
    cap_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', content)
    entities['potential_entities'] = list(set(cap_phrases))[:20]

    return {
        'entityCounts': {k: len(v) for k, v in entities.items()},
        'entities': entities
    }


def extract_sentiment_features(content: str) -> dict:
    """Extract sentiment-related features."""
    content_lower = content.lower()

    # Sentiment lexicons
    positive_words = [
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'best', 'love', 'perfect', 'awesome', 'outstanding', 'brilliant',
        'recommend', 'happy', 'pleased', 'satisfied', 'impressive'
    ]
    negative_words = [
        'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'poor',
        'disappointing', 'frustrated', 'angry', 'avoid', 'problem', 'issue',
        'fail', 'broken', 'useless', 'waste'
    ]
    intensity_words = [
        'very', 'extremely', 'incredibly', 'absolutely', 'totally',
        'really', 'highly', 'completely', 'utterly', 'definitely'
    ]
    negation_words = ['not', 'never', 'no', 'none', 'neither', 'nor', "n't", 'without']

    positive_count = sum(1 for w in positive_words if w in content_lower)
    negative_count = sum(1 for w in negative_words if w in content_lower)
    intensity_count = sum(1 for w in intensity_words if w in content_lower)
    negation_count = sum(1 for w in negation_words if w in content_lower)

    # Calculate sentiment score
    total_sentiment_words = positive_count + negative_count
    if total_sentiment_words > 0:
        sentiment_score = (positive_count - negative_count) / total_sentiment_words
    else:
        sentiment_score = 0.0

    return {
        'positiveWordCount': positive_count,
        'negativeWordCount': negative_count,
        'intensityWordCount': intensity_count,
        'negationWordCount': negation_count,
        'sentimentScore': round(sentiment_score, 3),
        'sentimentLabel': 'positive' if sentiment_score > 0.2 else ('negative' if sentiment_score < -0.2 else 'neutral')
    }
