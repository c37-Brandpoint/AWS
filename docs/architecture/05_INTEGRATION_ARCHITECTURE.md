# Integration Architecture

## Strategic Decision

**Build a completely new AI platform using AWS cloud-native services and integrate with the legacy Hub via REST APIs.**

This document captures the architectural approach, AWS service selection, and persona-based agent system integration.

---

## The Problem

### Legacy Constraints

| Factor | Reality | Impact |
|--------|---------|--------|
| Framework | .NET 4.7.2 | Cannot run modern AI libraries |
| Testing | 0% coverage | Any change is risky |
| Services | 95% static | No DI, no mocking |
| Frontend | AngularJS 1.6.9 EOL | Security vulnerabilities |
| Documentation | None | Reverse engineering required |
| Stability | Production stable | Don't want to break it |
| Timeline | 6-8 weeks | No time for refactoring |
| Infrastructure | AWS RDS (VMs) | Legacy VM-based hosting |

### The Decision

> "The Hub is stable but fragile. Don't break what's working. Build new AI platform on AWS cloud-native services and integrate via APIs. No VMs - use serverless and managed services."

---

## AWS Cloud-Native Philosophy

### Why Cloud-Native Over VMs

| Factor | VM-Based (EC2/RDS) | Cloud-Native |
|--------|-------------------|--------------|
| Cost Model | Pay 24/7 | Pay per execution |
| Scaling | Manual or autoscale groups | Automatic, instant |
| Maintenance | OS patching, security | Managed by AWS |
| Startup Time | Minutes | Milliseconds (Lambda) |
| Estimated Cost | ~$500/month baseline | ~$150/month at moderate volume |

### Key Principle

> "Legacy runs on VMs. New AI products use native AWS services optimized for AI/ML workloads."

---

## Integration Options Evaluated

### Option 1: API Extension (Legacy Hub Changes)

Add new endpoints directly to Hub.

| Pros | Cons |
|------|------|
| Uses existing infrastructure | Must modify Hub codebase |
| Consistent authentication | Static services limit flexibility |
| Direct database access | No unit tests = risky changes |

**Verdict**: MEDIUM risk, requires Hub changes

---

### Option 2: AWS Cloud-Native + API (SELECTED)

Build new AI platform on AWS serverless services, integrate via REST APIs.

| Pros | Cons |
|------|------|
| Modern AI/ML services (Bedrock, SageMaker) | Requires stable Hub APIs |
| Serverless = no maintenance | Network latency for API calls |
| Pay per execution | Authentication complexity |
| Independent scaling | May need new Hub endpoints |
| Built-in HA and fault tolerance | |

**Verdict**: LOW risk, recommended approach

---

### Option 3: Direct Database Integration

AI products connect directly to ARA3 database.

| Pros | Cons |
|------|------|
| Fastest data access | Tight coupling to schema |
| Full data availability | Bypass business logic |
| Good for analytics/ML | Risk of data corruption |

**Verdict**: HIGH risk for writes, acceptable for reads

---

