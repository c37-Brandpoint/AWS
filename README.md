# Brandpoint AI Platform - AWS Infrastructure

Production-ready Infrastructure as Code (IaC) for deploying the Brandpoint AI Platform on AWS cloud-native services.

**Status: Ready for POC Deployment**

---

## Quick Start

**One command to deploy everything:**

```bash
git clone git@github.com:c37-Brandpoint/AWS.git && cd AWS
./scripts/brandpoint-deploy.sh --env dev
```

That's it. The script will:
- Run preflight checks (credentials, quotas, network conflicts)
- Auto-select a safe VPC CIDR (no manual network configuration needed)
- Deploy all infrastructure
- Guide you through secrets configuration
- Offer to enable scheduled jobs when ready

For the quick reference guide, see: **[docs/BRANDPOINT_RUNBOOK.md](docs/BRANDPOINT_RUNBOOK.md)**

For detailed instructions, see: **[docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)**

---

## Platform Overview

The Brandpoint AI Platform provides three core capabilities:

| Capability | Description | Key Services |
|------------|-------------|--------------|
| **AI Visibility Predictor** | ML model predicting content appearance in AI search results | SageMaker, Lambda, S3 |
| **Persona Agent System** | Simulates real users querying AI engines (ChatGPT, Perplexity, Gemini, Claude) | Step Functions, Lambda, Bedrock, DynamoDB |
| **Intelligence Engine** | Vector + Graph knowledge platform for semantic search and insights | OpenSearch (k-NN), Neptune (Gremlin), Bedrock |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BRANDPOINT AI PLATFORM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────────┐ │
│  │  API Gateway │───▶│  Lambda Functions (16 functions)                    │ │
│  │  (REST API)  │    │  - Persona management (CRUD + execution)            │ │
│  │  + API Keys  │    │  - Query execution (4 AI engines)                   │ │
│  └─────────────┘    │  - Visibility analysis                              │ │
│                      │  - Intelligence engine (search, graph, insights)    │ │
│                      └─────────────────────────────────────────────────────┘ │
│                                     │                                        │
│          ┌──────────────────────────┼──────────────────────────┐            │
│          │                          │                          │            │
│          ▼                          ▼                          ▼            │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐         │
│  │  DynamoDB   │          │  OpenSearch │          │   Neptune   │         │
│  │  (Personas, │          │  (Vectors,  │          │  (Knowledge │         │
│  │   Results)  │          │   k-NN)     │          │    Graph)   │         │
│  └─────────────┘          └─────────────┘          └─────────────┘         │
│                                                                              │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐         │
│  │  SageMaker  │          │   Bedrock   │          │    S3       │         │
│  │ (ML Models) │          │  (Claude,   │          │  (Storage)  │         │
│  │             │          │   Titan)    │          │             │         │
│  └─────────────┘          └─────────────┘          └─────────────┘         │
│                                                                              │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐         │
│  │    Step     │          │ EventBridge │          │  Secrets    │         │
│  │  Functions  │◀─────────│ (Schedules) │          │  Manager    │         │
│  │ (Workflows) │          │             │          │  (API Keys) │         │
│  └─────────────┘          └─────────────┘          └─────────────┘         │
│                                                                              │
│                    ┌─────────────────────────────┐                          │
│                    │        CloudWatch           │                          │
│                    │  (Dashboard, Alarms, Logs)  │                          │
│                    └─────────────────────────────┘                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    Brandpoint Hub (.NET 4.7.2) + ARA3 SQL Server
```

---

## Repository Structure

```
AWS/
├── README.md                              # This file
├── docs/
│   ├── DEPLOYMENT_GUIDE.md               # Step-by-step deployment instructions
│   ├── QUALITY_AUDIT_REPORT.md           # Infrastructure audit results
│   ├── 00_PROJECT_CONTEXT.md             # Engagement overview
│   ├── 01_POC_PROPOSAL_SUMMARY.md        # Business case
│   ├── architecture/                      # Architecture documentation
│   │   ├── 05_INTEGRATION_ARCHITECTURE.md
│   │   ├── 06_IMPLEMENTATION_ROADMAP.md
│   │   ├── 07_PERSONA_AGENT_ARCHITECTURE.md
│   │   ├── 08_INTELLIGENCE_ENGINE_ARCHITECTURE.md
│   │   ├── 09_COMPLETE_PLATFORM_ARCHITECTURE.md
│   │   └── 16_COMPLETE_DATA_FLOW_DOCUMENTATION.md
│   └── integration/
│       └── BRANDPOINT_HANDOFF_GUIDE.md
│
├── infrastructure/
│   ├── cloudformation/                    # CloudFormation templates
│   │   ├── main.yaml                     # Master nested stack
│   │   ├── 00-foundation.yaml            # VPC, Security Groups, IAM
│   │   ├── 01-storage.yaml               # S3, DynamoDB
│   │   ├── 02-databases.yaml             # OpenSearch, Neptune
│   │   ├── 03-compute.yaml               # Lambda, SageMaker
│   │   ├── 04-orchestration.yaml         # Step Functions, EventBridge
│   │   ├── 05-api.yaml                   # API Gateway
│   │   ├── 06-monitoring.yaml            # CloudWatch, Budgets
│   │   ├── 07-secrets.yaml               # Secrets Manager
│   │   └── parameters/
│   │       ├── dev.json                  # Development parameters
│   │       └── prod.json                 # Production parameters
│   │
│   ├── lambda/                           # Lambda function code (Python 3.11)
│   │   ├── load-persona/                 # Load persona from DynamoDB
│   │   ├── generate-queries/             # Generate queries via Bedrock
│   │   ├── execute-query/                # Query AI engines
│   │   ├── analyze-visibility/           # Analyze brand visibility
│   │   ├── store-results/                # Store results + Hub sync
│   │   ├── feature-extraction/           # ML feature extraction
│   │   ├── content-ingestion/            # Vector embeddings
│   │   ├── graph-update/                 # Neptune graph updates
│   │   ├── similarity-search/            # k-NN vector search
│   │   ├── graph-query/                  # Gremlin queries
│   │   ├── insights-generator/           # LLM insights
│   │   ├── prediction-api/               # ML predictions
│   │   ├── persona-api/                  # Persona CRUD API
│   │   ├── intelligence-api/             # Intelligence endpoints
│   │   └── health-check/                 # Health status
│   │
│   ├── step-functions/                   # State machine definitions
│   │   ├── persona-agent-workflow.asl.json
│   │   └── content-ingestion-workflow.asl.json
│   │
│   └── api-gateway/
│       └── openapi.yaml                  # OpenAPI 3.0 specification
│
├── scripts/
│   ├── brandpoint-deploy.sh              # ONE-COMMAND deployment (recommended)
│   ├── deploy.sh                         # Automated deployment (7-step process)
│   ├── preflight-check.sh                # Pre-deployment validation
│   ├── smoke-test.sh                     # Post-deployment verification
│   ├── ignite.sh                         # Enable schedules (after secrets configured)
│   ├── rollback.sh                       # Emergency stack rollback
│   └── destroy.sh                        # Complete teardown
│
└── build/                                # Generated artifacts (gitignored)
    └── lambda/                           # Packaged Lambda ZIPs
