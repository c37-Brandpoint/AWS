# Persona Agent Architecture

## The Big Idea

Instead of using generic prompts to measure AI visibility, we create **intelligent agents that simulate real target audience personas**. These agents query AI engines the way actual customers would, generating dramatically more realistic and actionable visibility data.

---

## Why Personas Matter

### The Problem with Generic Prompts

Current AI Monitor uses queries like:
- "What is a mat release?"
- "How do I get branded content in publications?"
- "What are the benefits of military service?"

**Result**: 0% visibility. Real people don't talk like this.

### The Persona Solution

For US Army targeting 18-24 year old males:
- "is joining the army worth it in 2025"
- "what's army basic training actually like"
- "army vs marines which is better for someone who wants to travel"

**Result**: Queries that match how REAL prospects actually ask questions.

---

## Persona Examples by Client

| Client | Target Persona | Generic Query (Fails) | Persona Query (Wins) |
|--------|---------------|----------------------|---------------------|
| **US Army** | 18-24 male, HS senior, considering alternatives to college | "What are the benefits of joining the military?" | "is the army a good career if i don't want college debt" |
| **United Healthcare** | 65 female, approaching Medicare eligibility | "What Medicare supplement plans are available?" | "turning 65 next month do i need to sign up for medicare" |
| **Myrtle Beach** | 45 couple, midwest, family vacation planning | "Family vacation destinations in South Carolina" | "beach trip with teenagers that won't break the bank" |
| **HP** | 35 IT manager, enterprise laptop procurement | "Enterprise laptop comparison for business" | "best business laptops for remote workers 2025" |
| **Whoop** | 28 male, fitness enthusiast, data-driven | "Fitness tracker comparison" | "whoop vs oura vs apple watch for serious athletes" |
| **GoodRx** | 55 female, managing prescriptions, cost-conscious | "How to save money on prescriptions" | "why is my medication so expensive even with insurance" |

---

## Persona Data Model

```json
{
  "personaId": "us-army-prospect-male-18-24",
  "clientId": 123,
  "brandId": 456,
  "name": "Young Military Prospect",
  "description": "High school senior or recent grad considering military as alternative to college",

  "demographics": {
    "ageRange": [18, 24],
    "gender": "male",
    "education": "high_school_senior_or_recent_grad",
    "location": "suburban_midwest",
    "income": "entry_level_or_none",
    "occupation": "student_or_service_job"
  },

  "psychographics": {
    "concerns": [
      "student_debt",
      "unclear_career_path",
      "desire_for_independence",
      "adventure_seeking",
      "wanting_to_prove_themselves"
    ],
    "motivations": [
      "financial_stability",
      "skills_training",
      "travel_opportunities",
      "sense_of_purpose",
      "physical_challenge"
    ],
    "fears": [
      "being_stuck",
      "deployment_danger",
      "losing_freedom",
      "drill_sergeants"
    ],
    "mediaHabits": ["tiktok", "youtube", "reddit", "instagram", "gaming"],
    "informationStyle": "informal_direct_visual"
  },

  "queryPatterns": {
    "speakingStyle": "casual_with_slang",
    "typicalFormats": [
      "is X worth it",
      "what's it actually like to",
      "X vs Y which is better",
      "can i still X if i join",
      "do you really have to",
      "reddit says X is that true"
    ],
    "avoidPatterns": [
      "formal_business_speak",
      "military_jargon",
      "recruiter_language",
      "complete_sentences"
    ],
    "typosAndInformal": true
  },

  "topicFocus": [
    "military_career_benefits",
    "basic_training_experience",
    "education_benefits_gi_bill",
    "deployment_reality",
    "branch_comparisons",
    "daily_life_in_military",
    "signing_bonus_reality",
    "can_i_choose_my_job"
  ],

  "brandContext": {
    "brandName": "U.S. Army",
    "competitors": ["Marines", "Navy", "Air Force", "Space Force", "Coast Guard"],
    "keyMessages": ["Be All You Can Be", "Army Strong"],
    "uniqueValue": ["largest branch", "most job options", "army reserve flexibility"]
  }
}
```

---