## Selected Architecture: AWS Cloud-Native

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AWS CLOUD-NATIVE PLATFORM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    PERSONA AGENT ORCHESTRATION                           ││
│  │                                                                          ││
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  ││
│  │  │ EventBridge │───►│    Step     │───►│   Lambda    │                  ││
│  │  │ (Scheduler) │    │  Functions  │    │  (Compute)  │                  ││
│  │  └─────────────┘    │(Orchestrate)│    └──────┬──────┘                  ││
│  │                     └─────────────┘           │                          ││
│  │                           │                   │                          ││
│  │  ┌────────────────────────┼───────────────────┼────────────────────────┐││
│  │  │                        ▼                   ▼                         │││
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │││
│  │  │  │  DynamoDB   │  │   Bedrock   │  │ External    │                  │││
│  │  │  │  (Persona   │  │  (Claude    │  │ LLM APIs    │                  │││
│  │  │  │   Store)    │  │   3.5)      │  │ GPT,Gemini  │                  │││
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘                  │││
│  │  │       Persona         Query           Query                          │││
│  │  │       Definitions     Generation      Execution                      │││
│  │  └──────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    AI VISIBILITY PREDICTOR                               ││
│  │                                                                          ││
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  ││
│  │  │    S3       │───►│  SageMaker  │───►│   Lambda    │                  ││
│  │  │  (Model     │    │  (Inference │    │  (Feature   │                  ││
│  │  │  Artifacts) │    │   Endpoint) │    │  Extraction)│                  ││
│  │  └─────────────┘    └─────────────┘    └─────────────┘                  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         API LAYER                                        ││
│  │                                                                          ││
│  │       ┌───────────────────────────────────────────────────┐             ││
│  │       │              API Gateway                          │             ││
│  │       │  POST /predict/{contentId}  → Run prediction      │             ││
│  │       │  GET  /predict/{contentId}  → Get prediction      │             ││
│  │       │  POST /persona/query        → Execute persona     │             ││
│  │       │  GET  /health               → Service health      │             ││
│  │       └───────────────────────┬───────────────────────────┘             ││
│  └───────────────────────────────┼─────────────────────────────────────────┘│
└──────────────────────────────────┼──────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
┌────────────────────────────┐     ┌──────────────────────────────────────────┐
│    HUB API (LEGACY)        │     │           ARA3 DATABASE                   │
│    .NET 4.7.2              │     │                                          │
│                            │     │  READ (for ML features):                 │
│  EXISTING:                 │     │  - HubContent                            │
│  GET /api/content          │     │  - AiMonitorResult                       │
│  GET /api/monitors         │     │  - Article                               │
│                            │     │                                          │
│  NEW (minimal):            │     │  WRITE (via Hub API):                    │
│  POST /api/predictions     │◄────│  - AiContentPrediction (new)             │
│  GET  /api/predictions     │     │  - PersonaQueryResult (new)              │
└────────────────────────────┘     └──────────────────────────────────────────┘
```

---

## AWS Service Selection

### Core Services

| Component | AWS Service | Purpose | Why This Service |
|-----------|-------------|---------|------------------|
| **Orchestration** | Step Functions | Persona agent workflows | Visual workflow, built-in retry, state management |
| **Compute** | Lambda | Query execution, feature extraction | Pay per invocation, auto-scale |
| **AI/LLM** | Bedrock (Claude 3.5) | Query generation from personas | Managed LLM, no infrastructure |
| **ML Models** | SageMaker Endpoints | Visibility predictor inference | Managed ML hosting, autoscale |
| **Persona Store** | DynamoDB | Persona definitions, session state | Serverless NoSQL, fast lookup |
| **Storage** | S3 | Model artifacts, results archive | Durable storage, versioning |
| **API** | API Gateway | REST endpoints for Hub integration | Managed API, throttling, auth |
| **Scheduling** | EventBridge | Scheduled persona agent runs | Cron-based triggers |
| **Secrets** | Secrets Manager | External API keys (OpenAI, Perplexity) | Secure key rotation |
| **Monitoring** | CloudWatch + X-Ray | Logs, metrics, distributed tracing | Full observability |

### Intelligence Engine Services (POC Scope - Current Data)

> **Note**: Intelligence Engine is IN POC SCOPE for processing new/current content as it's published. Historical data migration (43K articles) is future scope.

| Component | AWS Service | Purpose | POC Status |
|-----------|-------------|---------|------------|
| **Vector Store** | OpenSearch Service | Semantic search, k-NN similarity | **POC** |
| **Graph Store** | Neptune | Knowledge graph, relationships | **POC** |
| **Embeddings** | Bedrock Titan | Vector generation for content | **POC** |
| **Graph ML** | Neptune ML | Link prediction, node classification | **POC** |
| **ETL** | Glue | Data transformation, batch processing | Future (historical) |
| **Data Lake** | S3 + Athena | Historical data, ad-hoc queries | Future (historical) |

See [08_INTELLIGENCE_ENGINE_ARCHITECTURE.md](08_INTELLIGENCE_ENGINE_ARCHITECTURE.md) for full Intelligence Engine design.

### Service Architecture by Component

#### Persona Agent System

```
EventBridge (cron schedule)
    │
    ▼
