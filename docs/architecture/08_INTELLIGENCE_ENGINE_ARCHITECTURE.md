# Intelligence Engine Architecture

## Executive Summary

The Intelligence Engine transforms Brandpoint's content data into an interconnected, semantically-aware knowledge platform using vector embeddings and graph relationships. This enables AI-powered insights that were previously impossible with traditional relational databases.

### POC Scope

| Scope | Description | Timeline |
|-------|-------------|----------|
| **Current Data (POC)** | Vector + Graph ALL new content as it's published | Weeks 5-8 |
| **Historical Data (Future)** | Backfill 30+ years of content (43K articles) | Post-POC |

**Key Principle**: Start with real-time ingestion of new content. Prove the value. Then backfill historical data.

---

## The Opportunity

### What Brandpoint Has

| Asset | Volume | Current State |
|-------|--------|---------------|
| Articles | 43,927 | Stored in SQL, text-searchable only |
| Article Accesses | 19.25M | Behavioral data, basic analytics |
| Clients | 6,451 | CRM data, siloed |
| Publishers | 50+ networks | Relationship data, not connected |
| AI Monitor Results | 49K+ | Visibility data, not correlated |
| Content Campaigns | 30 years | Historical patterns, untapped |

### What's Missing

**Traditional databases can answer:**
- "Show me articles for client X"
- "How many clicks did article Y get?"
- "List publishers in network Z"

**But cannot answer:**
- "What content LIKE this performed well?"
- "What topics are semantically related to our successful campaigns?"
- "What's the relationship between publisher type, content style, and AI visibility?"
- "What content strategy would work for a NEW client similar to existing ones?"
- "What patterns predict high engagement across different demographics?"

### The Intelligence Engine Solution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INTELLIGENCE ENGINE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   VECTOR LAYER                          GRAPH LAYER                         │
│   "What is SIMILAR?"                    "How is it CONNECTED?"              │
│                                                                              │
│   ┌─────────────────────┐               ┌─────────────────────┐             │
│   │  Content Embeddings │               │  Knowledge Graph    │             │
│   │  - Headlines        │               │  - Client → Content │             │
│   │  - Body text        │               │  - Content → Topic  │             │
│   │  - Topics           │               │  - Topic → Publisher│             │
│   │  - Queries          │               │  - Publisher → Perf │             │
│   └─────────────────────┘               │  - Content → AI Vis │             │
│                                         └─────────────────────┘             │
│                                                                              │
│   INTELLIGENCE LAYER                                                        │
│   "What does it MEAN?"                                                      │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  ML Models + LLM Analysis                                            │  │
│   │  - Pattern recognition                                               │  │
│   │  - Trend prediction                                                  │  │
│   │  - Content recommendations                                           │  │
│   │  - Strategy generation                                               │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Overview