## Agent Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PERSONA AGENT PLATFORM                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    PERSONA STORE (DynamoDB)                       │   │
│  │                                                                   │   │
│  │  Stores persona definitions for each client/brand combination    │   │
│  │  - Demographics, psychographics, query patterns                  │   │
│  │  - Topic focus areas, brand context                              │   │
│  │  - Speaking style, avoid patterns                                │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  QUERY GENERATOR AGENT (Bedrock/Claude)           │   │
│  │                                                                   │   │
│  │  LLM-powered query generation that:                              │   │
│  │  - Takes persona definition as input                             │   │
│  │  - Generates realistic, natural-language queries                 │   │
│  │  - Matches persona's speaking style and concerns                 │   │
│  │  - Avoids corporate/formal language                              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                 MULTI-ENGINE EXECUTOR (Lambda)                    │   │
│  │                                                                   │   │
│  │  Executes generated queries across all AI engines:               │   │
│  │  - ChatGPT (OpenAI API)                                          │   │
│  │  - Perplexity (Perplexity API)                                   │   │
│  │  - Google Gemini (Gemini API)                                    │   │
│  │  - Microsoft Copilot (Bing API)                                  │   │
│  │  - Claude (Anthropic API) - for competitive analysis             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                 RESPONSE ANALYZER (Lambda + Bedrock)              │   │
│  │                                                                   │   │
│  │  Analyzes AI responses for:                                      │   │
│  │  - Brand visibility (target mentioned?)                          │   │
│  │  - Competitor visibility (anti-targets mentioned?)               │   │
│  │  - Sentiment analysis (positive/negative context)                │   │
│  │  - Citation extraction (sources referenced)                      │   │
│  │  - Position analysis (where in response?)                        │   │
│  │  - Recommendation context (recommended or just mentioned?)       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    RESULTS STORE (S3 + RDS)                       │   │
│  │                                                                   │   │
│  │  Persists results with full context:                             │   │
│  │  - Persona used, query generated, engine queried                 │   │
│  │  - Full response text, visibility flags                          │   │
│  │  - Sentiment scores, citations extracted                         │   │
│  │  - Timestamp, model versions                                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Query Generation Process

### Step 1: Load Persona

```python
persona = dynamodb.get_item(
    TableName='Personas',
    Key={'personaId': 'us-army-prospect-male-18-24'}
)
```

### Step 2: Build Generation Prompt

```python
prompt = f"""
You are simulating a real person with these characteristics:
- Age: {persona['demographics']['ageRange']}
- Gender: {persona['demographics']['gender']}
- Education: {persona['demographics']['education']}
- Main concerns: {persona['psychographics']['concerns']}
- Speaking style: {persona['queryPatterns']['speakingStyle']}

Generate 10 realistic questions this person would type into an AI chatbot
about {persona['topicFocus']}.

IMPORTANT RULES:
1. Use {persona['queryPatterns']['speakingStyle']} language
2. Match their typical question formats: {persona['queryPatterns']['typicalFormats']}
3. DO NOT use: {persona['queryPatterns']['avoidPatterns']}
4. Include natural typos and informal language if appropriate
5. Questions should reflect their genuine concerns and motivations
6. Do NOT include the brand name "{persona['brandContext']['brandName']}" in most queries

Return as JSON array of strings.
"""
```

### Step 3: Call Bedrock (Claude 3.5)

```python
response = bedrock.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 1024,
        'messages': [{'role': 'user', 'content': prompt}]
    })
)
```

### Step 4: Parse Generated Queries

```json
[
  "is the army worth it if i hate school",
  "do you actually get free college after army",
  "what's basic training really like reddit says it sucks",
  "army vs air force which has better life",
  "can i pick where i get stationed in the army",
  "how long do you have to serve minimum",
  "do army recruiters lie about everything",
  "what jobs in the army don't see combat",
  "can i bring my phone to basic training",
  "is army reserve worth it or just go active"
]
```

### Step 5: Execute Against AI Engines

```python
for query in generated_queries:
    # ChatGPT
    chatgpt_response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": query}]
    )

    # Perplexity
    perplexity_response = perplexity.chat.completions.create(
        model="llama-3.1-sonar-large-128k-online",
        messages=[{"role": "user", "content": query}]
    )

    # Gemini
    gemini_response = genai.GenerativeModel('gemini-pro').generate_content(query)

    # Analyze each response
    analyze_response(query, chatgpt_response, 'chatgpt', persona)
    analyze_response(query, perplexity_response, 'perplexity', persona)
    analyze_response(query, gemini_response, 'gemini', persona)
```

