# Project Context & Overview

## Document Purpose

This document establishes the context for the Brandpoint Intelligence Engine POC engagement, capturing all knowledge gathered during discovery and analysis phases.

---

## Engagement Overview

| Item | Details |
|------|---------|
| **Client** | Brandpoint |
| **Engagement** | Intelligence Engine POC |
| **Investment** | $60,000 |
| **Timeline** | 6-8 weeks (Phase 1: Dec 2025, Phase 2: Jan 2026) |
| **Codename 37 Team** | Michael Brendon (Leadership), Jake Trippel (Technology) |
| **Brandpoint Team** | Stacy Stusynski (Strategy), Libby Schulzetenberg (Product), Adam McBroom (Tech SME), Brendan Malone (Tech SME) |

---

## What is Brandpoint?

Brandpoint is an enterprise content marketing company that:

1. **Creates branded content** - Articles, infographics, videos for client brands
2. **Distributes to major publishers** - 50+ news networks (AP, USA Today, Tribune, Hearst, McClatchy)
3. **Manages workflows** - End-to-end content lifecycle from idea to publication
4. **Provides SaaS portal** - "Hub" client portal for content management
5. **Tracks performance** - Placement tracking, engagement analytics, ROI reporting

### Business Model

- **Distribution** - Syndicated articles placed on news sites
- **Development** - Custom content creation services
- **Hub SaaS** - Self-service content management platform

---

## The Problem We're Solving

### The AI Search Revolution

Traditional search (Google, Bing) is being disrupted by AI-powered search:

| Platform | Market Share (Oct 2025) |
|----------|------------------------|
| ChatGPT | 81.37% |
| Perplexity | 11.12% |
| Microsoft Copilot | 3.46% |
| Google Gemini | 3.01% |

**Critical Finding**: When users ask AI chatbots questions, **77% of responses mention NO brands at all**.

This means:
- Brands are becoming invisible in AI search
- Traditional SEO doesn't work for AI visibility
- No one is measuring brand presence in AI responses
- Content strategy needs to change for the AI era

### The Opportunity

Brandpoint distributes thousands of articles annually. If they can predict which content will appear in AI search results BEFORE publishing, they can:

1. **Optimize content** for AI visibility
2. **Prove value** to clients with measurable AI metrics
3. **Create new revenue** from AI optimization services
4. **Lead the market** as first-movers in GEO (Generative Engine Optimization)

---

## What We're Building

### AI Visibility Predictor

A machine learning model that predicts whether content will appear in AI search results.

**Two Insight Modes:**

| Mode | Timing | Purpose |
|------|--------|---------|
| **Pre-Release** | Before publishing | Predict visibility, recommend optimizations |
| **Post-Release** | After AI responses collected | Explain why content appeared/didn't |

### Persona-Based Agent System (NEW)

A breakthrough approach to AI visibility measurement using intelligent agents that simulate real target audience personas.

**The Problem with Generic Prompts:**
- Current AI Monitor uses generic queries like "What are the benefits of military service?"
- Real 18-24 year olds don't talk like that
- Result: 0% visibility on generic queries

**The Persona Solution:**
- Create agents that simulate actual target personas
- Generate queries the way REAL customers ask
- Example: "is the army worth it if i don't want college debt"

| Client | Persona | Generic Query (Fails) | Persona Query (Wins) |
|--------|---------|----------------------|---------------------|
| US Army | 18-24 male | "Benefits of military service" | "is joining the army worth it in 2025" |
| United Healthcare | 65 female | "Medicare supplement plans" | "turning 65 do i need to sign up for medicare" |
| Myrtle Beach | 45 couple | "SC vacation destinations" | "beach trip with teenagers that won't break the bank" |

### Intelligence Engine (POC Scope - Current Data)

Beyond AI visibility prediction, Brandpoint is sitting on 30+ years of untapped data potential. The Intelligence Engine transforms this data into an interconnected knowledge platform.

**POC Scope**: Real-time vectorization and graphing of NEW content as it's published.
**Future Scope**: Historical data migration (43K articles, 30+ years).

The Intelligence Engine uses:

**Vector Databases** - Semantic understanding
- Convert all content into embeddings (1536-dimensional vectors)
- Enable: "Find content SIMILAR to this" not just "containing these keywords"
- Discover topic clusters, content gaps, and semantic relationships

**Graph Databases** - Relationship mapping
- Map connections: Client → Content → Topic → Publisher → Performance → AI Visibility
- Enable: "What paths lead to success?" "What patterns predict engagement?"
- Traverse relationships that are invisible in relational databases

**ML/Deep Learning** - Pattern intelligence
- Neural networks for performance prediction
- Graph ML for link prediction and node classification
- LLM analysis for natural language insights and recommendations

**Business Impact:**

| Current State | With Intelligence Engine |
|---------------|-------------------------|
| "Show articles for client X" | "What content LIKE our best performers should client X create?" |
| Keyword search | Semantic similarity search |
| Manual strategy | AI-generated recommendations |
| Historical reports | Predictive insights |
| Siloed data | Connected knowledge graph |

**Note**: Intelligence Engine is IN POC SCOPE for current/new data. Historical data migration is post-POC. See [08_INTELLIGENCE_ENGINE_ARCHITECTURE.md](08_INTELLIGENCE_ENGINE_ARCHITECTURE.md) for full design.

### Success Criteria

| Metric | Target |
|--------|--------|
| Absolute Accuracy | ≥65% |
| Lift Over Baseline | ≥15 percentage points |
| Statistical Confidence | 95% |

### Revenue Potential (Risk-Adjusted)

| Scenario | Annual Revenue |
|----------|---------------|
| Conservative | $300,000 |
| Moderate | $600,000 |
| Aggressive | $1,200,000 |

