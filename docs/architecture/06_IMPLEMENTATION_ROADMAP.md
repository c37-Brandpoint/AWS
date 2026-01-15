# Implementation Roadmap

## Overview

6-8 week POC to build the complete Brandpoint AI Platform on AWS cloud-native infrastructure, integrated with the legacy Hub.

### POC Scope

| Component | Description | Data Scope |
|-----------|-------------|------------|
| AI Visibility Predictor | ML model predicting AI search visibility | All |
| Persona Agent System | Simulate real users querying AI engines | All |
| Intelligence Engine | Vector + Graph knowledge platform | **Current data only** |

**Historical Data Migration**: Post-POC (backfill 43K articles)

---

## Architecture Summary

```
AWS Cloud-Native Platform
├── Persona Agent System (Step Functions + Bedrock)
├── Visibility Predictor (SageMaker)
├── Intelligence Engine (OpenSearch + Neptune) ← NEW IN POC
└── API Layer (API Gateway + Lambda)
         │
         ▼
    Legacy Hub (.NET 4.7.2)
```

---

## Phase 0: Foundation (Week 1)

### Objectives

- AWS infrastructure provisioning
- Hub access confirmation
- Project scaffolding

### Tasks

| Task | Owner | Dependency | Status |
|------|-------|------------|--------|
| Provision AWS account/VPC | Codename 37 | AWS access | Pending |
| Create DynamoDB tables | Codename 37 | VPC | Pending |
| **Deploy OpenSearch cluster** | Codename 37 | VPC | Pending |
| **Deploy Neptune cluster** | Codename 37 | VPC | Pending |
| Configure Secrets Manager | Codename 37 | VPC | Pending |
| Set up CloudWatch dashboards | Codename 37 | VPC | Pending |
| Obtain Brandpoint staging access | Brandpoint | None | Pending |
| Create service account in Hub | Brandpoint | Staging access | Pending |
| Generate API key for service account | Brandpoint | Service account | Pending |
| Database read access confirmation | Brandpoint | None | Pending |

### AWS Infrastructure Setup

```
Terraform/CloudFormation:
├── VPC + Security Groups
├── DynamoDB Tables
│   ├── personas (persona definitions)
│   └── query_results (execution history)
├── OpenSearch Service (Intelligence Engine)
│   └── brandpoint-content-vectors (k-NN index)
├── Neptune (Intelligence Engine)
│   └── Knowledge graph cluster
├── S3 Buckets
│   ├── model-artifacts
│   └── results-archive
├── Secrets Manager
│   ├── openai-api-key
│   ├── perplexity-api-key
│   ├── gemini-api-key
│   └── hub-service-account-key
├── IAM Roles
│   ├── lambda-execution-role
│   ├── step-functions-role
│   └── sagemaker-role
└── CloudWatch Log Groups
```

### Deliverables

- [ ] AWS infrastructure provisioned (IaC)
- [ ] **OpenSearch cluster deployed with k-NN index**
- [ ] **Neptune cluster deployed with graph schema**
- [ ] Service account authenticated with Hub
- [ ] Database read access confirmed
- [ ] CI/CD pipeline configured

---

## Phase 1: Data Pipeline & Persona Foundation (Week 2)

### Objectives

- Build feature extraction pipeline
- Create training dataset
- Establish persona data model
- Seed initial personas

### Tasks

| Task | Description | Priority |
|------|-------------|----------|
| Connect to ARA3 database | Read access for ML features | P0 |
| Extract AiMonitorResult labels | 49K records with visibility labels | P0 |
| Join HubContent features | Content text, metadata | P0 |
| Join Article features | Published content characteristics | P1 |
| Create train/test split | 80/20 stratified | P0 |
| Define persona data model | DynamoDB schema | P0 |
| Create initial personas | 3-4 client personas | P0 |
| Build Lambda feature extractor | Content → features | P0 |

### Persona Creation

| Client | Persona ID | Target Demographics |
|--------|------------|---------------------|
| US Army | us-army-prospect-male-18-24 | 18-24 male, HS senior |
| United Healthcare | uhc-medicare-female-65 | 65 female, pre-Medicare |
| Myrtle Beach | myrtle-family-midwest-45 | 45 couple, midwest |
| HP | hp-it-manager-35 | 35 IT manager |

### Feature Engineering