---

## AWS Architecture

### Service Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AWS CLOUD-NATIVE ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ORCHESTRATION                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    AWS Step Functions                             │   │
│  │                                                                   │   │
│  │   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐        │   │
│  │   │  Load   │──▶│Generate │──▶│ Execute │──▶│ Analyze │        │   │
│  │   │Personas │   │ Queries │   │ Queries │   │ Results │        │   │
│  │   └─────────┘   └─────────┘   └─────────┘   └─────────┘        │   │
│  │        │             │             │             │              │   │
│  │        ▼             ▼             ▼             ▼              │   │
│  │   DynamoDB      Bedrock       Lambda x N     Lambda +          │   │
│  │                 Claude                       Bedrock           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  COMPUTE                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  AWS Lambda    │  │  AWS Lambda    │  │  ECS Fargate   │            │
│  │                │  │                │  │                │            │
│  │  - Query gen   │  │  - API calls   │  │  - ML model    │            │
│  │  - Response    │  │  - ChatGPT     │  │    inference   │            │
│  │    parsing     │  │  - Perplexity  │  │  - Long-run    │            │
│  │  - Analysis    │  │  - Gemini      │  │    tasks       │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                          │
│  AI/ML SERVICES                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │ Amazon Bedrock │  │   SageMaker    │  │ External APIs  │            │
│  │                │  │                │  │                │            │
│  │ - Claude 3.5   │  │ - Visibility   │  │ - OpenAI       │            │
│  │ - Query gen    │  │   predictor    │  │ - Perplexity   │            │
│  │ - Response     │  │ - Custom ML    │  │ - Gemini       │            │
│  │   analysis     │  │   models       │  │ - Copilot      │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                          │
│  DATA STORES                                                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │    DynamoDB    │  │    Amazon S3   │  │   Amazon RDS   │            │
│  │                │  │                │  │   (existing)   │            │
│  │ - Personas     │  │ - Model files  │  │                │            │
│  │ - Query cache  │  │ - Training     │  │ - ARA3 DB      │            │
│  │ - Sessions     │  │ - Results      │  │ - Hub data     │            │
│  │ - Config       │  │ - Archives     │  │ - Integration  │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                          │
│  INTEGRATION & SCHEDULING                                                │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  API Gateway   │  │  EventBridge   │  │    Secrets     │            │
│  │                │  │                │  │    Manager     │            │
│  │ - REST APIs    │  │ - Scheduled    │  │                │            │
│  │ - Hub calls    │  │   runs         │  │ - API keys     │            │
│  │ - Auth/throttle│  │ - Event-driven │  │ - Credentials  │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                          │
│  MONITORING                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │   CloudWatch   │  │     X-Ray      │  │ Cost Explorer  │            │
│  │                │  │                │  │                │            │
│  │ - Logs         │  │ - Tracing      │  │ - API costs    │            │
│  │ - Metrics      │  │ - Latency      │  │ - Budget       │            │
│  │ - Alarms       │  │ - Debug        │  │   alerts       │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Service Selection Rationale

| Service | Purpose | Why This Choice |
|---------|---------|-----------------|
| **Step Functions** | Agent workflow orchestration | Visual workflows, built-in error handling, parallel execution |
| **Lambda** | Query execution, response parsing | Serverless, pay-per-use, auto-scales, 15-min max sufficient |
| **Bedrock (Claude)** | Query generation, response analysis | Managed LLMs, no infrastructure, Claude excels at personas |
| **DynamoDB** | Persona storage, session state | Serverless, fast reads, scales automatically |
| **S3** | Model artifacts, result archives | Cheap storage, integrates with SageMaker |
| **SageMaker** | Visibility predictor model | Managed ML, easy deployment, A/B testing |
| **API Gateway** | Hub integration, external APIs | Managed REST, auth, throttling, monitoring |
| **EventBridge** | Scheduled execution | Cron scheduling, event-driven triggers |
| **Secrets Manager** | API key storage | Secure, rotatable, auditable |

