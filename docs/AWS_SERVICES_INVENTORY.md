# AWS Services Inventory

Comprehensive inventory of all AWS services required for the Brandpoint AI Platform.

## Service Summary

| Category | Service | Count | Purpose |
|----------|---------|-------|---------|
| **Foundation** | VPC | 1 | Network isolation (10.100.0.0/16) |
| | Security Groups | 5 | Network security |
| | IAM Roles | 5 | Service permissions |
| **Storage** | S3 | 3 buckets | Models, data, archives |
| | DynamoDB | 3 tables | Personas, results, predictions |
| **Databases** | OpenSearch | 1 cluster | Vector search (k-NN) |
| | Neptune | 1 cluster | Knowledge graph |
| **Compute** | Lambda | 16 functions | Business logic |
| | SageMaker | 1 endpoint | ML inference |
| **Orchestration** | Step Functions | 2 state machines | Workflow automation |
| | EventBridge | 2 rules | Scheduling, events |
| **API** | API Gateway | 1 REST API | External interface |
| **AI/ML** | Bedrock | 2 models | Claude + Titan |
| **Security** | Secrets Manager | 6 secrets | API keys, database credentials, RDS access |
| **Operations** | CloudWatch | Dashboard + 7 alarms | Monitoring |
| | Budgets | 1 budget | Cost control |

---

## Phase 0: Foundation Infrastructure

### 1. VPC Configuration

```yaml
VPC:
  CIDR: 10.100.0.0/16  # Non-overlapping with existing Brandpoint VPC
  Subnets:
    Public:
      - 10.100.1.0/24 (us-east-1a)
      - 10.100.2.0/24 (us-east-1b)
    Private:
      - 10.100.10.0/24 (us-east-1a)
      - 10.100.11.0/24 (us-east-1b)
  NAT Gateway: Yes (for Lambda outbound to external APIs)
  Internet Gateway: Yes
  VPC Peering: To existing Brandpoint VPC (for RDS access)
```

### 2. Security Groups

| Name | Purpose | Inbound | Outbound |
|------|---------|---------|----------|
| `sg-lambda` | Lambda functions | None | 443 (HTTPS), 8182 (Neptune), 1433 (SQL Server via VPC Peering) |
| `sg-opensearch` | OpenSearch cluster | 443 from Lambda SG | None |
| `sg-neptune` | Neptune cluster | 8182 from Lambda SG | None |
| `sg-sagemaker` | SageMaker endpoint | 443 from Lambda SG | None |
| `sg-api-gateway` | API Gateway VPC Link | 443 from internet | Lambda SG |

**Note:** RDS security group in existing Brandpoint VPC must allow inbound 1433 from 10.100.0.0/16

### 3. IAM Roles

| Role | Trust | Policies |
|------|-------|----------|
| `BrandpointLambdaRole` | lambda.amazonaws.com | DynamoDB, S3, Bedrock, Secrets, CloudWatch, VPC |
| `BrandpointStepFunctionsRole` | states.amazonaws.com | Lambda invoke, DynamoDB, CloudWatch |
| `BrandpointSageMakerRole` | sagemaker.amazonaws.com | S3, CloudWatch, ECR |
| `BrandpointAPIGatewayRole` | apigateway.amazonaws.com | Lambda invoke, CloudWatch |
| `BrandpointEventBridgeRole` | events.amazonaws.com | Step Functions start |

---

## Storage Layer

### S3 Buckets

| Bucket | Purpose | Lifecycle |
|--------|---------|-----------|
| `brandpoint-model-artifacts` | ML model files, training data | Standard |
| `brandpoint-results-archive` | Prediction/query results | IA after 30 days |
| `brandpoint-data-lake` | Raw data, ETL outputs | Glacier after 90 days |

### DynamoDB Tables

#### Table: `personas`

```yaml
TableName: brandpoint-personas
PartitionKey: personaId (S)
Attributes:
  - personaId: String
  - clientId: String
  - brandId: String
  - demographics: Map
  - psychographics: Map
  - queryPatterns: Map
  - targetQueries: List
  - createdAt: String
  - updatedAt: String
GSI:
  - clientId-index (clientId, personaId)
Capacity: On-Demand
```