### AWS Services for Intelligence Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE ENGINE - AWS ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DATA INGESTION LAYER                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  EventBridge ──► Step Functions ──► Lambda (processors)              │    │
│  │       │                                    │                         │    │
│  │       │         ┌──────────────────────────┼──────────────────┐     │    │
│  │       │         │                          │                  │     │    │
│  │       ▼         ▼                          ▼                  ▼     │    │
│  │  ┌─────────┐  ┌─────────┐           ┌─────────┐        ┌─────────┐ │    │
│  │  │ Kinesis │  │   S3    │           │ Bedrock │        │   RDS   │ │    │
│  │  │ (stream)│  │ (batch) │           │ (embed) │        │ (source)│ │    │
│  │  └─────────┘  └─────────┘           └─────────┘        └─────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  STORAGE LAYER                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌──────────────────────┐      ┌──────────────────────┐            │    │
│  │  │   VECTOR STORE       │      │    GRAPH STORE       │            │    │
│  │  │   Amazon OpenSearch  │      │    Amazon Neptune    │            │    │
│  │  │   (with k-NN)        │      │    (Property Graph)  │            │    │
│  │  │                      │      │                      │            │    │
│  │  │   • Content vectors  │      │   • Entity nodes     │            │    │
│  │  │   • Query vectors    │      │   • Relationship     │            │    │
│  │  │   • Topic vectors    │      │     edges            │            │    │
│  │  │   • Client profiles  │      │   • Performance      │            │    │
│  │  │                      │      │     attributes       │            │    │
│  │  └──────────────────────┘      └──────────────────────┘            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  INTELLIGENCE LAYER                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │  SageMaker   │  │   Bedrock    │  │  Neptune ML  │              │    │
│  │  │  (Custom ML) │  │   (LLM)      │  │  (Graph ML)  │              │    │
│  │  │              │  │              │  │              │              │    │
│  │  │  • Pattern   │  │  • Analysis  │  │  • Link      │              │    │
│  │  │    detection │  │  • Summary   │  │    prediction│              │    │
│  │  │  • Prediction│  │  • Recommend │  │  • Node      │              │    │
│  │  │  • Clustering│  │  • Generate  │  │    classify  │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  API LAYER                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  API Gateway                                                         │    │
│  │  POST /intelligence/similar     → Find similar content               │    │
│  │  POST /intelligence/insights    → Generate insights for client       │    │
│  │  GET  /intelligence/graph       → Query knowledge graph              │    │
│  │  POST /intelligence/recommend   → Content strategy recommendations   │    │
│  │  POST /intelligence/predict     → Predict performance                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Vector Database Architecture

### Why Vectors?

Traditional search: **keyword matching**
- "beach vacation" only finds documents with those exact words

Vector search: **semantic similarity**
- "beach vacation" also finds "coastal getaway", "oceanside trip", "seaside holiday"

### Embedding Strategy

```
Content Embedding Pipeline:

Article/Content
    │
    ├── Headline ──────────► Bedrock Titan Embeddings ──► 1536-dim vector
    │
    ├── Body Text ─────────► Chunk (512 tokens) ────────► Multiple vectors
    │                              │
    │                              └── Overlap (50 tokens)
    │
    ├── Metadata ──────────► Structured embedding ──────► Combined vector
    │   • Client industry
    │   • Publisher type
    │   • Topic categories
    │
    └── Performance ───────► Behavioral embedding ──────► Outcome vector
        • Engagement rate
        • AI visibility
        • Placement success
```

### Amazon OpenSearch Configuration

```
Index: brandpoint-content-vectors
{
  "settings": {
    "index": {
      "knn": true,
      "knn.algo_param.ef_search": 100
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
      "body_vectors": {
        "type": "nested",
        "properties": {
          "chunk_id": { "type": "integer" },
          "vector": {
            "type": "knn_vector",
            "dimension": 1536
          }
        }
      },
      "metadata": {
        "properties": {
          "industry": { "type": "keyword" },
          "publisher_type": { "type": "keyword" },
          "topics": { "type": "keyword" },
          "publish_date": { "type": "date" },
          "engagement_score": { "type": "float" },
          "ai_visibility_score": { "type": "float" }
        }
      }
    }
  }
}
```

### Vector Search Use Cases

| Use Case | Query Type | Business Value |
|----------|------------|----------------|
| Similar Content | k-NN on headline_vector | "What content like this worked before?" |
| Topic Clustering | Vector aggregation | "What topics naturally group together?" |
| Content Gaps | Inverse similarity | "What topics are we NOT covering?" |
| Client Matching | Client profile similarity | "What clients have similar content needs?" |
| Performance Prediction | Vector + outcome correlation | "Will this content perform well?" |

---

## Graph Database Architecture

### Why Graphs?

Relational databases: **Tables and joins**
- Complex queries require multiple joins
- Relationships are implicit

Graph databases: **Nodes and edges**
- Relationships are first-class citizens
- Traverse connections naturally

### Knowledge Graph Schema