### Why NOT EC2/VMs?

| VM Approach | Cloud-Native Approach |
|-------------|----------------------|
| Pay 24/7 for idle capacity | Pay only when executing |
| Manual scaling configuration | Automatic scaling |
| OS patching and maintenance | Fully managed |
| Fixed compute capacity | Elastic to demand |
| ~$500/month minimum | ~$50-100/month at low volume |

---

## Data Flow

### Complete Agent Execution Flow

```
EventBridge (Scheduler)
    │
    │  Trigger: "Run US Army persona queries"
    ▼
Step Functions (Orchestrator)
    │
    ├─► Step 1: Load Persona
    │       │
    │       └─► DynamoDB.get_item('us-army-prospect-male-18-24')
    │               │
    │               ▼
    │           Persona Definition JSON
    │
    ├─► Step 2: Generate Queries
    │       │
    │       └─► Bedrock (Claude 3.5)
    │               │
    │               ▼
    │           10 Realistic Queries
    │
    ├─► Step 3: Execute Queries (Parallel)
    │       │
    │       ├─► Lambda: Call ChatGPT ──► Response 1
    │       ├─► Lambda: Call Perplexity ──► Response 2
    │       └─► Lambda: Call Gemini ──► Response 3
    │               │
    │               ▼
    │           30 Total Responses (10 queries x 3 engines)
    │
    ├─► Step 4: Analyze Responses
    │       │
    │       └─► Lambda + Bedrock
    │               │
    │               ▼
    │           Visibility Analysis
    │           - Brand mentioned: true/false
    │           - Competitor mentioned: true/false
    │           - Sentiment: positive/negative/neutral
    │           - Citations: [list of sources]
    │           - Position: first/middle/last/not_present
    │
    └─► Step 5: Store Results
            │
            ├─► S3: Full response archive
            └─► RDS (ARA3): Structured results for Hub
```

---

## Enhanced Result Model

### AiMonitorResult (Extended)

```sql
-- Existing fields
AiMonitorResultId           INT
AiMonitorResultQueryId      INT
AiMonitorResultEngineId     INT
AiMonitorResultText         NVARCHAR(MAX)
AiMonitorResultTargetPresent BOOL
AiMonitorResultWebSearch    BOOL

-- NEW: Persona fields
AiMonitorResultPersonaId    VARCHAR(100)    -- Links to persona used
AiMonitorResultQueryGenerated VARCHAR(500)  -- The actual query sent
AiMonitorResultQueryType    VARCHAR(50)     -- 'persona_generated' vs 'static'

-- NEW: Enhanced analysis fields
AiMonitorResultPosition     VARCHAR(20)     -- 'first', 'middle', 'last', 'absent'
AiMonitorResultCitationCount INT            -- Number of sources cited
AiMonitorResultRecommended  BOOL            -- Was brand recommended (not just mentioned)
AiMonitorResultContext      VARCHAR(50)     -- 'positive', 'negative', 'neutral', 'comparative'
```

### Persona Execution Log

```sql
CREATE TABLE AiPersonaExecution (
    ExecutionId         BIGINT IDENTITY PRIMARY KEY,
    PersonaId           VARCHAR(100) NOT NULL,
    ClientId            INT NOT NULL,
    ExecutionStartTime  DATETIME2 NOT NULL,
    ExecutionEndTime    DATETIME2,
    QueriesGenerated    INT,
    QueriesExecuted     INT,
    EnginesQueried      INT,
    TotalResponses      INT,
    VisibilityRate      DECIMAL(5,4),       -- % of responses with brand
    StepFunctionArn     VARCHAR(500),
    Status              VARCHAR(20),         -- 'running', 'completed', 'failed'
    ErrorMessage        NVARCHAR(MAX)
);
```

---

## API Endpoints

### Persona Management

```
POST   /api/personas                    Create new persona
GET    /api/personas                    List all personas for client
GET    /api/personas/{id}               Get persona details
PUT    /api/personas/{id}               Update persona
DELETE /api/personas/{id}               Delete persona
POST   /api/personas/{id}/generate      Generate sample queries (preview)
```

### Execution