```

---

## AWS Services

| Service | Resource | Purpose |
|---------|----------|---------|
| **VPC** | 2 AZs, Private Subnets, NAT Gateway | Network isolation |
| **Lambda** | 16 functions (Python 3.11) | Serverless compute |
| **Step Functions** | 2 state machines | Workflow orchestration |
| **API Gateway** | REST API with API key auth | External access |
| **DynamoDB** | 3 tables (Personas, Results, Predictions) | NoSQL storage |
| **OpenSearch** | k-NN enabled (1536 dimensions) | Vector search |
| **Neptune** | Gremlin graph database | Knowledge graph |
| **SageMaker** | Inference endpoint | ML predictions |
| **Bedrock** | Claude 3.5 Sonnet, Titan Embeddings | LLM + embeddings |
| **S3** | 3 buckets | Models, results, data lake |
| **EventBridge** | 2 rules | Scheduling + events |
| **Secrets Manager** | 5 secrets | API key storage |
| **CloudWatch** | Dashboard + 7 alarms | Monitoring |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predict/{contentId}` | Start prediction |
| `GET` | `/predict/{contentId}` | Get prediction result |
| `GET` | `/personas` | List all personas |
| `POST` | `/personas` | Create persona |
| `GET` | `/personas/{id}` | Get persona |
| `PUT` | `/personas/{id}` | Update persona |
| `DELETE` | `/personas/{id}` | Delete persona |
| `POST` | `/personas/{id}/execute` | Execute persona agent |
| `GET` | `/personas/{id}/results` | Get persona results |
| `POST` | `/intelligence/search` | Semantic search |
| `GET` | `/intelligence/graph/{id}` | Graph traversal |
| `POST` | `/intelligence/insights` | Generate insights |
| `POST` | `/intelligence/ingest` | Ingest content |
| `GET` | `/health` | Health check |

---

## Estimated Monthly Cost