```
NODES (Entities):
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Client    │  │   Content   │  │   Topic     │
├─────────────┤  ├─────────────┤  ├─────────────┤
│ clientId    │  │ contentId   │  │ topicId     │
│ name        │  │ headline    │  │ name        │
│ industry    │  │ publishDate │  │ category    │
│ tier        │  │ contentType │  │ trending    │
└─────────────┘  └─────────────┘  └─────────────┘

┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Publisher  │  │   Query     │  │   Persona   │
├─────────────┤  ├─────────────┤  ├─────────────┤
│ publisherId │  │ queryId     │  │ personaId   │
│ domain      │  │ queryText   │  │ demographics│
│ authority   │  │ queryType   │  │ interests   │
│ aiCrawlable │  │ visibility  │  │ speaking    │
└─────────────┘  └─────────────┘  └─────────────┘

EDGES (Relationships):
Client ──CREATED──► Content
Content ──ABOUT──► Topic
Content ──PUBLISHED_ON──► Publisher
Content ──MENTIONED_IN──► Query (AI response)
Query ──ASKED_BY──► Persona
Client ──TARGETS──► Persona
Topic ──RELATED_TO──► Topic
Publisher ──SYNDICATES_TO──► Publisher
Content ──SIMILAR_TO──► Content (vector similarity edge)
```

### Amazon Neptune (Gremlin) Queries

```groovy
// Find all content paths from client to AI visibility
g.V().has('Client', 'name', 'US Army')
  .out('CREATED').as('content')
  .out('MENTIONED_IN').as('query')
  .has('visibility', gt(0.5))
  .select('content', 'query')
  .by(valueMap())

// Find topics that perform well with specific publishers
g.V().has('Publisher', 'aiCrawlable', true)
  .in('PUBLISHED_ON').as('content')
  .out('ABOUT').as('topic')
  .group()
    .by(select('topic').values('name'))
    .by(select('content').values('engagementScore').mean())
  .order(local).by(values, desc)

// Recommend topics for a new client based on similar clients
g.V().has('Client', 'clientId', 'new-client-123')
  .as('newClient')
  .V().has('Client').has('industry', 'same-industry')
  .where(neq('newClient'))
  .out('CREATED')
  .out('ABOUT')
  .groupCount()
  .order(local).by(values, desc)
  .limit(local, 10)

// Find content gaps: topics covered by competitors but not by client
g.V().has('Client', 'name', 'Client A')
  .out('CREATED').out('ABOUT').store('clientTopics')
  .V().has('Client', 'industry', 'same-industry')
  .out('CREATED').out('ABOUT')
  .where(without('clientTopics'))
  .dedup()
  .valueMap()
```

### Graph Use Cases

| Use Case | Graph Pattern | Business Value |
|----------|---------------|----------------|
| Content Lineage | Client → Content → Publisher → Performance | "Trace success path" |
| Topic Networks | Topic ←→ Topic relationships | "What topics cluster?" |
| Client Similarity | Client → Content → Topic overlap | "Find similar clients" |
| Publisher Effectiveness | Publisher → Content → AI Visibility | "Which publishers get AI pickup?" |
| Persona-Content Match | Persona → Query → Content | "What content resonates with persona?" |
| Gap Analysis | Missing edges | "What's not connected that should be?" |

---

## Intelligence Layer (ML/DL)

### Model Architecture

```
INTELLIGENCE ENGINE MODELS:

1. EMBEDDING MODELS (Bedrock)
   ├── Amazon Titan Embeddings v2
   │   • 1536 dimensions
   │   • Multilingual support
   │   • Optimized for semantic similarity
   └── Purpose: Vector generation for content

2. PATTERN RECOGNITION (SageMaker)
   ├── XGBoost Classifier
   │   • Content performance prediction
   │   • Feature: [content_vector, publisher_features, topic_features]
   │   • Target: engagement_score, ai_visibility
   │
   ├── Neural Network (PyTorch)
   │   • Multi-task learning
   │   • Predict: engagement + visibility + sentiment
   │   • Architecture: Transformer encoder + task heads
   │
   └── Clustering (K-Means / HDBSCAN)
       • Topic discovery
       • Client segmentation
       • Content grouping

3. GRAPH ML (Neptune ML)
   ├── Node Classification
   │   • Predict content success likelihood
   │   • Features: graph structure + node properties
   │
   ├── Link Prediction
   │   • Predict: "Will this content appear in AI responses?"
   │   • Predict: "Will this topic trend?"
   │
   └── Graph Neural Networks
       • Learn from network structure
       • Propagate performance signals through graph

4. LLM ANALYSIS (Bedrock Claude)
   ├── Content Analysis
   │   • Extract topics, entities, sentiment
   │   • Generate summaries
   │
   ├── Strategy Generation
   │   • Input: Graph insights + vector similarities
   │   • Output: Content strategy recommendations
   │
   └── Natural Language Interface
       • "What content should we create for Client X?"
       • "Why did this campaign perform well?"
```