---

## Data Assets Available

### AI Monitor Production Data

Brandpoint has already collected:

| Metric | Value |
|--------|-------|
| Total AI responses | 49,090 |
| Days of data | 93 |
| Brands tracked | 13 |
| Queries tracked | 228 |
| Date range | Sep 8 - Dec 10, 2025 |

### Key Findings from Data

1. **77% Invisibility**: Most AI responses mention no brands
2. **3.7x Web Search Lift**: Content with web search enabled gets 3.7x more visibility
3. **Query Type Matters**: Brand-in-query = 100% success, generic how-to = 13%
4. **Engine Differences**: 5.3% gap between AI engines (statistically significant)

### SQL Server Foundation

| Asset | Volume | ML Value |
|-------|--------|----------|
| ArticleAccesses | 19.25M | Behavioral prediction |
| Articles | 43,927 | 30 years of content corpus |
| Clients | 6,451 | Segmentation data |
| Relationship Mappings | 300K+ | Graph analytics potential |

---

## Technology Landscape

### Legacy Stack (Brandpoint Hub)

| Component | Technology | Constraint |
|-----------|------------|------------|
| Framework | .NET Framework 4.7.2 | Cannot run modern AI libraries |
| Frontend | AngularJS 1.6.9 | EOL, security vulnerabilities |
| ORM | Entity Framework 6 | Database-first, auto-generated |
| Database | SQL Server 2019 | Solid foundation |
| AI (current) | OpenAI GPT-4o-mini | Basic integration exists |

### Why Legacy Matters

The Hub is stable but fragile:
- 95% static services (no dependency injection)
- No unit tests
- 630KB ContentService.cs monolith
- No API documentation
- Tight coupling throughout

**Decision**: Don't break what's working. Build new AI platform separately.

### New Stack (AWS Cloud-Native)

**Key Decision**: No VMs. Use AWS native serverless and managed services.

| Component | AWS Service | Purpose |
|-----------|-------------|---------|
| Orchestration | Step Functions | Agent workflow management |
| Compute | Lambda + Fargate | Serverless execution |
| AI/LLM | Bedrock (Claude 3.5) | Query generation, response analysis |
| ML Models | SageMaker | Visibility predictor hosting |
| Persona Store | DynamoDB | Persona definitions, session state |
| Storage | S3 | Model artifacts, result archives |
| API | API Gateway | Hub integration, REST endpoints |
| Scheduling | EventBridge | Scheduled agent execution |
| Secrets | Secrets Manager | API keys (OpenAI, Perplexity, etc.) |
| Monitoring | CloudWatch + X-Ray | Logs, metrics, tracing |
| **Vector Store** | OpenSearch Service | Semantic search, embeddings (POC) |
| **Graph Store** | Neptune | Knowledge graph, relationships (POC) |
| **Graph ML** | Neptune ML | Link prediction, node classification (POC) |

**Why Cloud-Native over VMs:**
- Pay per execution (not 24/7)
- Auto-scaling
- No OS maintenance
- ~70% lower cost at moderate volume

---

## Key Stakeholders

### Brandpoint

| Person | Role | Focus |
|--------|------|-------|
| Stacy Stusynski | Strategy/Experience/Commercialization | Business value, go-to-market |
| Libby Schulzetenberg | Product Development Manager/Scrum Master | Feature prioritization, sprints |
| Adam McBroom | Technology Access SME | System access, integrations |
| Brendan Malone | Technology SME | Technical implementation |

### Codename 37

| Person | Role | Focus |
|--------|------|-------|
| Michael Brendon | Leadership Captain | Client relationship, delivery |
| Jake Trippel | Technology Leader | Architecture, implementation |

---

## Repository Structure

```
brandpoint_ie_poc/
├── README.md                              # Project overview
├── Brandpoint Proposalv4_November 24 2025 (1).pdf  # Original proposal
└── docs/
    ├── 00_PROJECT_CONTEXT.md              # This document
    ├── 01_POC_PROPOSAL_SUMMARY.md         # Proposal key points
    ├── 02_AI_MONITOR_ANALYSIS.md          # 49K records analysis
    ├── 03_SQL_SERVER_FOUNDATION.md        # Database assets
    ├── 04_LEGACY_SYSTEM_ARCHITECTURE.md   # Hub & 13 projects
    ├── 05_INTEGRATION_ARCHITECTURE.md     # Integration plan
    ├── 06_IMPLEMENTATION_ROADMAP.md       # Build plan
    ├── 07_PERSONA_AGENT_ARCHITECTURE.md   # Persona-based agents
    ├── 08_INTELLIGENCE_ENGINE_ARCHITECTURE.md  # Vector + Graph platform (future)
    └── 09_COMPLETE_PLATFORM_ARCHITECTURE.md    # Unified architecture
```

---

## Related Repositories & Resources

| Resource | Location | Purpose |
|----------|----------|---------|
| AI Monitor Analysis | `/home/jaket/dev_c37/brandpoint_ai_monitor` | Data analysis, findings |
| Legacy Codebase | `/home/jaket/dev_c37/AI_Monitor_Legacy` | Hub, services, all 13 projects |
| SQL Assessment | `/home/jaket/dev_c37/SQL_server` | Database evaluation |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-22 | Jake Trippel / Claude | Initial documentation |
| 1.1 | 2025-12-22 | Jake Trippel / Claude | Added persona-based agent system, AWS cloud-native stack |
| 1.2 | 2025-12-22 | Jake Trippel / Claude | Added Intelligence Engine vision (vector + graph databases) |
| 1.3 | 2025-12-22 | Jake Trippel / Claude | Added complete platform architecture reference |
| 1.4 | 2025-12-22 | Jake Trippel / Claude | Intelligence Engine in POC scope (current data only) |