### POC Environment (Default)

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| OpenSearch | 2x t3.small.search, 20GB | ~$50 |
| Neptune | db.t3.medium | ~$50 |
| Lambda | 200K invocations | ~$5 |
| Step Functions | 20K executions | ~$5 |
| Bedrock | 3M tokens | ~$50 |
| SageMaker | ml.t3.medium | ~$50 |
| DynamoDB | On-demand | ~$10 |
| Other (S3, API GW, etc.) | - | ~$30 |
| **Total POC** | | **~$250/month** |

### Production Environment

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| OpenSearch | 2x r6g.large.search, 100GB | ~$400 |
| Neptune | db.r5.large | ~$300 |
| Other services | Production scale | ~$200 |
| **Total Production** | | **~$900/month** |

---

## Deployment

### Prerequisites

- AWS Account with Administrator access
- AWS CLI installed and configured (`aws configure`)
- Python 3.11+ with pip
- Git
- Bash shell (Mac/Linux terminal, or **Git Bash/WSL on Windows**)
- zip utility (included with Git Bash, Mac, and Linux)

### Deploy to Dev (One Command)

```bash
./scripts/brandpoint-deploy.sh --env dev
```

The script handles everything automatically:
- Preflight checks (credentials, quotas, CIDR conflicts)
- Auto-selects a safe VPC CIDR
- Deploys all infrastructure
- Runs smoke tests
- Guides you through secrets configuration
- Enables scheduled jobs when ready

### Deploy to Production

```bash
./scripts/brandpoint-deploy.sh --env prod
```

### Post-Deployment

After deployment, the script will guide you through:
1. Configuring API keys in Secrets Manager
2. Enabling scheduled jobs with `./scripts/ignite.sh --env dev`
3. Setting up VPC Peering for RDS access (see DEPLOYMENT_GUIDE.md)

### Emergency Rollback

```bash
# Delete the stack and all resources (use with caution)
./scripts/rollback.sh dev us-east-1

# Or complete teardown including deployment buckets
./scripts/destroy.sh --environment dev --region us-east-1
```

See **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** for detailed step-by-step instructions.

---

## Configuration

### Environment Parameters

| Parameter | Dev Default | Prod Default |
|-----------|-------------|--------------|
| `OpenSearchInstanceType` | t3.small.search | r6g.large.search |
| `OpenSearchVolumeSize` | 20 GB | 100 GB |
| `NeptuneInstanceClass` | db.t3.medium | db.r5.large |
| `SageMakerInstanceType` | ml.t3.medium | ml.m5.large |
| `HubApiBaseUrl` | hub-staging.brandpoint.com | hub.brandpoint.com |

### Hub Integration

| Setting | Value |
|---------|-------|
| Auth Header | `X-Api-Key` |
| Persona Results Endpoint | `/api/AiPrediction/persona-results` |
| Predictions Endpoint | `/api/AiPrediction/predictions` |

---

## Documentation

| Document | Description |
|----------|-------------|
| **[BRANDPOINT_RUNBOOK.md](docs/BRANDPOINT_RUNBOOK.md)** | One-page quick reference for deployment |
| **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** | Step-by-step deployment for IT team |
| **[QUALITY_AUDIT_REPORT.md](docs/QUALITY_AUDIT_REPORT.md)** | Infrastructure audit and fixes |
| [Integration Architecture](docs/architecture/05_INTEGRATION_ARCHITECTURE.md) | AWS service design |
| [Persona Agent Architecture](docs/architecture/07_PERSONA_AGENT_ARCHITECTURE.md) | Persona system design |
| [Intelligence Engine Architecture](docs/architecture/08_INTELLIGENCE_ENGINE_ARCHITECTURE.md) | Vector + Graph design |
| [Complete Platform Architecture](docs/architecture/09_COMPLETE_PLATFORM_ARCHITECTURE.md) | Unified architecture view |
| [Handoff Guide](docs/integration/BRANDPOINT_HANDOFF_GUIDE.md) | Hub integration details |

---

## Quality Assurance

A comprehensive quality audit was performed to ensure alignment with the original architecture specifications. All critical issues have been resolved:

- IAM policies scoped to least-privilege
- OpenSearch access restricted to Lambda execution role
- Hub API integration configured correctly
- Database sizing optimized for POC
- All 16 Lambda functions implemented
- Both Step Functions workflows defined

See **[QUALITY_AUDIT_REPORT.md](docs/QUALITY_AUDIT_REPORT.md)** for full details.

---

## Support

### Primary Contact (Development & Technical)
- **Company**: Codename37
- **Consultant**: Jake Trippel
- **Email**: jake@codename37.com

### Source Repository
Extracted from: `git@github.com:c37-Brandpoint/brandpoint_ie_poc.git`

---

## License

Proprietary - Brandpoint / Codename37

---

**Document Version**: 3.0
**Last Updated**: January 2026
**Status**: Production-Ready for POC Deployment
