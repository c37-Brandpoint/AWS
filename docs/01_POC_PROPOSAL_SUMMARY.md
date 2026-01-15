# POC Proposal Summary

## Source Document

`Brandpoint Proposalv4_November 24 2025 (1).pdf` - 33 pages

---

## Executive Summary

### The Product: AI Visibility Predictor

A machine learning system that predicts whether Brandpoint's distributed content will appear in AI-powered search results (ChatGPT, Perplexity, Claude, Gemini, Copilot).

### Investment & Timeline

| Item | Value |
|------|-------|
| POC Investment | $60,000 |
| AWS Infrastructure | ~$1,500/month |
| Total POC Cost | ~$61,500 |
| Timeline | 6-8 weeks |
| Phase 1 | December 2025 |
| Phase 2 | January 2026 |

### Risk-Adjusted Revenue Potential

| Scenario | Probability | Revenue | Risk-Adjusted |
|----------|-------------|---------|---------------|
| Conservative | 40% | $300K | $120K |
| Moderate | 35% | $600K | $210K |
| Aggressive | 25% | $1.2M | $300K |
| **Expected Value** | - | - | **$630K** |

---

## The Problem Statement

### Traditional Search is Dying

- AI chatbots are replacing Google for many queries
- ChatGPT alone has 81% of AI search market share
- Users get answers directly from AI, never visiting websites
- Traditional SEO metrics (rankings, clicks) becoming irrelevant

### Brands Are Invisible to AI

From Brandpoint's 49,000 AI response analysis:
- **77% of AI responses mention NO brands**
- Only 23% of responses include any brand mention
- Competitors rarely "win" - the real competition is irrelevance

### No One Measures This

- Traditional analytics don't track AI visibility
- Brands don't know if their content appears in AI responses
- No tools exist to predict AI visibility before publishing

---

## The Solution

### Dual Insight Engine

**1. Pre-Release Insight (Before Publishing)**

```
Content Draft → AI Visibility Predictor → Prediction Score
                                        → Top Influencing Factors
                                        → Optimization Recommendations
```

Value: Optimize content BEFORE it goes live

**2. Post-Release Insight (After AI Responses)**

```
Published Content → AI Monitor → AI Responses Collected
                              → Visibility Measured
                              → Factors Explained
```