```
Content Features:
├── headline_text (string)
├── body_text (string)
├── content_length (int)
├── word_count (int)
├── readability_score (float)
├── has_numbers (bool)
├── has_questions (bool)
└── entity_density (float)

Query Features:
├── query_text (string)
├── query_type (categorical)
├── brand_in_query (bool)
├── location_query (bool)
├── comparison_query (bool)
└── how_to_query (bool)

Publisher Features:
├── publisher_domain (string)
├── domain_authority (float) - external
├── ai_crawlable (bool) - robots.txt check
└── historical_visibility (float)

Persona Features:
├── persona_id (string)
├── demographic_match (float)
├── query_style (categorical)
└── speaking_formality (float)
```

### Deliverables

- [ ] Feature extraction Lambda deployed
- [ ] Training dataset (CSV/Parquet) in S3
- [ ] Data quality report
- [ ] 4 initial personas seeded in DynamoDB
- [ ] Persona data model documented

---

## Phase 2: Model Development (Weeks 3-4)

### Objectives

- Train baseline models
- Develop transformer classifier
- Achieve ≥65% accuracy target
- Deploy model to SageMaker

### Model Progression

| Stage | Model | Expected Accuracy |
|-------|-------|-------------------|
| Baseline 1 | Logistic Regression | ~40% |
| Baseline 2 | Random Forest | ~50% |
| Baseline 3 | XGBoost | ~55% |
| Target | Transformer (fine-tuned) | ≥65% |

### Tasks

| Task | Description | Priority |
|------|-------------|----------|
| Train logistic regression | Baseline model | P0 |
| Train random forest | Feature importance | P0 |
| Train XGBoost | Gradient boosting baseline | P1 |
| Fine-tune transformer | DistilBERT or similar | P0 |
| Hyperparameter tuning | Optuna/GridSearch | P1 |
| Cross-validation | 5-fold stratified | P0 |
| Deploy to SageMaker | Inference endpoint | P0 |
| Test endpoint latency | <200ms P95 | P0 |

### SageMaker Deployment

```
Model Artifacts (S3):
├── model.tar.gz
│   ├── model_weights.bin
│   ├── config.json
│   └── tokenizer/
└── inference.py

Endpoint Configuration:
├── Instance: ml.t3.medium (POC)
├── Autoscaling: min=1, max=2
└── Timeout: 30 seconds
```

### Evaluation Metrics

```
Primary:
├── Accuracy (target: ≥65%)
├── Lift over baseline (target: ≥15 points)
└── 95% confidence interval

Secondary:
├── Precision (visible class)
├── Recall (visible class)
├── F1 Score
├── AUC-ROC
└── Brier Score (calibration)
```

### Deliverables

- [ ] Trained model artifacts in S3
- [ ] SageMaker endpoint deployed
- [ ] Model evaluation report
- [ ] Accuracy >= 65% demonstrated
- [ ] Lift >= 15 points demonstrated

---

## Phase 3: Persona Agents + Intelligence Engine (Week 5)

### Objectives

- Build Step Functions workflow for personas
- Implement query generation with Bedrock
- Execute queries across AI engines
- **Build real-time content ingestion pipeline (Vector + Graph)**
- Analyze and store results

### Step Functions Workflow

```
PersonaAgentExecution (State Machine)
│
├── State 1: LoadPersona
│   ├── Type: Task
│   ├── Resource: DynamoDB GetItem
│   └── Output: persona definition JSON
│
├── State 2: GenerateQueries
│   ├── Type: Task
│   ├── Resource: Lambda (invokes Bedrock)
│   ├── Input: persona definition
│   └── Output: 5-10 persona-style queries
│
├── State 3: ExecuteQueries
│   ├── Type: Map (parallel)
│   ├── Iterator: ExecuteSingleQuery
│   │   ├── Lambda: ChatGPT API
│   │   ├── Lambda: Perplexity API
│   │   ├── Lambda: Gemini API
│   │   └── Lambda: Claude API
│   └── Output: array of AI responses
│
├── State 4: AnalyzeVisibility
│   ├── Type: Task
│   ├── Resource: Lambda (invokes Bedrock)
│   ├── Input: responses + brand context
│   └── Output: visibility scores, mentions
│
└── State 5: StoreResults
    ├── Type: Parallel
    ├── Branches:
    │   ├── DynamoDB PutItem (results)
    │   └── Lambda → Hub API (sync results)
    └── Output: success confirmation
```

### Tasks

| Task | Description | Priority |
|------|-------------|----------|
| Create Step Functions state machine | Main orchestration | P0 |
| Build LoadPersona Lambda | DynamoDB integration | P0 |
| Build GenerateQueries Lambda | Bedrock Claude integration | P0 |
| Build ExecuteQuery Lambdas | External API calls | P0 |
| Build AnalyzeVisibility Lambda | Response analysis | P0 |
| Build StoreResults Lambda | Hub API integration | P0 |
| Configure EventBridge schedule | Daily/weekly triggers | P1 |
| Implement error handling | Retry logic, dead letter | P1 |
| **Build ContentIngestion Lambda** | Content → Bedrock Titan → Vector | P0 |
| **Build GraphUpdate Lambda** | Content → Entity extraction → Neptune | P0 |
| **Configure publish event trigger** | EventBridge on Hub content publish | P0 |
| **Test real-time ingestion** | End-to-end vector + graph | P0 |