Step Functions State Machine
    │
    ├── State 1: Load Persona from DynamoDB
    │       └── GetItem: personas/{personaId}
    │
    ├── State 2: Generate Queries via Bedrock
    │       └── InvokeModel: Claude 3.5 Sonnet
    │       └── Prompt: "Generate queries as {persona}"
    │
    ├── State 3: Execute Queries (Parallel Map)
    │       ├── Lambda → ChatGPT API
    │       ├── Lambda → Perplexity API
    │       ├── Lambda → Gemini API
    │       └── Lambda → Claude API
    │
    ├── State 4: Analyze Results via Bedrock
    │       └── InvokeModel: Visibility analysis
    │
    └── State 5: Store Results
            └── PutItem: DynamoDB + Hub API
```

#### Visibility Predictor

```
API Gateway
    │
    ▼
Lambda (Feature Extraction)
    │
    ├── Read content from Hub API
    ├── Extract text features
    ├── Compute derived features
    │
    ▼
SageMaker Endpoint (Inference)
    │
    ├── Run trained model
    ├── Return prediction + confidence
    │
    ▼
Lambda (Result Processing)
    │
    └── Store via Hub API → AiContentPrediction table
```

---

## Persona-Based Agent Integration

### The Problem with Generic Queries

Current AI Monitor uses generic prompts:
- "What are the benefits of military service?" → 0% visibility
- Real users don't talk like that

### The Persona Solution

Create intelligent agents that simulate actual target audience personas:

| Client | Target Persona | Generic Query (Fails) | Persona Query (Wins) |
|--------|---------------|----------------------|---------------------|
| US Army | 18-24 male, HS senior | "Benefits of military service" | "is joining the army worth it in 2025" |
| United Healthcare | 65 female, pre-Medicare | "Medicare supplement plans" | "turning 65 do i need to sign up for medicare" |
| Myrtle Beach | 45 couple, midwest | "SC vacation destinations" | "beach trip with teenagers that won't break the bank" |
| HP | 35 IT manager | "Business laptop recommendations" | "best business laptops for remote workers 2025" |

### Persona Data Model

```json
{
  "personaId": "us-army-prospect-male-18-24",
  "clientId": 123,
  "brandId": "us-army",
  "demographics": {
    "ageRange": [18, 24],
    "gender": "male",
    "education": "high_school_senior_or_recent_grad",
    "location": "suburban_midwest",
    "income": "entry_level"
  },
  "psychographics": {
    "interests": ["gaming", "sports", "career_options"],
    "concerns": ["student_debt", "job_security", "adventure"],
    "mediaConsumption": ["tiktok", "youtube", "reddit"]
  },
  "queryPatterns": {
    "speakingStyle": "casual_with_slang",
    "typicalQuestions": [
      "is X worth it",
      "what's the deal with Y",
      "how hard is Z really"
    ],
    "avoidedPatterns": ["formal_language", "industry_jargon"]
  },
  "targetQueries": [
    "is joining the army worth it in 2025",
    "army vs marines which is better",
    "what jobs in the army don't see combat"
  ]
}
```

### Query Generation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    BEDROCK (Claude 3.5)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  System Prompt:                                                  │
│  "You are simulating a {persona.demographics.ageRange} year     │
│  old {persona.demographics.gender} who                          │
│  {persona.psychographics.concerns}. Generate search queries      │
│  they would naturally type into an AI assistant.                │
│  Use {persona.queryPatterns.speakingStyle}."                    │
│                                                                  │
│  Example Output:                                                 │
│  - "is the army a good career if i hate school"                 │
│  - "do you get to pick your job in the military"                │
│  - "army signing bonus 2025 how much"                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hub Integration Points

### Minimal Hub Changes Required

Even with "don't touch Hub" approach, we need:

| Addition | Size | Risk | Purpose |
|----------|------|------|---------|
| AiPredictionController.cs | ~50 lines | LOW | Store/retrieve predictions |
| AiContentPrediction table | 1 table | LOW | Prediction storage |
| PersonaQueryResult table | 1 table | LOW | Persona query results |
| Service account + API key | Config | LOW | Gateway authentication |

### New Hub Endpoint Specification

```csharp
[Route("api/predictions")]
public class AiPredictionController : ApiController
{
    // Store prediction from AWS platform
    [HttpPost]
    [Route("content/{contentId}")]
    public IHttpActionResult StorePrediction(
        int contentId,
        [FromBody] PredictionRequest request)
    {
        // Validate auth
        // Store to AiContentPrediction table
        // Return success
    }

