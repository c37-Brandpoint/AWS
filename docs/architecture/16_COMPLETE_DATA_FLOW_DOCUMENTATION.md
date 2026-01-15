# Complete Data Flow Documentation

## Brandpoint Intelligence Engine POC - End-to-End Data Flows

This document provides comprehensive documentation of all data flows within the Brandpoint AI Platform, including request/response formats, database operations, and error handling.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Flow 1: Content Prediction (Hub → AWS → Hub)](#data-flow-1-content-prediction)
3. [Data Flow 2: Persona Agent Execution](#data-flow-2-persona-agent-execution)
4. [Data Flow 3: Hub to AWS Data Sync](#data-flow-3-hub-to-aws-data-sync)
5. [Data Flow 4: AWS to Hub Results Sync](#data-flow-4-aws-to-hub-results-sync)
6. [Data Flow 5: Intelligence Engine Ingestion](#data-flow-5-intelligence-engine-ingestion)
7. [Data Flow 6: Intelligence Engine Query](#data-flow-6-intelligence-engine-query)
8. [Database Schema Reference](#database-schema-reference)
9. [API Contract Reference](#api-contract-reference)
10. [Error Handling](#error-handling)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  COMPLETE DATA FLOW MAP                                   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────────┐                              ┌─────────────────────────────────────┐│
│  │  LEGACY HUB     │                              │         AWS CLOUD PLATFORM           ││
│  │  (.NET 4.7.2)   │                              │                                      ││
│  │                 │                              │  ┌──────────────────────────────┐   ││
│  │  ┌───────────┐  │     FLOW 1: Prediction       │  │     API GATEWAY               │   ││
│  │  │ Hub UI    │──┼──────────────────────────────┼─►│  POST /predict/{contentId}    │   ││
│  │  └───────────┘  │                              │  │  POST /persona/execute        │   ││
│  │                 │     FLOW 4: Results          │  │  POST /intel/similar          │   ││
│  │  ┌───────────┐  │◄─────────────────────────────┼──│  POST /intel/ingest           │   ││
│  │  │ Hub API   │  │                              │  └──────────────────────────────┘   ││
│  │  │           │  │                              │              │                       ││
│  │  │ Endpoints:│  │                              │              ▼                       ││
│  │  │ /predict  │  │                              │  ┌──────────────────────────────┐   ││
│  │  │ /persona  │  │                              │  │        LAMBDA LAYER           │   ││
│  │  └───────────┘  │                              │  │  - FeatureExtraction          │   ││
│  │                 │                              │  │  - QueryExecution             │   ││
│  │  ┌───────────┐  │                              │  │  - ResultProcessor            │   ││
│  │  │ ARA3 SQL  │  │     FLOW 3: Read Data        │  │  - IntelligenceQuery          │   ││
│  │  │ Server    │──┼──────────────────────────────┼─►│                                │   ││
│  │  │           │  │                              │  └──────────────────────────────┘   ││
│  │  │ Tables:   │  │                              │              │                       ││
│  │  │ -HubContent│ │                              │              ▼                       ││
│  │  │ -Article  │  │                              │  ┌──────────────────────────────┐   ││
│  │  │ -AiMonitor│  │                              │  │     PROCESSING LAYER          │   ││
│  │  │ -AiContent│  │                              │  │  - SageMaker (ML)             │   ││
│  │  │  Predict  │  │                              │  │  - Bedrock (LLM)              │   ││
│  │  │ -Persona  │  │                              │  │  - Step Functions             │   ││
│  │  │  Result   │  │                              │  └──────────────────────────────┘   ││
│  │  └───────────┘  │                              │              │                       ││
│  │                 │                              │              ▼                       ││
│  └─────────────────┘                              │  ┌──────────────────────────────┐   ││
│                                                   │  │     DATA STORES               │   ││
│                                                   │  │  - DynamoDB (Personas)        │   ││
│                                                   │  │  - OpenSearch (Vectors)       │   ││
│                                                   │  │  - Neptune (Graph)            │   ││
│                                                   │  │  - S3 (Models/Archives)       │   ││
│                                                   │  └──────────────────────────────┘   ││
│                                                   └─────────────────────────────────────┘│
│                                                                                          │
│  EXTERNAL AI ENGINES (FLOW 2)                                                            │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐                               │
│  │  ChatGPT  │ │ Perplexity│ │  Gemini   │ │  Claude   │                               │
│  │  (OpenAI) │ │           │ │ (Google)  │ │(Anthropic)│                               │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘                               │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow 1: Content Prediction

### Overview
When a user requests an AI visibility prediction for content, this flow extracts features, runs ML inference, and stores results.

### Sequence Diagram

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Hub UI  │     │ Hub API │     │API Gate │     │ Lambda  │     │SageMaker│     │ ARA3 DB │
└────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
     │               │               │               │               │               │
     │ 1. Click      │               │               │               │               │
     │   "Predict"   │               │               │               │               │
     │──────────────►│               │               │               │               │
     │               │               │               │               │               │
     │               │ 2. POST       │               │               │               │
     │               │  /predict/123 │               │               │               │
     │               │──────────────►│               │               │               │
     │               │               │               │               │               │
     │               │               │ 3. Invoke     │               │               │
     │               │               │   Lambda      │               │               │
     │               │               │──────────────►│               │               │
     │               │               │               │               │               │
     │               │               │               │ 4. Read Content               │
     │               │               │               │───────────────────────────────►
     │               │               │               │               │               │
     │               │               │               │◄───────────────────────────────
     │               │               │               │    Content Data               │
     │               │               │               │               │               │
     │               │               │               │ 5. Extract    │               │
     │               │               │               │   Features    │               │
     │               │               │               │               │               │
     │               │               │               │ 6. Invoke     │               │
     │               │               │               │──────────────►│               │
     │               │               │               │               │               │
     │               │               │               │◄──────────────│               │
     │               │               │               │  Prediction   │               │
     │               │               │               │               │               │
     │               │               │ 7. Store Result               │               │
     │               │               │◄──────────────│               │               │
     │               │               │               │               │               │
     │               │ 8. POST /api/predictions/content/123          │               │
     │               │◄──────────────│               │               │               │
     │               │               │               │               │               │
     │               │ 9. INSERT                     │               │               │
     │               │──────────────────────────────────────────────────────────────►
     │               │               │               │               │               │
     │ 10. Display   │               │               │               │               │
     │    Results    │               │               │               │               │
     │◄──────────────│               │               │               │               │
     │               │               │               │               │               │
```

### Step Details

#### Step 1-2: Request Initiation
```
Hub UI → Hub Backend → AWS API Gateway

HTTP Request:
POST https://api.brandpoint-ai.aws/predict/{contentId}
Headers:
  Authorization: Bearer {jwt_token}
  X-Api-Key: {hub_api_key}
  Content-Type: application/json

Body (optional - for draft content):
{
  "headline": "New Article Headline",
  "body": "Article body content...",
  "publisherId": 456,
  "topics": ["technology", "AI"]
}
```

#### Step 3-4: Feature Extraction
```
Lambda: feature-extraction

Input (from API Gateway):
{
  "contentId": 123,
  "source": "hub",
  "content": { ... }  // Optional draft content
}

Database Read (if contentId provided):
SELECT
  c.ContentId,
  c.Headline,
  c.Body,
  c.PublisherId,
  p.DomainAuthority,
  p.IsAiCrawlable,
  COUNT(a.AccessId) as EngagementCount
FROM HubContent c
JOIN Publisher p ON c.PublisherId = p.PublisherId
LEFT JOIN ArticleAccess a ON c.ContentId = a.ContentId
WHERE c.ContentId = 123
GROUP BY c.ContentId, c.Headline, c.Body, c.PublisherId,
         p.DomainAuthority, p.IsAiCrawlable
```

#### Step 5: Feature Vector Creation
```python
# Lambda feature extraction logic
features = {
    # Text Features
    "headline_length": len(headline),
    "headline_has_question": "?" in headline,
    "headline_has_number": bool(re.search(r'\d', headline)),
    "body_length": len(body),
    "readability_score": calculate_flesch_kincaid(body),
    "keyword_density": calculate_keyword_density(body, topics),

    # Publisher Features
    "domain_authority": publisher.domain_authority,
    "is_ai_crawlable": publisher.is_ai_crawlable,

    # Entity Features
    "has_wikipedia_entity": check_wikipedia_entities(body),
    "entity_count": extract_entity_count(body),

    # Historical Features (if available)
    "past_visibility_rate": calculate_historical_rate(client_id),
    "engagement_score": normalize_engagement(engagement_count)
}
```

#### Step 6: ML Inference
```
SageMaker Endpoint: brandpoint-visibility-predictor

Input:
{
  "instances": [
    {
      "features": [0.72, 1, 0, 2500, 65.4, 0.03, 45, 1, 1, 5, 0.35, 0.8]
    }
  ]
}

Output:
{
  "predictions": [
    {
      "visibility_score": 0.73,
      "confidence": 0.85,
      "class_probabilities": {
        "will_appear": 0.73,
        "wont_appear": 0.27
      },
      "feature_importance": {
        "is_ai_crawlable": 0.25,
        "domain_authority": 0.18,
        "readability_score": 0.15,
        "headline_has_question": 0.12,
        "entity_count": 0.10
      }
    }
  ]
}
```

#### Step 7-9: Result Storage
```
AWS Lambda → Hub API

HTTP Request:
POST https://hub.brandpoint.com/api/predictions/content/123
Headers:
  X-Api-Key: {aws_service_account_key}
  Content-Type: application/json

Body:
{
  "predictionScore": 0.73,
  "confidenceScore": 0.85,
  "topFactors": [
    {"factor": "is_ai_crawlable", "importance": 0.25, "value": true},
    {"factor": "domain_authority", "importance": 0.18, "value": 45},
    {"factor": "readability_score", "importance": 0.15, "value": 65.4}
  ],
  "recommendations": [
    "Consider adding more structured data markup",
    "Include FAQ sections to match question-based queries",
    "Add citations to authoritative sources"
  ],
  "modelVersion": "v1.2.0"
}

Hub API → SQL Insert:
INSERT INTO AiContentPrediction (
  PredictionId, ContentId, PredictionScore, ConfidenceScore,
  TopFactors, Recommendations, ModelVersion, CreatedAt
) VALUES (
  NEWID(), 123, 0.73, 0.85,
  '[{"factor":"is_ai_crawlable",...}]',
  '["Consider adding..."]',
  'v1.2.0', GETUTCDATE()
)
```

---

## Data Flow 2: Persona Agent Execution

### Overview
Scheduled or on-demand execution of persona agents that generate realistic queries, execute them across AI engines, and analyze results.

### Sequence Diagram

```
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│EventBrdg│  │Step Func│  │DynamoDB │  │ Bedrock │  │ Lambda  │  │External │  │ Hub API │
└────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
     │            │            │            │            │            │            │
     │ 1. Trigger │            │            │            │            │            │
     │  (cron)    │            │            │            │            │            │
     │───────────►│            │            │            │            │            │
     │            │            │            │            │            │            │
     │            │ 2. Get     │            │            │            │            │
     │            │   Persona  │            │            │            │            │
     │            │───────────►│            │            │            │            │
     │            │            │            │            │            │            │
     │            │◄───────────│            │            │            │            │
     │            │  Persona   │            │            │            │            │
     │            │  Data      │            │            │            │            │
     │            │            │            │            │            │            │
     │            │ 3. Generate│            │            │            │            │
     │            │   Queries  │            │            │            │            │
     │            │───────────────────────►│            │            │            │
     │            │            │            │            │            │            │
     │            │◄───────────────────────│            │            │            │
     │            │   Queries  │            │            │            │            │
     │            │            │            │            │            │            │
     │            │ 4. Execute │            │            │            │            │
     │            │   (parallel)            │            │            │            │
     │            │──────────────────────────────────────►            │            │
     │            │            │            │            │            │            │
     │            │            │            │            │ 5. Query   │            │
     │            │            │            │            │───────────►│            │
     │            │            │            │            │            │            │
     │            │            │            │            │◄───────────│            │
     │            │            │            │            │  Response  │            │
     │            │            │            │            │            │            │
     │            │◄──────────────────────────────────────            │            │
     │            │   Results  │            │            │            │            │
     │            │            │            │            │            │            │
     │            │ 6. Analyze │            │            │            │            │
     │            │   Results  │            │            │            │            │
     │            │───────────────────────►│            │            │            │
     │            │            │            │            │            │            │
     │            │◄───────────────────────│            │            │            │
     │            │  Analysis  │            │            │            │            │
     │            │            │            │            │            │            │
     │            │ 7. Store to DynamoDB   │            │            │            │
     │            │───────────►│            │            │            │            │
     │            │            │            │            │            │            │
     │            │ 8. Sync to Hub         │            │            │            │
     │            │───────────────────────────────────────────────────────────────►│
     │            │            │            │            │            │            │
```

### Step Details

#### Step 1: EventBridge Trigger
```json
// EventBridge Rule
{
  "Name": "persona-agent-schedule",
  "ScheduleExpression": "cron(0 6 * * ? *)",  // Daily at 6 AM UTC
  "State": "ENABLED",
  "Targets": [
    {
      "Arn": "arn:aws:states:us-east-1:123456789:stateMachine:PersonaAgentWorkflow",
      "Input": {
        "executionType": "scheduled",
        "batchSize": 10
      }
    }
  ]
}
```

#### Step 2: Load Persona from DynamoDB
```json
// DynamoDB GetItem
{
  "TableName": "brandpoint-personas",
  "Key": {
    "personaId": {"S": "us-army-prospect-male-18-24"},
    "clientId": {"N": "123"}
  }
}

// Response
{
  "Item": {
    "personaId": {"S": "us-army-prospect-male-18-24"},
    "clientId": {"N": "123"},
    "brandId": {"S": "us-army"},
    "demographics": {
      "M": {
        "ageRange": {"L": [{"N": "18"}, {"N": "24"}]},
        "gender": {"S": "male"},
        "education": {"S": "high_school_senior"},
        "location": {"S": "suburban_midwest"}
      }
    },
    "psychographics": {
      "M": {
        "interests": {"L": [{"S": "gaming"}, {"S": "career_options"}]},
        "concerns": {"L": [{"S": "student_debt"}, {"S": "job_security"}]},
        "mediaConsumption": {"L": [{"S": "tiktok"}, {"S": "youtube"}]}
      }
    },
    "queryPatterns": {
      "M": {
        "speakingStyle": {"S": "casual_with_slang"},
        "avoidedPatterns": {"L": [{"S": "formal_language"}]}
      }
    },
    "targetTopics": {"L": [{"S": "military_careers"}, {"S": "army_benefits"}]},
    "isActive": {"BOOL": true},
    "lastExecutedAt": {"S": "2025-12-21T06:00:00Z"}
  }
}
```

#### Step 3: Generate Queries via Bedrock
```json
// Bedrock InvokeModel Request
{
  "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "contentType": "application/json",
  "body": {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1024,
    "system": "You are simulating a specific user persona to generate realistic search queries they would type into an AI assistant. Generate natural, authentic queries that reflect the persona's speaking style, concerns, and interests.",
    "messages": [
      {
        "role": "user",
        "content": "Generate 5 search queries that a 18-24 year old male high school senior from the suburban midwest would naturally type into an AI assistant when exploring military career options. \n\nPersona details:\n- Interests: gaming, career options\n- Concerns: student debt, job security\n- Speaking style: casual with slang\n- Avoid: formal language, industry jargon\n\nThe queries should feel authentic - like something you'd see in a Reddit post or text message, not a formal research paper. Return as JSON array."
      }
    ]
  }
}

// Bedrock Response
{
  "content": [
    {
      "type": "text",
      "text": "[\"is joining the army worth it in 2025\", \"army vs marines which one is better\", \"do you actually get free college from the army\", \"what jobs in the army dont see combat\", \"how much do you make starting out in the army\"]"
    }
  ]
}
```

#### Step 4-5: Execute Queries Across AI Engines
```python
# Lambda: query-executor

# Parallel execution across engines
engines = {
    "chatgpt": {
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4-turbo-preview"
    },
    "perplexity": {
        "endpoint": "https://api.perplexity.ai/chat/completions",
        "model": "llama-3.1-sonar-large-128k-online"
    },
    "gemini": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
    },
    "claude": {
        "endpoint": "https://api.anthropic.com/v1/messages",
        "model": "claude-3-5-sonnet-20241022"
    }
}

# Request format (ChatGPT example)
{
    "model": "gpt-4-turbo-preview",
    "messages": [
        {"role": "user", "content": "is joining the army worth it in 2025"}
    ],
    "max_tokens": 2048
}

# Response captured
{
    "query": "is joining the army worth it in 2025",
    "engine": "chatgpt",
    "response": "Whether joining the Army in 2025 is worth it depends on your personal goals...",
    "executedAt": "2025-12-22T06:01:23Z",
    "latencyMs": 1847
}
```

#### Step 6: Analyze Results via Bedrock
```json
// Analysis Request
{
  "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "body": {
    "messages": [
      {
        "role": "user",
        "content": "Analyze these AI responses for brand visibility. For each response, determine:\n1. Was 'US Army' mentioned? (boolean)\n2. Visibility score 0-1 (how prominently featured)\n3. Sentiment toward the brand (-1 to 1)\n4. Key themes mentioned\n\nResponses:\n[4 engine responses here]\n\nReturn as JSON."
      }
    ]
  }
}

// Analysis Response
{
  "results": [
    {
      "engine": "chatgpt",
      "brandMentioned": true,
      "visibilityScore": 0.65,
      "sentiment": 0.3,
      "themes": ["career opportunity", "education benefits", "commitment required"],
      "brandPosition": "mentioned in list of military branches"
    },
    {
      "engine": "perplexity",
      "brandMentioned": true,
      "visibilityScore": 0.82,
      "sentiment": 0.5,
      "themes": ["benefits", "signing bonus", "job training"],
      "brandPosition": "featured prominently with statistics"
    }
    // ... other engines
  ],
  "aggregated": {
    "overallVisibility": 0.68,
    "averageSentiment": 0.35,
    "mentionRate": 0.75
  }
}
```

#### Step 7-8: Store Results
```json
// DynamoDB PutItem
{
  "TableName": "brandpoint-persona-results",
  "Item": {
    "executionId": {"S": "exec-2025-12-22-06-00-123"},
    "personaId": {"S": "us-army-prospect-male-18-24"},
    "executedAt": {"S": "2025-12-22T06:05:00Z"},
    "queries": {
      "L": [
        {
          "M": {
            "queryText": {"S": "is joining the army worth it in 2025"},
            "results": {
              "L": [
                {
                  "M": {
                    "engine": {"S": "chatgpt"},
                    "brandMentioned": {"BOOL": true},
                    "visibilityScore": {"N": "0.65"},
                    "sentiment": {"N": "0.3"},
                    "responseLength": {"N": "1847"}
                  }
                }
                // ... other engines
              ]
            }
          }
        }
        // ... other queries
      ]
    },
    "aggregatedMetrics": {
      "M": {
        "overallVisibility": {"N": "0.68"},
        "averageSentiment": {"N": "0.35"},
        "mentionRate": {"N": "0.75"}
      }
    }
  }
}

// Hub API Sync
POST https://hub.brandpoint.com/api/predictions/persona/results
{
  "executionId": "exec-2025-12-22-06-00-123",
  "personaId": "us-army-prospect-male-18-24",
  "clientId": 123,
  "results": [
    {
      "queryText": "is joining the army worth it in 2025",
      "engine": "chatgpt",
      "brandMentioned": true,
      "visibilityScore": 0.65,
      "sentiment": 0.3,
      "executedAt": "2025-12-22T06:01:23Z"
    }
    // ... all results
  ]
}

// SQL Insert (batch)
INSERT INTO PersonaQueryResult (
  ResultId, ExecutionId, PersonaId, QueryText, Engine,
  ResponseText, BrandMentioned, VisibilityScore, ExecutedAt, CreatedAt
) VALUES
  (NEWID(), 'exec-2025-12-22-06-00-123', 'us-army-prospect-male-18-24',
   'is joining the army worth it in 2025', 'chatgpt',
   '...response...', 1, 0.65, '2025-12-22T06:01:23Z', GETUTCDATE()),
  -- ... batch insert all results
```

---

## Data Flow 3: Hub to AWS Data Sync

### Overview
Read-only data flow from Hub's ARA3 database to AWS for ML training, feature extraction, and content analysis.

### Data Sources

```
ARA3 SQL Server (Read-Only Access)
    │
    ├── HubContent (Content metadata, text)
    │   └── Used for: Feature extraction, training labels
    │
    ├── Article (Published articles)
    │   └── Used for: Historical performance data
    │
    ├── ArticleAccess (Engagement metrics)
    │   └── Used for: Engagement features
    │
    ├── AiMonitorResult (AI visibility data - 49K+ records)
    │   └── Used for: Training labels, validation
    │
    ├── Client (Client information)
    │   └── Used for: Segmentation, personalization
    │
    └── Publisher (Publisher metadata)
        └── Used for: Domain authority, crawlability
```

### Sync Patterns

#### Pattern A: On-Demand Feature Extraction
```sql
-- Lambda direct query for single content
SELECT
    c.ContentId,
    c.Headline,
    c.Body,
    c.PublisherId,
    c.ClientId,
    c.DateCreated,
    p.PublisherName,
    p.DomainUrl,
    p.DomainAuthority,
    p.IsAiCrawlable,
    cl.ClientName,
    (SELECT COUNT(*) FROM ArticleAccess aa WHERE aa.ContentId = c.ContentId) as AccessCount
FROM HubContent c
JOIN Publisher p ON c.PublisherId = p.PublisherId
JOIN Client cl ON c.ClientId = cl.ClientId
WHERE c.ContentId = @ContentId
```

#### Pattern B: Batch Training Data Export
```sql
-- S3 data export for ML training (scheduled)
SELECT
    amr.ResultId,
    amr.MonitoredContentId,
    amr.QueryText,
    amr.AiEngine,
    amr.BrandWasMentioned,
    amr.ResponseText,
    amr.ExecutionDate,
    c.Headline,
    c.Body,
    c.PublisherId,
    p.DomainAuthority,
    p.IsAiCrawlable
FROM AiMonitorResult amr
LEFT JOIN HubContent c ON amr.MonitoredContentId = c.ContentId
LEFT JOIN Publisher p ON c.PublisherId = p.PublisherId
WHERE amr.ExecutionDate >= @StartDate
ORDER BY amr.ExecutionDate

-- Exported to: s3://brandpoint-ml/training-data/ai-monitor-export-{date}.parquet
```

#### Pattern C: Real-time Content Event (Future)
```json
// When content is published in Hub, trigger AWS ingestion
// Hub publishes to SNS topic

{
  "eventType": "CONTENT_PUBLISHED",
  "timestamp": "2025-12-22T10:30:00Z",
  "payload": {
    "contentId": 12345,
    "clientId": 123,
    "publisherId": 456,
    "headline": "New Article Title",
    "publishUrl": "https://example.com/article/12345"
  }
}
```

---

## Data Flow 4: AWS to Hub Results Sync

### Overview
Write path for storing AI predictions and persona results back to Hub's database.

### Sync Endpoints

#### Endpoint 1: Store Prediction
```
POST /api/predictions/content/{contentId}

Request:
{
  "predictionScore": 0.73,
  "confidenceScore": 0.85,
  "topFactors": [
    {"factor": "is_ai_crawlable", "importance": 0.25, "value": true},
    {"factor": "domain_authority", "importance": 0.18, "value": 45}
  ],
  "recommendations": [
    "Add structured data markup",
    "Include FAQ sections"
  ],
  "modelVersion": "v1.2.0"
}

Response:
{
  "success": true,
  "predictionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "storedAt": "2025-12-22T10:35:00Z"
}
```

#### Endpoint 2: Store Persona Results
```
POST /api/predictions/persona/results

Request:
{
  "executionId": "exec-2025-12-22-06-00-123",
  "personaId": "us-army-prospect-male-18-24",
  "clientId": 123,
  "results": [
    {
      "queryText": "is joining the army worth it in 2025",
      "engine": "chatgpt",
      "responseText": "Whether joining...",
      "brandMentioned": true,
      "visibilityScore": 0.65,
      "executedAt": "2025-12-22T06:01:23Z"
    }
  ]
}

Response:
{
  "success": true,
  "resultsStored": 4,
  "executionId": "exec-2025-12-22-06-00-123"
}
```

#### Endpoint 3: Get Predictions
```
GET /api/predictions/content/{contentId}

Response:
{
  "contentId": 123,
  "predictions": [
    {
      "predictionId": "a1b2c3d4-...",
      "predictionScore": 0.73,
      "confidenceScore": 0.85,
      "topFactors": [...],
      "recommendations": [...],
      "modelVersion": "v1.2.0",
      "createdAt": "2025-12-22T10:35:00Z"
    }
  ],
  "latestPrediction": {
    // Most recent prediction object
  }
}
```

---

## Data Flow 5: Intelligence Engine Ingestion

### Overview
Real-time ingestion of new content into OpenSearch (vectors) and Neptune (graph) for the Intelligence Engine.

### Ingestion Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Content Event   │────►│ Lambda:         │────►│ Parallel Write  │
│ (SNS/API)       │     │ intel-ingest    │     │                 │
└─────────────────┘     └─────────────────┘     │ ┌─────────────┐ │
                                │               │ │ OpenSearch  │ │
                                ▼               │ │ (Vector)    │ │
                        ┌───────────────┐       │ └─────────────┘ │
                        │ Bedrock Titan │       │                 │
                        │ (Embeddings)  │       │ ┌─────────────┐ │
                        └───────────────┘       │ │ Neptune     │ │
                                                │ │ (Graph)     │ │
                                                │ └─────────────┘ │
                                                └─────────────────┘
```

### Step Details

#### Step 1: Content Event Received
```json
// Lambda Input
{
  "eventType": "CONTENT_PUBLISHED",
  "contentId": 12345,
  "clientId": 123,
  "headline": "5 Ways AI is Transforming Marketing",
  "body": "Artificial intelligence is revolutionizing...",
  "topics": ["AI", "marketing", "technology"],
  "publisherId": 456,
  "publisherName": "Marketing Weekly",
  "publishUrl": "https://marketingweekly.com/ai-marketing"
}
```

#### Step 2: Generate Embeddings
```json
// Bedrock Titan Embeddings Request
{
  "modelId": "amazon.titan-embed-text-v2:0",
  "body": {
    "inputText": "5 Ways AI is Transforming Marketing. Artificial intelligence is revolutionizing...",
    "dimensions": 1024,
    "normalize": true
  }
}

// Response
{
  "embedding": [0.023, -0.045, 0.089, ...],  // 1024 dimensions
  "inputTextTokenCount": 856
}
```

#### Step 3: Store in OpenSearch
```json
// OpenSearch Index Document
PUT /content-vectors/_doc/12345
{
  "contentId": 12345,
  "clientId": 123,
  "headline": "5 Ways AI is Transforming Marketing",
  "topics": ["AI", "marketing", "technology"],
  "publisherId": 456,
  "publisherName": "Marketing Weekly",
  "embedding": [0.023, -0.045, 0.089, ...],
  "createdAt": "2025-12-22T10:30:00Z",
  "metadata": {
    "wordCount": 1500,
    "readingTime": 6,
    "language": "en"
  }
}
```

#### Step 4: Store in Neptune (Graph)
```sparql
# Neptune Gremlin/SPARQL Insert

# Add Content Node
g.addV('Content')
  .property('contentId', 12345)
  .property('headline', '5 Ways AI is Transforming Marketing')
  .property('createdAt', '2025-12-22T10:30:00Z')

# Add Topic Nodes (if not exist) and Edges
g.V().has('Topic', 'name', 'AI').fold()
  .coalesce(unfold(), addV('Topic').property('name', 'AI'))
  .as('topic')
g.V().has('Content', 'contentId', 12345).as('content')
  .addE('ABOUT').from('content').to('topic')

# Add Client Edge
g.V().has('Content', 'contentId', 12345).as('content')
g.V().has('Client', 'clientId', 123).as('client')
  .addE('CREATED').from('client').to('content')

# Add Publisher Edge
g.V().has('Content', 'contentId', 12345).as('content')
g.V().has('Publisher', 'publisherId', 456).as('publisher')
  .addE('PUBLISHED_ON').from('content').to('publisher')
```

---

## Data Flow 6: Intelligence Engine Query

### Overview
Query flow for semantic search, graph traversal, and AI-powered insights.

### Query Types

#### Type A: Semantic Similarity Search
```json
// API Request
POST /intel/similar
{
  "contentId": 12345,  // or "text": "AI marketing strategies"
  "topK": 10,
  "filters": {
    "clientId": 123,
    "minDate": "2024-01-01"
  }
}

// OpenSearch k-NN Query
{
  "size": 10,
  "query": {
    "bool": {
      "must": [
        {
          "knn": {
            "embedding": {
              "vector": [0.023, -0.045, ...],
              "k": 10
            }
          }
        }
      ],
      "filter": [
        {"term": {"clientId": 123}},
        {"range": {"createdAt": {"gte": "2024-01-01"}}}
      ]
    }
  }
}

// Response
{
  "similar": [
    {
      "contentId": 11234,
      "headline": "AI-Powered Marketing Automation",
      "similarity": 0.94,
      "topics": ["AI", "automation", "marketing"]
    },
    {
      "contentId": 10987,
      "headline": "Machine Learning in Digital Advertising",
      "similarity": 0.89,
      "topics": ["ML", "advertising", "AI"]
    }
  ]
}
```

#### Type B: Graph Traversal Query
```json
// API Request
POST /intel/graph
{
  "query": "What content paths lead to high AI visibility for client 123?",
  "startNode": {"type": "Client", "id": 123},
  "traversalDepth": 3
}

// Neptune Gremlin Query
g.V().has('Client', 'clientId', 123)
  .out('CREATED').as('content')
  .out('ABOUT').as('topic')
  .in('ABOUT').has('visibility_score', gt(0.7))
  .path()
  .by(valueMap())
  .limit(20)

// Response
{
  "paths": [
    {
      "nodes": [
        {"type": "Client", "name": "Acme Corp"},
        {"type": "Content", "headline": "AI Marketing Guide"},
        {"type": "Topic", "name": "AI"},
        {"type": "Content", "headline": "AI Strategy 2025", "visibilityScore": 0.85}
      ],
      "edges": ["CREATED", "ABOUT", "ABOUT"]
    }
  ],
  "insights": "High-visibility content for this client tends to focus on AI and automation topics with practical guides."
}
```

#### Type C: Natural Language Insights
```json
// API Request
POST /intel/insights
{
  "question": "What content strategy should client 123 pursue based on their AI visibility patterns?",
  "context": {
    "clientId": 123,
    "timeframe": "last_90_days"
  }
}

// Internal Flow:
// 1. Query OpenSearch for client's recent content
// 2. Query Neptune for relationship patterns
// 3. Send to Bedrock for analysis

// Bedrock Analysis Request
{
  "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "messages": [
    {
      "role": "user",
      "content": "Based on this data about client 123's content performance:\n\nTop performing content:\n- AI Marketing Guide (visibility: 0.85)\n- Automation Best Practices (visibility: 0.78)\n\nTopic patterns:\n- AI-related: 85% visibility rate\n- General marketing: 45% visibility rate\n\nPublisher patterns:\n- Tech publications: 72% avg visibility\n- General news: 38% avg visibility\n\nWhat content strategy recommendations would you make?"
    }
  ]
}

// Response
{
  "insights": [
    {
      "category": "Topic Strategy",
      "recommendation": "Focus on AI and automation content which shows 2x visibility vs general marketing topics",
      "confidence": 0.92
    },
    {
      "category": "Publisher Strategy",
      "recommendation": "Prioritize tech-focused publications which yield 34 percentage points higher visibility",
      "confidence": 0.88
    },
    {
      "category": "Content Format",
      "recommendation": "Practical guides and how-to content outperform thought leadership pieces",
      "confidence": 0.85
    }
  ],
  "supportingData": {
    "contentAnalyzed": 45,
    "timeframe": "2024-09-22 to 2024-12-22",
    "avgVisibilityImprovement": "23%"
  }
}
```

---

## Database Schema Reference

### Hub Database (ARA3 SQL Server)

#### New Table: AiContentPrediction
```sql
CREATE TABLE AiContentPrediction (
    PredictionId        UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ContentId           INT NOT NULL,
    PredictionScore     DECIMAL(5,4) NOT NULL,      -- 0.0000 to 1.0000
    ConfidenceScore     DECIMAL(5,4) NOT NULL,      -- 0.0000 to 1.0000
    TopFactors          NVARCHAR(MAX) NULL,         -- JSON array
    Recommendations     NVARCHAR(MAX) NULL,         -- JSON array
    ModelVersion        VARCHAR(20) NOT NULL,
    CreatedAt           DATETIME2 DEFAULT GETUTCDATE(),

    CONSTRAINT FK_AiContentPrediction_Content
        FOREIGN KEY (ContentId) REFERENCES HubContent(ContentId),

    INDEX IX_AiContentPrediction_Content (ContentId),
    INDEX IX_AiContentPrediction_Date (CreatedAt DESC)
);
```

#### New Table: PersonaQueryResult
```sql
CREATE TABLE PersonaQueryResult (
    ResultId            UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ExecutionId         UNIQUEIDENTIFIER NOT NULL,
    PersonaId           VARCHAR(100) NOT NULL,
    ClientId            INT NOT NULL,
    QueryText           NVARCHAR(500) NOT NULL,
    Engine              VARCHAR(50) NOT NULL,       -- chatgpt, perplexity, gemini, claude
    ResponseText        NVARCHAR(MAX) NULL,
    BrandMentioned      BIT NOT NULL,
    VisibilityScore     DECIMAL(5,4) NULL,
    SentimentScore      DECIMAL(5,4) NULL,          -- -1.0000 to 1.0000
    ExecutedAt          DATETIME2 NOT NULL,
    CreatedAt           DATETIME2 DEFAULT GETUTCDATE(),

    INDEX IX_PersonaQueryResult_Execution (ExecutionId),
    INDEX IX_PersonaQueryResult_Client (ClientId, ExecutedAt DESC),
    INDEX IX_PersonaQueryResult_Persona (PersonaId, ExecutedAt DESC)
);
```

### AWS DynamoDB Tables

#### Table: brandpoint-personas
```json
{
  "TableName": "brandpoint-personas",
  "KeySchema": [
    {"AttributeName": "personaId", "KeyType": "HASH"},
    {"AttributeName": "clientId", "KeyType": "RANGE"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "personaId", "AttributeType": "S"},
    {"AttributeName": "clientId", "AttributeType": "N"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "client-index",
      "KeySchema": [
        {"AttributeName": "clientId", "KeyType": "HASH"}
      ]
    }
  ]
}
```

#### Table: brandpoint-persona-results
```json
{
  "TableName": "brandpoint-persona-results",
  "KeySchema": [
    {"AttributeName": "executionId", "KeyType": "HASH"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "executionId", "AttributeType": "S"},
    {"AttributeName": "personaId", "AttributeType": "S"},
    {"AttributeName": "executedAt", "AttributeType": "S"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "persona-date-index",
      "KeySchema": [
        {"AttributeName": "personaId", "KeyType": "HASH"},
        {"AttributeName": "executedAt", "KeyType": "RANGE"}
      ]
    }
  ]
}
```

### OpenSearch Index Schema

```json
{
  "settings": {
    "index": {
      "knn": true,
      "knn.algo_param.ef_search": 100
    }
  },
  "mappings": {
    "properties": {
      "contentId": {"type": "integer"},
      "clientId": {"type": "integer"},
      "headline": {"type": "text"},
      "body": {"type": "text"},
      "topics": {"type": "keyword"},
      "publisherId": {"type": "integer"},
      "publisherName": {"type": "keyword"},
      "embedding": {
        "type": "knn_vector",
        "dimension": 1024,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "nmslib"
        }
      },
      "createdAt": {"type": "date"},
      "metadata": {
        "type": "object",
        "properties": {
          "wordCount": {"type": "integer"},
          "readingTime": {"type": "integer"},
          "language": {"type": "keyword"}
        }
      }
    }
  }
}
```

### Neptune Graph Schema

```
Node Types:
├── Client
│   ├── clientId (INT, primary)
│   ├── clientName (STRING)
│   └── industry (STRING)
│
├── Content
│   ├── contentId (INT, primary)
│   ├── headline (STRING)
│   ├── createdAt (DATETIME)
│   └── visibilityScore (FLOAT)
│
├── Topic
│   ├── topicId (STRING, primary)
│   └── name (STRING)
│
├── Publisher
│   ├── publisherId (INT, primary)
│   ├── name (STRING)
│   └── domainAuthority (FLOAT)
│
├── Persona
│   ├── personaId (STRING, primary)
│   └── description (STRING)
│
└── Query
    ├── queryId (STRING, primary)
    └── queryText (STRING)

Edge Types:
├── CREATED (Client → Content)
├── ABOUT (Content → Topic)
├── PUBLISHED_ON (Content → Publisher)
├── TARGETS (Client → Persona)
├── GENERATED (Persona → Query)
├── MENTIONED_IN (Content → Query)
└── SIMILAR_TO (Content → Content, weight: FLOAT)
```

---

## API Contract Reference

### AWS API Gateway Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/predict/{contentId}` | POST | Run visibility prediction | API Key |
| `/predict/{contentId}` | GET | Get prediction results | API Key |
| `/persona/execute` | POST | Trigger persona agent | API Key |
| `/persona/{personaId}/results` | GET | Get persona results | API Key |
| `/personas` | GET | List all personas | API Key |
| `/personas` | POST | Create new persona | API Key |
| `/intel/similar` | POST | Semantic similarity search | API Key |
| `/intel/graph` | POST | Graph traversal query | API Key |
| `/intel/insights` | POST | Natural language insights | API Key |
| `/intel/ingest` | POST | Ingest content | API Key |
| `/health` | GET | Service health check | None |

### Hub API Endpoints (New)

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/predictions/content/{id}` | POST | Store prediction | X-Api-Key |
| `/api/predictions/content/{id}` | GET | Get predictions | X-Api-Key |
| `/api/predictions/persona/results` | POST | Store persona results | X-Api-Key |
| `/api/predictions/persona/results` | GET | Get persona results | X-Api-Key |

---

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "PREDICTION_FAILED",
    "message": "Failed to generate prediction for content 12345",
    "details": {
      "reason": "Content not found in database",
      "contentId": 12345
    },
    "requestId": "req-abc123",
    "timestamp": "2025-12-22T10:35:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description | Recovery |
|------|-------------|-------------|----------|
| `CONTENT_NOT_FOUND` | 404 | Content ID doesn't exist | Verify content ID |
| `PREDICTION_FAILED` | 500 | ML inference error | Retry with backoff |
| `RATE_LIMITED` | 429 | Too many requests | Wait and retry |
| `INVALID_INPUT` | 400 | Bad request payload | Check request format |
| `AUTH_FAILED` | 401 | Invalid API key | Check credentials |
| `EXTERNAL_API_ERROR` | 502 | External AI engine failed | Retry or skip engine |
| `PERSONA_NOT_FOUND` | 404 | Persona ID invalid | Verify persona ID |

### Retry Strategy
```python
# Exponential backoff with jitter
def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RetryableError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-22 | Jake Trippel / Claude | Initial data flow documentation |