Value: Learn WHY content appeared (or didn't)

### Persona-Based Agent System (NEW ENHANCEMENT)

**The Generic Query Problem:**
Current AI Monitor uses generic prompts that don't reflect real user behavior:
- "What are the benefits of military service?" → 0% visibility
- Real 18-24 year olds ask: "is the army worth it if i don't want college debt"

**The Persona Solution:**
Create intelligent agents that simulate actual target audience personas:

```
Persona Definition → Query Generator (Claude) → Realistic Queries → Multi-Engine Execution
        ↓                                              ↓
  "18-24 male,                               "is joining the army worth it in 2025"
   considering military,                      "army vs marines which is better"
   uses TikTok,                               "what jobs in the army don't see combat"
   informal speech"
```

| Client | Target Persona | Persona-Generated Query |
|--------|---------------|------------------------|
| US Army | 18-24 male, HS senior | "is the army a good career if i hate school" |
| United Healthcare | 65 female, pre-Medicare | "turning 65 do i need to sign up for medicare" |
| Myrtle Beach | 45 couple, midwest | "beach trip with teenagers that won't break the bank" |
| HP | 35 IT manager | "best business laptops for remote workers 2025" |

**Why This Matters:**
- Generic queries: 0-13% visibility
- Brand-in-query: 100% visibility
- Persona queries: Match how REAL customers ask → dramatically higher relevance

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE ENGINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  INPUT: Content Features                                     │
│  ├── Text content (headline, body, structure)               │
│  ├── Publisher characteristics (domain authority, crawl)    │
│  ├── Query alignment (topic, intent, keywords)              │
│  ├── Entity strength (brand recognition, Wikipedia, etc.)   │
│  └── Historical performance (prior visibility rates)        │
│                                                              │
│  MODEL: Transformer-Based Classifier                         │
│  ├── Supervised learning on labeled visibility data         │
│  ├── Fine-tuned on Brandpoint's domain                      │
│  └── Continuous learning from new results                   │
│                                                              │
│  OUTPUT: Prediction                                          │
│  ├── Visibility Score (0-100%)                              │
│  ├── Confidence Level                                        │
│  ├── Top 5 Influencing Factors                              │
│  └── Actionable Recommendations                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Success Criteria

### Primary Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Absolute Accuracy** | ≥65% | Correct predictions / Total predictions |
| **Lift Over Baseline** | ≥15 points | Model accuracy - Random baseline |
| **Statistical Significance** | 95% CI | Confidence interval on metrics |

### Why These Targets?

- **65% accuracy** is achievable and commercially valuable
- **15-point lift** proves the model adds real value over guessing
- **95% confidence** ensures results aren't due to chance

### Baseline Comparison

| Approach | Expected Accuracy |
|----------|-------------------|
| Random guess | ~23% (class distribution) |
| Simple heuristics | ~35-40% |
| **Our model target** | **≥65%** |

---

## Technical Approach

### Phase 1: Foundation (December 2025)

**Data Pipeline**
- Extract features from HubContent, Article, AiMonitorResult
- Build training dataset with visibility labels
- Implement feature engineering pipeline

**Model Development**
- Train baseline models (logistic regression, random forest)
- Develop transformer-based classifier
- Evaluate against success criteria

**Infrastructure**
- AWS deployment (matches Brandpoint's stack)
- API endpoints for prediction requests
- Integration hooks for Hub

### Phase 2: Integration (January 2026)

**Hub Integration**
- REST API connection to legacy Hub
- Prediction display in Hub UI
- Pre-publish workflow integration

**Demo Interface**
- Standalone prediction interface
- Results visualization
- Recommendation display

**Documentation**
- Technical documentation
- API specifications
- Accuracy report

---

## Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 1 | Working ML Model | Trained, validated visibility predictor |
| 2 | API Endpoints | REST API for prediction requests |
| 3 | Demo Interface | UI for demonstrating predictions |
| 4 | Accuracy Report | Model performance documentation |
| 5 | Integration Spec | How to connect with Hub |
| 6 | Training Pipeline | Reproducible model training |
| 7 | Deployment Guide | AWS infrastructure setup |
| 8 | Recommendations | Post-POC roadmap |

---

## Feature Categories

### Content Features

| Feature | Source | Importance |
|---------|--------|------------|
| Headline text | HubContent | High |
| Body content | HubContent | High |
| Content length | Calculated | Medium |
| Structure (headers, lists) | Parsed | Medium |
| Readability score | Calculated | Medium |

### Publisher Features

| Feature | Source | Importance |
|---------|--------|------------|
| Domain authority | External API | High |
| AI crawlability | robots.txt check | Critical |
| Historical visibility | AiMonitorResult | High |
| Publisher tier | Article metadata | Medium |

### Query Features

| Feature | Source | Importance |
|---------|--------|------------|
| Query type | Classification | Critical |
| Brand inclusion | Text match | Critical |
| Topic alignment | Semantic similarity | High |
| Intent category | Classification | Medium |

### Entity Features

| Feature | Source | Importance |
|---------|--------|------------|
| Wikipedia presence | External check | High |
| Wikidata entity | External check | High |
| Knowledge Graph | External check | Medium |
| Brand search volume | External API | Medium |

---

## Risk Factors

### Technical Risks

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Insufficient training data | Low | 49K labeled examples available |
| Model underperformance | Medium | Multiple model architectures, ensemble |
| Integration complexity | Medium | Minimal Hub changes, API-first |

### Business Risks

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Changing AI algorithms | High | Continuous monitoring, retraining |
| Client adoption | Medium | Strong demo, clear value prop |
| Competitive response | Medium | First-mover advantage |

---

## Post-POC Vision

### Immediate (Q1 2026)
- Production deployment
- Client pilot program
- Feedback collection

### Near-term (Q2-Q3 2026)
- Multi-engine expansion (all AI platforms)
- Real-time optimization suggestions
- Automated content scoring

### Long-term (2027+)
- Predictive content generation
- Competitive intelligence
- Industry benchmarking

---

## Investment Justification

### POC Cost: $60,000 + $1,500/month AWS

### Potential Return

| Scenario | Year 1 Revenue | ROI |
|----------|----------------|-----|
| Conservative | $300,000 | 387% |
| Moderate | $600,000 | 874% |
| Aggressive | $1,200,000 | 1,848% |

### Strategic Value

1. **Market Leadership** - First GEO measurement platform
2. **Client Retention** - Unique value proposition
3. **New Revenue** - AI optimization services
4. **Competitive Moat** - Proprietary training data

---

## Key Assumptions

1. AI Monitor data (49K records) is representative of future patterns
2. Brandpoint can obtain client consent for AI training
3. AI platforms don't dramatically change citation behavior
4. Hub integration can be accomplished with minimal changes
5. AWS infrastructure is approved and accessible

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-22 | Jake Trippel / Claude | Initial summary from proposal |
| 1.1 | 2025-12-22 | Jake Trippel / Claude | Added persona-based agent system enhancement |