    // Get prediction for content
    [HttpGet]
    [Route("content/{contentId}")]
    public IHttpActionResult GetPrediction(int contentId)
    {
        // Validate auth
        // Get from AiContentPrediction table
        // Return prediction
    }

    // Store persona query results
    [HttpPost]
    [Route("persona/results")]
    public IHttpActionResult StorePersonaResults(
        [FromBody] PersonaQueryResultRequest request)
    {
        // Validate auth
        // Store to PersonaQueryResult table
        // Return success
    }
}
```

### New Database Tables

```sql
-- Visibility Predictions
CREATE TABLE AiContentPrediction (
    PredictionId        INT IDENTITY PRIMARY KEY,
    ContentId           INT NOT NULL,
    PredictionScore     DECIMAL(5,4) NOT NULL,
    ConfidenceScore     DECIMAL(5,4) NOT NULL,
    TopFactors          NVARCHAR(MAX) NULL,  -- JSON array
    PredictionType      VARCHAR(20) NOT NULL,
    ModelVersion        VARCHAR(50) NOT NULL,
    DateCreated         DATETIME2 NOT NULL,

    CONSTRAINT FK_Prediction_Content
        FOREIGN KEY (ContentId) REFERENCES HubContent(ContentId)
);

-- Persona Query Results
CREATE TABLE PersonaQueryResult (
    ResultId            INT IDENTITY PRIMARY KEY,
    PersonaId           VARCHAR(100) NOT NULL,
    ClientId            INT NOT NULL,
    QueryText           NVARCHAR(500) NOT NULL,
    AiEngine            VARCHAR(50) NOT NULL,
    ResponseText        NVARCHAR(MAX) NULL,
    BrandMentioned      BIT NOT NULL,
    VisibilityScore     DECIMAL(5,4) NULL,
    SentimentScore      DECIMAL(5,4) NULL,
    ExecutedAt          DATETIME2 NOT NULL,

    INDEX IX_PersonaResult_Client (ClientId, ExecutedAt)
);
```

---

## Authentication Strategy

### Current State

```
Hub uses:
1. Forms Authentication (session cookies)
2. X-Api-Key header (HubApiKeyService)
   - Tied to ContactId + ClientId
   - No service account concept
```

### Proposed for AWS Platform

```
1. Create "AWS AI Platform" contact in Hub
2. Generate API key for that contact
3. AWS services use X-Api-Key header
4. Works with existing infrastructure

API Gateway → Lambda → Hub API (X-Api-Key header)
```

**No OAuth, no JWT needed** - use existing pattern.

### AWS-Side Authentication

```
API Gateway
    │
    ├── API Key (for Hub callbacks)
    │
    └── IAM Roles (for internal AWS services)
        ├── Lambda execution role
        ├── Step Functions execution role
        └── SageMaker execution role

Secrets Manager
    │
    └── External API Keys
        ├── OpenAI API Key
        ├── Perplexity API Key
        ├── Google Gemini API Key
        └── Hub Service Account API Key
```

---

## Data Flow Patterns

### Read Path (No Hub Changes)

```
AWS Lambda
    │
    └──► SQL Read Replica (or direct ARA3)
            │
            ├── HubContent (content features)
            ├── Article (published content)
            ├── AiMonitorResult (training labels)
            ├── Client (segmentation)
            └── ArticleAccess (engagement)