### Training Data Pipeline

```
Historical Data Processing:

ARA3 SQL Server
    │
    ├── Articles (43K) ────────────────────┐
    │                                      │
    ├── ArticleAccesses (19.25M) ──────────┤
    │                                      │
    ├── Clients (6.4K) ────────────────────┤
    │                                      ▼
    ├── HubContent ───────────────► AWS Glue ETL
    │                                      │
    └── AiMonitorResult (49K) ─────────────┤
                                           │
                                           ▼
                              ┌────────────────────────┐
                              │   S3 Data Lake         │
                              │   (Parquet format)     │
                              │                        │
                              │   • content_features/  │
                              │   • engagement_labels/ │
                              │   • visibility_labels/ │
                              │   • graph_edges/       │
                              └────────────────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
            ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
            │   Bedrock    │      │  SageMaker   │      │   Neptune    │
            │  (Embeddings)│      │  (Training)  │      │  (Graph Load)│
            └──────────────┘      └──────────────┘      └──────────────┘
                    │                      │                      │
                    ▼                      ▼                      ▼
            ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
            │  OpenSearch  │      │   S3 Model   │      │   Neptune    │
            │  (Vectors)   │      │  Artifacts   │      │  (Graph DB)  │
            └──────────────┘      └──────────────┘      └──────────────┘
```

---

## Data Flows

### Real-Time Ingestion (New Content)

```
New Content Published in Hub
    │
    ▼
EventBridge (content.published event)
    │
    ▼
Step Functions: ContentIngestionWorkflow
    │
    ├── State 1: Extract Content
    │   └── Lambda: Fetch from Hub API
    │
    ├── State 2: Generate Embeddings
    │   └── Lambda → Bedrock Titan
    │   └── Output: 1536-dim vector
    │
    ├── State 3: Extract Graph Entities
    │   └── Lambda → Bedrock Claude
    │   └── Output: topics, entities, relationships
    │
    ├── State 4: Store Vector (Parallel)
    │   └── Lambda → OpenSearch
    │   └── Index: brandpoint-content-vectors
    │
    └── State 5: Update Graph (Parallel)
        └── Lambda → Neptune
        └── Create: Content node + edges
```

### Historical Data Migration (FUTURE SCOPE - Post-POC)

> **Note**: Historical data migration is NOT part of the POC. This section documents the future approach for backfilling 30+ years of content after the POC proves value with current data.

```
Phase 1: Data Export
├── AWS DMS: SQL Server → S3 (full export)
├── Format: Parquet, partitioned by year
└── Tables: Articles, HubContent, Clients, ArticleAccesses

Phase 2: Embedding Generation
├── AWS Glue: Batch processing job
├── Process: 43K articles in batches of 100
├── Bedrock: Generate embeddings
└── Output: S3 → OpenSearch bulk load

Phase 3: Graph Construction
├── AWS Glue: Transform relational → graph format
├── Output: Nodes CSV, Edges CSV
├── Neptune: Bulk loader
└── Validate: Graph integrity checks

Phase 4: ML Training (Enhanced with Historical Data)
├── SageMaker: Train on historical + labels
├── Neptune ML: Train graph models
└── Deploy: Endpoints for inference

Estimated Duration: 4-6 weeks
Estimated Cost: ~$40,000
```