### Bedrock Query Generation Prompt

```
System Prompt:
"You are simulating a {age}-year-old {gender} who is interested in
{interests} and concerned about {concerns}. Generate 5 natural search
queries they would type into an AI assistant about {topic}.

Speaking style: {speakingStyle}
Avoid: {avoidedPatterns}

Output only the queries, one per line, no numbering or explanation."

Example Output:
- is joining the army worth it in 2025
- army vs marines which is better for tech jobs
- what jobs in the army don't see combat
- do you get to pick where you're stationed army
- army signing bonus how much 2025
```

### Deliverables

- [ ] Step Functions state machine deployed
- [ ] All Lambda functions tested
- [ ] Query generation working with Bedrock
- [ ] Multi-engine query execution working
- [ ] Results stored in DynamoDB
- [ ] EventBridge schedule configured
- [ ] **Real-time content ingestion working**
- [ ] **New content vectorized in OpenSearch**
- [ ] **New content graphed in Neptune**

---

## Phase 4: API Layer & Hub Integration + Intelligence APIs (Week 6)

### Objectives

- Deploy API Gateway endpoints
- Add minimal Hub changes
- Connect persona results to Hub
- Enable prediction display
- **Deploy Intelligence Engine APIs (similarity, graph, insights)**

### API Gateway Endpoints

```
API Gateway (REST API)
│
├── POST /predict/{contentId}
│   └── Lambda → SageMaker → Hub API
│
├── GET /predict/{contentId}
│   └── Lambda → DynamoDB/Hub API
│
├── POST /persona/{personaId}/execute
│   └── Step Functions StartExecution
│
├── GET /persona/{personaId}/results
│   └── Lambda → DynamoDB
│
├── POST /intel/similarity
│   └── Lambda → OpenSearch k-NN → Similar content
│
├── GET /intel/graph/{entityId}
│   └── Lambda → Neptune → Related entities
│
├── POST /intel/insights
│   └── Lambda → Bedrock → Natural language insights
│
└── GET /health
    └── Lambda → Health check
```

### Hub Changes (Minimal)

```
New Files (~100 lines total):
├── Api/AiPredictionController.cs (~50 lines)
├── Models/PredictionRequest.cs (~15 lines)
└── Models/PersonaResultRequest.cs (~15 lines)

Database Tables:
├── AiContentPrediction
└── PersonaQueryResult

Config:
└── AWS API Gateway URL in AppSettings
```

### Tasks