#### Table: `query_results`

```yaml
TableName: brandpoint-query-results
PartitionKey: executionId (S)
SortKey: resultId (S)
Attributes:
  - executionId: String
  - resultId: String
  - personaId: String
  - queryText: String
  - engine: String
  - responseText: String
  - brandMentioned: Boolean
  - visibilityScore: Number
  - executedAt: String
GSI:
  - personaId-executedAt-index (personaId, executedAt)
Capacity: On-Demand
TTL: expiresAt (90 days)
```

---

## Database Layer

### OpenSearch Service

```yaml
DomainName: brandpoint-vectors
EngineVersion: OpenSearch_2.11
ClusterConfig:
  InstanceType: r6g.large.search
  InstanceCount: 2
  DedicatedMasterEnabled: false
  ZoneAwarenessEnabled: true
EBSOptions:
  VolumeType: gp3
  VolumeSize: 100
  Iops: 3000
AdvancedOptions:
  indices.knn: "true"
VPCOptions:
  SubnetIds: [private-subnet-1, private-subnet-2]
  SecurityGroupIds: [sg-opensearch]
```

#### k-NN Index Configuration

```json
{
  "settings": {
    "index": {
      "knn": true,
      "knn.algo_param.ef_search": 100,
      "number_of_shards": 2,
      "number_of_replicas": 1
    }
  },
  "mappings": {
    "properties": {
      "content_id": { "type": "keyword" },
      "client_id": { "type": "keyword" },
      "headline_vector": {
        "type": "knn_vector",
        "dimension": 1536,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "nmslib"
        }
      },
      "metadata": {
        "properties": {
          "industry": { "type": "keyword" },
          "topics": { "type": "keyword" },
          "publish_date": { "type": "date" },
          "ai_visibility_score": { "type": "float" }
        }
      }
    }
  }
}
```

### Neptune

```yaml
DBClusterIdentifier: brandpoint-knowledge-graph
Engine: neptune
EngineVersion: 1.2.1.0
DBInstanceIdentifier: brandpoint-neptune-instance
DBInstanceClass: db.r5.large
AvailabilityZone: us-east-1a
DBSubnetGroupName: neptune-subnet-group
VPCSecurityGroups: [sg-neptune]
IAMDatabaseAuthenticationEnabled: true
```

#### Graph Schema

```
Nodes:
- Client (clientId, name, industry, tier)
- Content (contentId, headline, publishDate, contentType)
- Topic (topicId, name, category, trending)
- Publisher (publisherId, domain, authority, aiCrawlable)
- Query (queryId, queryText, queryType, visibility)
- Persona (personaId, demographics, interests, speaking)

Edges:
- Client --CREATED--> Content
- Content --ABOUT--> Topic
- Content --PUBLISHED_ON--> Publisher
- Content --MENTIONED_IN--> Query
- Query --ASKED_BY--> Persona
- Client --TARGETS--> Persona
- Topic --RELATED_TO--> Topic
- Content --SIMILAR_TO--> Content (weight: similarity score)
```

---

## Compute Layer

### Lambda Functions (16 Total)

| Function | Runtime | Memory | Timeout | Trigger | RDS Access |
|----------|---------|--------|---------|---------|------------|
| `load-persona` | Python 3.11 | 256 MB | 30s | Step Functions | No |
| `generate-queries` | Python 3.11 | 512 MB | 60s | Step Functions | No |
| `execute-query` | Python 3.11 | 256 MB | 120s | Step Functions | No |
| `analyze-visibility` | Python 3.11 | 512 MB | 60s | Step Functions | No |
| `store-results` | Python 3.11 | 256 MB | 30s | Step Functions | No |
| `feature-extraction` | Python 3.11 | 1024 MB | 60s | API Gateway | **Yes** |
| `content-ingestion` | Python 3.11 | 512 MB | 60s | EventBridge | **Yes** |
| `graph-update` | Python 3.11 | 512 MB | 60s | EventBridge | No |
| `similarity-search` | Python 3.11 | 256 MB | 30s | API Gateway | No |
| `graph-query` | Python 3.11 | 256 MB | 30s | API Gateway | No |
| `insights-generator` | Python 3.11 | 512 MB | 60s | API Gateway | No |
| `prediction-api` | Python 3.11 | 512 MB | 30s | API Gateway | **Yes** |
| `persona-api` | Python 3.11 | 256 MB | 30s | API Gateway | No |
| `intelligence-api` | Python 3.11 | 512 MB | 30s | API Gateway | No |
| `health-check` | Python 3.11 | 128 MB | 10s | API Gateway | No |
| `common` (Layer) | Python 3.11 | - | - | Shared library | No |