### Query Flow (Intelligence Request)

```
User: "What content strategy should we use for Client X?"
    │
    ▼
API Gateway: POST /intelligence/recommend
    │
    ▼
Lambda: IntelligenceOrchestrator
    │
    ├── 1. Get Client Context
    │   └── Neptune: g.V().has('Client', 'clientId', 'X').out('CREATED')...
    │   └── Result: Client's content history, topics, performance
    │
    ├── 2. Find Similar Successful Content
    │   └── OpenSearch: k-NN search on client's topic vectors
    │   └── Filter: engagement_score > 0.7, ai_visibility > 0.5
    │   └── Result: Top 10 similar high-performing content
    │
    ├── 3. Analyze Patterns
    │   └── Neptune ML: Predict success likelihood for topics
    │   └── SageMaker: Cluster analysis on successful content
    │   └── Result: Pattern insights
    │
    └── 4. Generate Recommendations
        └── Bedrock Claude:
            Input: {client_context, similar_content, patterns}
            Prompt: "Based on this analysis, recommend content strategy..."
        └── Result: Natural language recommendations

Response:
{
    "clientId": "X",
    "recommendations": [
        {
            "strategy": "Focus on how-to content for topic Y",
            "reasoning": "Similar clients saw 3.2x engagement with this approach",
            "supportingEvidence": [
                {"contentId": 123, "similarity": 0.92, "performance": "high"}
            ],
            "predictedSuccess": 0.78
        }
    ],
    "topicGaps": ["Topic A", "Topic B"],
    "publisherRecommendations": ["Publisher X has 89% AI crawlability"]
}
```

---

## AWS Services Selection

### Core Services

| Component | AWS Service | Purpose | Why This Service |
|-----------|-------------|---------|------------------|
| **Vector Store** | OpenSearch Service | Semantic search, k-NN | Managed, scalable, k-NN plugin |
| **Graph Store** | Neptune | Knowledge graph, relationships | Native graph, Gremlin support, Neptune ML |
| **Embeddings** | Bedrock Titan | Vector generation | Managed, high-quality, AWS-native |
| **LLM Analysis** | Bedrock Claude | Insights, recommendations | Best reasoning, AWS-native |
| **Custom ML** | SageMaker | Pattern recognition, prediction | Full ML lifecycle, managed training |
| **Graph ML** | Neptune ML | Link prediction, node classification | Graph-native ML, integrated |
| **ETL** | Glue | Data transformation | Serverless, Spark-based |
| **Streaming** | Kinesis | Real-time ingestion | Low latency, scalable |
| **Batch** | S3 + Glue | Historical processing | Cost-effective, scalable |
| **Orchestration** | Step Functions | Workflow coordination | Visual, error handling |
| **API** | API Gateway | REST endpoints | Managed, scalable |

### Infrastructure Sizing (POC)

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| OpenSearch | 2x r6g.large.search | ~$200/month |
| Neptune | db.r5.large | ~$250/month |
| Bedrock | Pay per token | ~$50/month |
| SageMaker | ml.t3.medium endpoint | ~$50/month |
| Glue | On-demand ETL | ~$30/month |
| Lambda | ~500K invocations | ~$10/month |
| S3 | 100GB storage | ~$3/month |
| **Total** | | **~$600/month** |

---

## Integration with AI Monitor & Persona Agents

### Unified Platform Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BRANDPOINT AI PLATFORM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  AI VISIBILITY  │  │  PERSONA AGENT  │  │  INTELLIGENCE   │             │
│  │   PREDICTOR     │  │     SYSTEM      │  │     ENGINE      │             │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤             │
│  │ Predict if      │  │ Simulate real   │  │ Vector + Graph  │             │
│  │ content appears │  │ user queries    │  │ insights        │             │
│  │ in AI responses │  │                 │  │                 │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                            │
│                    ┌───────────┴───────────┐                               │
│                    │   SHARED SERVICES     │                               │
│                    ├───────────────────────┤                               │
│                    │ • Bedrock (LLM)       │                               │
│                    │ • SageMaker (ML)      │                               │
│                    │ • OpenSearch (Vector) │                               │
│                    │ • Neptune (Graph)     │                               │
│                    │ • DynamoDB (State)    │                               │
│                    │ • Step Functions      │                               │
│                    └───────────────────────┘                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cross-System Data Flows