```
POST   /api/executions                  Start persona execution
GET    /api/executions/{id}             Get execution status
GET    /api/executions/{id}/results     Get execution results
POST   /api/executions/schedule         Schedule recurring execution
DELETE /api/executions/schedule/{id}    Cancel scheduled execution
```

### Results

```
GET    /api/results/persona/{id}        Results by persona
GET    /api/results/client/{id}         Results by client
GET    /api/results/visibility          Visibility summary
GET    /api/results/trends              Visibility trends over time
```

### Predictions

```
POST   /api/predict                     Run visibility prediction
GET    /api/predict/content/{id}        Get prediction for content
POST   /api/predict/persona/{id}        Predict with persona context
```

---

## Cost Model

### Monthly Estimate (Moderate Usage)

| Service | Usage | Cost |
|---------|-------|------|
| **Lambda** | 2M invocations, 256MB, 10s avg | ~$40 |
| **Step Functions** | 200K state transitions | ~$50 |
| **Bedrock (Claude 3.5)** | 5M input + 2M output tokens | ~$100 |
| **DynamoDB** | 20GB, 2M reads/writes | ~$25 |
| **S3** | 200GB storage + requests | ~$10 |
| **API Gateway** | 2M requests | ~$8 |
| **SageMaker** | ml.t3.medium endpoint | ~$50 |
| **Secrets Manager** | 15 secrets | ~$6 |
| **CloudWatch** | Logs + metrics | ~$30 |
| **EventBridge** | 10K scheduled events | ~$1 |
| **Subtotal AWS** | | **~$320** |
| | | |
| **External APIs** | | |
| OpenAI (GPT-4o) | 2M tokens | ~$200 |
| Perplexity | 2M tokens | ~$150 |
| Gemini | 2M tokens | ~$100 |
| **Subtotal External** | | **~$450** |
| | | |
| **TOTAL** | | **~$770/month** |

### Cost Scaling

| Query Volume | AWS Cost | API Cost | Total |
|--------------|----------|----------|-------|
| 10K queries/month | ~$150 | ~$100 | ~$250 |
| 50K queries/month | ~$320 | ~$450 | ~$770 |
| 200K queries/month | ~$600 | ~$1,800 | ~$2,400 |
| 500K queries/month | ~$1,000 | ~$4,500 | ~$5,500 |

---

## Security Considerations

### API Key Management

```
Secrets Manager
├── openai-api-key
├── perplexity-api-key
├── gemini-api-key
├── anthropic-api-key (for Claude direct if needed)
└── hub-service-account-key
```

### IAM Roles

```
PersonaAgentExecutionRole
├── Lambda: Invoke
├── Bedrock: InvokeModel
├── DynamoDB: Read/Write (Personas table)
├── S3: Read/Write (results bucket)
├── Secrets Manager: GetSecretValue
├── Step Functions: StartExecution
└── CloudWatch: PutMetrics, PutLogs
```

### Network Security

- API Gateway with throttling and API keys
- VPC endpoints for AWS services
- No public internet access from Lambda (use NAT for external APIs)
- Encryption at rest (S3, DynamoDB, RDS)
- Encryption in transit (TLS everywhere)

---

## Implementation Phases

### Phase 1: Foundation
- DynamoDB table for personas
- Basic persona CRUD API
- Step Functions skeleton

### Phase 2: Query Generation
- Bedrock integration
- Query generation prompts
- Sample persona testing

### Phase 3: Multi-Engine Execution
- Lambda functions for each engine
- Parallel execution in Step Functions
- Error handling and retries

### Phase 4: Response Analysis
- Visibility detection
- Sentiment analysis
- Citation extraction

### Phase 5: Integration
- Hub API integration
- Results persistence
- Reporting endpoints

### Phase 6: Prediction
- Feature engineering with persona context
- Model training with persona features
- Prediction API

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Query realism | >80% human-like | Turing-style evaluation |
| Persona coverage | 3+ personas per client | Configuration audit |
| Engine coverage | 4+ engines | Execution logs |
| Visibility accuracy | >90% detection | Manual validation sample |
| Execution reliability | >99% success | Step Functions metrics |
| Latency | <5 min full execution | CloudWatch metrics |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-22 | Jake Trippel / Claude | Initial persona architecture |