```

### Write Path (Minimal Hub Change)

```
AWS Lambda
    │
    └──► Hub API (X-Api-Key auth)
            │
            ├──► POST /api/predictions/content/{id}
            │        └──► AiContentPrediction table
            │
            └──► POST /api/predictions/persona/results
                     └──► PersonaQueryResult table
```

### Persona Agent Execution Flow

```
EventBridge (scheduled)
    │
    ▼
Step Functions
    │
    ├─1─► DynamoDB: Load persona definition
    │
    ├─2─► Bedrock: Generate persona-specific queries
    │         └── Claude 3.5 Sonnet
    │
    ├─3─► Lambda (parallel): Execute queries
    │         ├── ChatGPT API
    │         ├── Perplexity API
    │         ├── Gemini API
    │         └── Claude API
    │
    ├─4─► Bedrock: Analyze responses for visibility
    │
    └─5─► Hub API: Store results
```

---

## Cost Model (Estimated)

### Monthly Cost at Moderate Volume

| Service | Usage Estimate | Cost |
|---------|---------------|------|
| Lambda | 100K invocations | $2 |
| Step Functions | 10K executions | $2.50 |
| Bedrock (Claude + Titan) | 1M tokens | $20 |
| SageMaker Endpoint | ml.t3.medium | $50 |
| DynamoDB | 1GB storage, moderate read/write | $5 |
| API Gateway | 100K requests | $3.50 |
| S3 | 10GB storage | $2.30 |
| Secrets Manager | 5 secrets | $2 |
| CloudWatch | Logs, metrics | $10 |
| **OpenSearch** | 2x r6g.large.search | **$200** |
| **Neptune** | db.r5.large | **$250** |
| **Total** | | **~$550/month** |

### Cost Comparison

| Approach | Monthly Cost |
|----------|-------------|
| EC2-based (VMs) | ~$300-500 |
| Cloud-Native (selected) | ~$550-600 |
| **Note** | Includes Intelligence Engine |

---

## Risk Mitigation

### Risk: Hub API changes break integration

**Mitigation**:
- Version API contracts
- Integration tests
- Monitor for breaking changes

### Risk: Cold start latency

**Mitigation**:
- Provisioned concurrency for critical Lambdas
- Warm-up requests
- SageMaker always-on endpoint

### Risk: External API rate limits

**Mitigation**:
- Implement backoff/retry in Step Functions
- Queue requests during high volume
- Monitor usage against limits

### Risk: Cost overrun

**Mitigation**:
- AWS Budgets with alerts
- Usage caps in API Gateway
- Monitor CloudWatch billing metrics

---

## Success Criteria

### Architecture Goals

| Goal | Metric | Target |
|------|--------|--------|
| Hub stability | Production incidents | Zero increase |
| Platform reliability | Step Functions success rate | >99% |
| Integration latency | API response time | <500ms P95 |
| Cost efficiency | Monthly AWS bill | <$600 |
| Deployment independence | Release coupling | None |

### POC Deliverables

1. Working AWS cloud-native platform
2. Persona agent system (Step Functions)
3. Visibility predictor (SageMaker)
4. Hub integration (minimal)
5. **Intelligence Engine - current data (OpenSearch + Neptune)**
6. **Real-time content ingestion pipeline**
7. Demo interface
8. Documentation

### Future Deliverables (Post-POC)

1. Historical data migration pipeline (43K articles)
2. Batch vectorization of 30+ years of content
3. Full graph population from historical relationships
4. Advanced ML-driven content recommendations
5. Natural language insights interface (enhanced)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-22 | Jake Trippel / Claude | Initial architecture |
| 2.0 | 2025-12-22 | Jake Trippel / Claude | AWS cloud-native architecture, persona agent system |
| 2.1 | 2025-12-22 | Jake Trippel / Claude | Added Intelligence Engine services (OpenSearch, Neptune) |
| 3.0 | 2025-12-22 | Jake Trippel / Claude | Intelligence Engine in POC scope (current data only) |