```
1. PERSONA → INTELLIGENCE ENGINE
   Persona generates queries
       │
       ▼
   AI engines return responses
       │
       ▼
   Intelligence Engine:
   • Vectorizes responses
   • Updates graph: Query → Content → Visibility
   • Learns: "What query patterns lead to visibility?"

2. INTELLIGENCE ENGINE → PERSONA
   Intelligence Engine analyzes patterns
       │
       ▼
   Identifies: "Casual queries outperform formal"
       │
       ▼
   Persona system: Updates persona query patterns

3. VISIBILITY PREDICTOR → INTELLIGENCE ENGINE
   Predictor scores content
       │
       ▼
   Intelligence Engine:
   • Stores prediction in graph
   • Correlates with actual outcomes
   • Improves prediction model

4. INTELLIGENCE ENGINE → VISIBILITY PREDICTOR
   Intelligence Engine identifies patterns
       │
       ▼
   Feeds features to predictor:
   • Similar content performance
   • Graph-based features (centrality, path scores)
   • Cluster membership
```

### Unified API

```
API Gateway: /api/v1/

AI Monitor:
├── POST /predict/{contentId}          → Visibility prediction
├── GET  /predict/{contentId}          → Get prediction
├── POST /persona/{id}/execute         → Run persona agent
└── GET  /persona/{id}/results         → Get persona results

Intelligence Engine:
├── POST /intelligence/similar         → Find similar content
│   Request: { "contentId": 123, "limit": 10 }
│   Response: { "similar": [{ "contentId": 456, "similarity": 0.92 }] }
│
├── POST /intelligence/insights        → Generate insights
│   Request: { "clientId": "abc", "timeRange": "90d" }
│   Response: { "insights": [...], "recommendations": [...] }
│
├── GET  /intelligence/graph           → Query knowledge graph
│   Request: ?query=g.V().has('Client','name','US Army')...
│   Response: { "nodes": [...], "edges": [...] }
│
├── POST /intelligence/recommend       → Content recommendations
│   Request: { "clientId": "abc", "targetPersona": "18-24-male" }
│   Response: { "recommendations": [...] }
│
└── POST /intelligence/predict         → Performance prediction
    Request: { "content": "...", "publisher": "...", "topic": "..." }
    Response: { "predictedEngagement": 0.72, "predictedVisibility": 0.65 }
```

---

## Use Cases & Business Value

### 1. Content Strategy Optimization

**Question**: "What content should we create for a new healthcare client?"

**Process**:
1. Find similar healthcare clients in graph
2. Analyze their successful content (vector similarity)
3. Identify topic gaps (graph analysis)
4. Generate recommendations (LLM)

**Value**: Data-driven content strategy vs. guesswork

### 2. Publisher Selection

**Question**: "Which publishers should we target for AI visibility?"

**Process**:
1. Query graph: Publisher → Content → AI Visibility
2. Aggregate by publisher, filter by ai_crawlable
3. Rank by visibility success rate

**Value**: Optimize distribution for AI era

### 3. Trend Detection

**Question**: "What topics are emerging in our industry?"

**Process**:
1. Vector clustering on recent content
2. Compare to historical clusters
3. Identify new/growing clusters
4. Alert on emerging topics

**Value**: Early trend identification

### 4. Client Similarity

**Question**: "What clients are similar to our best performers?"

**Process**:
1. Embed client profiles (industry, content history, performance)
2. k-NN search for similar clients
3. Identify: underperforming but similar to high performers
4. Apply successful strategies

**Value**: Replicate success across client base

### 5. Content Gap Analysis

**Question**: "What topics should Client X cover that they're missing?"