**Note:** The `execute-query` function handles all 4 AI engines (ChatGPT, Perplexity, Gemini, Claude) based on input parameters.

### SageMaker Endpoint

```yaml
EndpointName: brandpoint-visibility-predictor
EndpointConfigName: brandpoint-predictor-config
ModelName: brandpoint-visibility-model
InstanceType: ml.t3.medium
InitialInstanceCount: 1
VariantName: AllTraffic
```

---

## Orchestration Layer

### Step Functions State Machines

#### 1. Persona Agent Workflow

```yaml
StateMachineName: PersonaAgentExecution
States:
  - LoadPersona (Task -> DynamoDB)
  - GenerateQueries (Task -> Lambda -> Bedrock)
  - ExecuteQueries (Map -> Parallel Lambda)
  - AnalyzeVisibility (Task -> Lambda -> Bedrock)
  - StoreResults (Parallel -> DynamoDB + Hub API)
```

#### 2. Content Ingestion Workflow

```yaml
StateMachineName: ContentIngestionWorkflow
States:
  - ExtractContent (Task -> Lambda)
  - GenerateEmbeddings (Task -> Lambda -> Bedrock Titan)
  - ExtractEntities (Task -> Lambda -> Bedrock Claude)
  - StoreVector (Task -> Lambda -> OpenSearch)
  - UpdateGraph (Task -> Lambda -> Neptune)
```

### EventBridge Rules

| Rule | Schedule/Event | Target |
|------|----------------|--------|
| `PersonaAgentDaily` | `cron(0 6 * * ? *)` | Step Functions |
| `ContentPublished` | Hub publish event | Step Functions |
| `ModelRetraining` | `cron(0 0 * * 0 ?)` | SageMaker Pipeline |

---

## API Layer

### API Gateway Endpoints

```yaml
RestApiName: brandpoint-ai-platform-api
Endpoints:
  # Prediction
  - POST /predict/{contentId}
  - GET /predict/{contentId}

  # Persona
  - POST /persona/{personaId}/execute
  - GET /persona/{personaId}/results
  - POST /persona
  - GET /personas

  # Intelligence Engine
  - POST /intel/similar
  - GET /intel/graph/{entityId}
  - POST /intel/insights
  - POST /intel/recommend
  - POST /intel/predict

  # Health
  - GET /health
```

---

## AI/ML Services

### Bedrock Models

| Model | Model ID | Purpose |
|-------|----------|---------|
| Claude 3.5 Sonnet | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Query generation, analysis |
| Titan Embeddings | `amazon.titan-embed-text-v2:0` | Vector generation (1536 dim) |

### Bedrock Configuration

```yaml
BedrockInvocationPolicy:
  MaxTokens: 4096
  Temperature: 0.7 (queries), 0.0 (analysis)
  TopP: 0.9
```

---

## Security Layer

### Secrets Manager Secrets (6 Total)

| Secret | Purpose | Rotation |
|--------|---------|----------|
| `openai-api-key` | ChatGPT queries | Manual |
| `perplexity-api-key` | Perplexity queries | Manual |
| `gemini-api-key` | Google Gemini queries | Manual |
| `hub-service-account-key` | Hub API auth | Manual |
| `ara3-database-readonly` | ARA3 SQL Server RDS access (via VPC Peering) | Manual |
| `hub-database-readonly` | Hub database access | 30 days |

---

## Operations Layer

### CloudWatch