| Task | Description | Priority |
|------|-------------|----------|
| Create API Gateway REST API | Main API | P0 |
| Implement prediction endpoints | /predict/* | P0 |
| Implement persona endpoints | /persona/* | P0 |
| **Implement similarity endpoint** | /intel/similarity | P0 |
| **Implement graph endpoint** | /intel/graph/* | P0 |
| **Implement insights endpoint** | /intel/insights | P1 |
| Create AiContentPrediction table | Database migration | P0 |
| Create PersonaQueryResult table | Database migration | P0 |
| Add AiPredictionController | Hub API endpoints | P0 |
| Configure API Gateway auth | API keys | P0 |
| Test end-to-end flow | Hub → AWS → Hub | P0 |
| **Test similarity search** | Vector k-NN retrieval | P0 |
| **Test graph traversal** | Neptune Gremlin queries | P0 |

### API Contract

```
POST /predict/{contentId}
Response:
{
    "predictionId": "pred_123",
    "contentId": 456,
    "predictionScore": 0.72,
    "confidenceScore": 0.85,
    "topFactors": [
        {"name": "query_type", "impact": 0.35, "value": "brand_specific"},
        {"name": "web_search", "impact": 0.28, "value": true},
        {"name": "publisher_crawlable", "impact": 0.15, "value": true}
    ],
    "modelVersion": "v1.0.0"
}

GET /persona/{personaId}/results
Response:
{
    "personaId": "us-army-prospect-male-18-24",
    "results": [
        {
            "queryText": "is joining the army worth it 2025",
            "engine": "chatgpt",
            "brandMentioned": true,
            "visibilityScore": 0.65,
            "executedAt": "2025-12-22T10:30:00Z"
        }
    ],
    "aggregateVisibility": 0.42,
    "totalQueries": 20
}
```

### Deliverables

- [ ] API Gateway deployed with all endpoints
- [ ] Hub API endpoints functional
- [ ] Database tables created
- [ ] End-to-end integration tested
- [ ] Authentication working
- [ ] **Similarity search API working**
- [ ] **Graph traversal API working**
- [ ] **Insights API working**

---

## Phase 5: Demo & Polish (Weeks 7-8)

### Objectives

- Build demo interface
- Document everything
- Prepare handoff
- Validate success criteria

### Demo Interface

```
Standalone Web App (React or Vue)
│
├── Content Prediction View
│   ├── Select content from Hub
│   ├── Run prediction
│   ├── Display score (0-100%)
│   ├── Show top 5 factors (visual)
│   └── Recommendations
│
├── Persona Agent View
│   ├── Select persona
│   ├── View generated queries
│   ├── Execute against engines
│   ├── Real-time results streaming
│   └── Visibility breakdown by engine
│
├── Intelligence Engine View (NEW)
│   ├── Similarity search interface
│   ├── "Find content like this" feature
│   ├── Knowledge graph explorer
│   ├── Entity relationship visualization
│   └── Natural language insights
│
└── Dashboard
    ├── Overall visibility trends
    ├── Per-client breakdown
    ├── Engine comparison
    └── Persona performance
```

### Tasks

| Task | Description | Priority |
|------|-------------|----------|
| Build demo UI | React app | P0 |
| Create accuracy report | Model performance doc | P0 |
| Write API documentation | OpenAPI/Swagger | P0 |
| Create AWS deployment guide | CloudFormation/Terraform | P0 |
| Write persona authoring guide | How to create personas | P1 |
| Prepare presentation | Stakeholder demo | P0 |
| Conduct user testing | With Brandpoint team | P1 |
| Create post-POC roadmap | Next steps | P1 |

### Deliverables

- [ ] Demo interface working
- [ ] Accuracy report complete (≥65%, ≥15pt lift)
- [ ] API documentation (OpenAPI)
- [ ] AWS deployment guide (IaC)
- [ ] Persona authoring guide
- [ ] Stakeholder presentation delivered
- [ ] Post-POC recommendations documented

---

## Success Metrics

### Primary (Must Achieve)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Absolute Accuracy | ≥65% | Test set evaluation |
| Lift Over Baseline | ≥15 points | vs. random guess (~23%) |
| Statistical Significance | 95% CI | Confidence interval |
| Persona Query Visibility | >Generic | Side-by-side comparison |

### Secondary (Nice to Have)

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time | <500ms P95 | API Gateway latency |
| Step Functions Success | >99% | Execution success rate |
| Hub Integration | Working | End-to-end test |
| Demo Feedback | Positive | Stakeholder survey |
| Monthly AWS Cost | <$600 | CloudWatch billing |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Model underperforms | Medium | High | Ensemble, more features, adjust target |
| Bedrock latency | Low | Medium | Cache common queries, async execution |
| External API rate limits | Medium | Medium | Implement backoff, queue requests |
| Hub integration delays | Medium | Medium | Early coordination, API-first |
| AWS access delays | Low | High | Early provisioning, IaC |
| Persona quality | Medium | High | A/B test vs generic, iterate |

---

## Scope Reduction Options

If timeline pressure requires:

| Priority | Cut | Keep |
|----------|-----|------|
| P0 | Nothing | All core deliverables |
| P1 | Fancy demo UI | Basic prediction display |
| P2 | Multiple personas | Single persona per client |
| P3 | Dashboard analytics | Individual query results |
| P4 | Real-time streaming | Batch results |

---

## Team Responsibilities

### Codename 37

- AWS infrastructure (IaC)
- Step Functions workflow
- Lambda functions
- SageMaker model deployment
- Bedrock integration
- API Gateway configuration
- Demo interface
- Documentation

### Brandpoint

- Staging environment access
- Service account creation
- Hub endpoint additions (~100 lines)
- Database table creation
- User acceptance testing
- Persona validation (are queries realistic?)

---

## Communication Plan

| Event | Frequency | Participants |
|-------|-----------|--------------
| Status update | Weekly | All |
| Technical sync | As needed | Tech leads |
| Demo checkpoint | End of each phase | All |
| Final presentation | End of POC | All + stakeholders |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-22 | Jake Trippel / Claude | Initial roadmap |
| 2.0 | 2025-12-22 | Jake Trippel / Claude | AWS cloud-native, persona agent system |
| 3.0 | 2025-12-22 | Jake Trippel / Claude | Intelligence Engine in POC scope (current data only) |