**Process**:
1. Graph: Client X → Content → Topics
2. Graph: Similar Clients → Content → Topics
3. Difference: Topics covered by similar clients but not X
4. Filter by performance metrics

**Value**: Identify missed opportunities

### 6. AI Visibility Correlation

**Question**: "What factors most influence AI visibility?"

**Process**:
1. Neptune ML: Feature importance analysis
2. Graph: Content → attributes → AI Visibility edges
3. Identify: publisher type, topic, query alignment
4. Build predictive features

**Value**: Actionable insights for GEO

---

## Implementation Phases

### POC Scope: Intelligence Engine with Current Data

The Intelligence Engine is **IN POC SCOPE** for real-time processing of new/current data. Historical data migration is future scope.

#### Phase A: Infrastructure Setup (Week 5)

| Task | Duration | Description |
|------|----------|-------------|
| OpenSearch setup | 2 days | Deploy, configure k-NN index |
| Neptune setup | 2 days | Deploy, design schema |
| IAM roles & security | 1 day | Cross-service permissions |
| Basic APIs | 2 days | Similar content, graph queries |

#### Phase B: Real-Time Ingestion Pipeline (Week 6)

| Task | Duration | Description |
|------|----------|-------------|
| Content publish event | 1 day | EventBridge trigger on Hub publish |
| Embedding Lambda | 2 days | Content → Bedrock → Vector |
| Graph Lambda | 2 days | Content → Entity extraction → Neptune |
| Step Functions workflow | 2 days | Orchestrate ingestion pipeline |

#### Phase C: Intelligence APIs (Weeks 7-8)

| Task | Duration | Description |
|------|----------|-------------|
| Similarity search API | 2 days | k-NN search on OpenSearch |
| Graph query API | 2 days | Gremlin queries on Neptune |
| Insights API | 3 days | Bedrock analysis + recommendations |
| Integration testing | 3 days | End-to-end validation |

### Future Scope: Historical Data Migration (Post-POC)

| Task | Duration | Description |
|------|----------|-------------|
| ETL pipeline | 2 weeks | AWS Glue jobs for batch processing |
| Embedding generation | 1 week | Batch process 43K articles |
| Graph loading | 1 week | Build complete knowledge graph |
| Neptune ML training | 2 weeks | Link prediction, node classification |
| Enhanced ML models | 2 weeks | Performance prediction with full data |

**Total Historical Migration**: ~6-8 weeks, ~$40,000

---

## Cost-Benefit Analysis

### Investment

| Phase | Cost | Duration | Scope |
|-------|------|----------|-------|
| **POC (Complete)** | **$60,000** | **6-8 weeks** | Predictor + Personas + IE (current data) |
| Historical Data Migration | ~$40,000 | 6-8 weeks | Backfill 43K articles (future) |
| **Total Platform** | **~$100,000** | **~4 months** | Full platform with history |

### POC Monthly Costs (All Components)

| Component | Monthly Cost |
|-----------|-------------|
| AI Monitor + Personas | ~$130 |
| OpenSearch (vectors) | ~$200 |
| Neptune (graph) | ~$250 |
| Additional Bedrock | ~$20 |
| **POC Total** | **~$600/month** |

### Post-Historical Migration Costs

| Component | Monthly Cost |
|-----------|-------------|
| POC services | ~$600 |
| Glue (ETL - one time) | ~$30 |
| **Total Platform** | **~$630/month** |

### Value Unlocked

| Capability | Current State | With Intelligence Engine |
|------------|---------------|--------------------------|
| Content recommendations | Manual/intuition | AI-driven, data-backed |
| Publisher selection | Static lists | Performance-optimized |
| Trend detection | Reactive | Predictive |
| Client insights | Basic reporting | Deep pattern analysis |
| Strategy generation | Manual research | Automated, scalable |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-22 | Jake Trippel / Claude | Initial architecture |
| 2.0 | 2025-12-22 | Jake Trippel / Claude | IE moved to POC scope (current data only), historical migration is future |