| Resource | Metric | Alarm Threshold |
|----------|--------|-----------------|
| Lambda | Errors | > 5% |
| Lambda | Duration | > 80% timeout |
| Step Functions | ExecutionsFailed | > 1% |
| SageMaker | InvocationErrors | > 1% |
| OpenSearch | ClusterStatus | Red |
| Neptune | CPUUtilization | > 80% |
| API Gateway | 4XXError | > 5% |
| API Gateway | 5XXError | > 1% |

### CloudWatch Dashboards

- **Platform Overview**: All service health
- **Persona Agents**: Execution metrics, visibility scores
- **Intelligence Engine**: Query latency, index health
- **Cost Tracking**: Daily/monthly spend

### X-Ray Tracing

- Lambda functions: Enabled
- API Gateway: Enabled
- Step Functions: Enabled

---

## Cost Estimates (Monthly)

### POC/Development Environment

| Service | Configuration | Cost |
|---------|---------------|------|
| VPC + NAT Gateway | 1 NAT | $35 |
| Lambda | 200K invocations | $4 |
| Step Functions | 20K executions | $5 |
| Bedrock (Claude) | 2M tokens | $30 |
| Bedrock (Titan) | 1M tokens | $20 |
| SageMaker | ml.t3.medium 24/7 | $50 |
| DynamoDB | 2GB, on-demand | $10 |
| OpenSearch | 2x t3.small.search | $50 |
| Neptune | db.t3.medium | $60 |
| S3 | 20GB | $5 |
| Secrets Manager | 6 secrets | $3 |
| CloudWatch | Logs + metrics | $15 |
| API Gateway | 200K requests | $7 |
| **POC Total** | | **~$294/month** |

### Production Environment

| Service | Configuration | Cost |
|---------|---------------|------|
| VPC + NAT Gateway | 1 NAT | $35 |
| Lambda | 500K invocations | $10 |
| Step Functions | 50K executions | $13 |
| Bedrock (Claude) | 5M tokens | $75 |
| Bedrock (Titan) | 2M tokens | $40 |
| SageMaker | ml.m5.large 24/7 | $120 |
| DynamoDB | 10GB, on-demand | $25 |
| OpenSearch | 2x r6g.large.search | $200 |
| Neptune | db.r5.large | $250 |
| S3 | 100GB | $25 |
| Secrets Manager | 6 secrets | $3 |
| CloudWatch | Logs + metrics | $25 |
| API Gateway | 500K requests | $18 |
| **Production Total** | | **~$839/month** |

---

## GitHub Issues Reference

All infrastructure tasks from the source repo organized by phase:

### Phase 0: Foundation
- [#1] Provision AWS account and VPC infrastructure
- [#2] Create DynamoDB tables for persona and results storage
- [#3] Deploy OpenSearch cluster for vector search
- [#4] Deploy Neptune cluster for knowledge graph
- [#5] Configure Secrets Manager for API keys
- [#6] Set up CloudWatch dashboards and monitoring
- [#7] Configure S3 buckets for model artifacts and results
- [#8] Configure CI/CD pipeline for Lambda deployments

### Phase 3: Infrastructure Components
- [#24] Create Step Functions state machine for persona agent workflow
- [#30] Configure EventBridge schedule for automated persona execution

### Phase 4: API Layer
- [#35] Create API Gateway REST API with authentication
- [#36] Implement prediction API endpoints
- [#37] Implement persona API endpoints
- [#38] Implement Intelligence Engine API endpoints

### Phase 5: Documentation
- [#45] Write API documentation (OpenAPI/Swagger)
- [#46] Create AWS deployment guide (Infrastructure as Code)

---

## Deployment Scripts

| Script | Purpose |
|--------|---------|
| `brandpoint-deploy.sh` | **One-command deployment** - runs everything automatically |
| `ignite.sh` | Enable EventBridge schedules after secrets are configured |
| `preflight-check.sh` | Validate AWS credentials, quotas, and CIDR conflicts |
| `deploy.sh` | 7-step deployment process (used by brandpoint-deploy.sh) |
| `smoke-test.sh` | Post-deployment verification |
| `rollback.sh` | Emergency stack rollback |
| `destroy.sh` | Complete teardown with cleanup guidance |

---

**Document Version:** 3.0
**Last Updated:** January 2026
