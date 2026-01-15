# Brandpoint Team Handoff Guide

## Intelligence Engine POC - Hub Integration Tasks

**Document Version:** 2.0
**Date:** January 2026
**Prepared by:** Codename 37 (Jake Trippel)
**For:** Brandpoint Development Team (Adam McBroom, Brendan Malone)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Integration Architecture](#integration-architecture)
3. [Timeline & Dependencies](#timeline--dependencies)
4. [Phase 0 Tasks (Week 1)](#phase-0-tasks-week-1---due-december-29-2025)
5. [Phase 4 Tasks (Week 6)](#phase-4-tasks-week-6---due-february-2-2026)
6. [Complete Code Samples](#complete-code-samples)
7. [Testing & Validation](#testing--validation)
8. [FAQ & Troubleshooting](#faq--troubleshooting)
9. [Contacts](#contacts)

---

## Executive Summary

### What We're Building

The Brandpoint Intelligence Engine POC adds AI-powered visibility prediction to the existing Hub platform. This requires minimal changes to Hub (~100 lines of code) while Codename 37 builds the AI platform on AWS.

### Brandpoint's Role

| Phase | Tasks | Effort | Due Date |
|-------|-------|--------|----------|
| Phase 0 | Provide access, create service account | ~2 hours | Dec 29, 2025 |
| Phase 4 | Create 2 tables, add 1 controller | ~4-6 hours | Feb 2, 2026 |
| **Total** | **7 tasks** | **~6-8 hours** | |

### What Codename 37 Handles

- All AWS infrastructure (Lambda, SageMaker, API Gateway, etc.)
- Machine learning model development
- Persona agent system
- Intelligence Engine (vector search, knowledge graph)
- Demo interface
- API development

---

## Integration Architecture

### How Hub and AWS Communicate

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                         INTEGRATION ARCHITECTURE                             │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌────────────────────┐                    ┌────────────────────┐         │
│    │                    │                    │                    │         │
│    │   BRANDPOINT HUB   │◄──────────────────►│   AWS PLATFORM     │         │
│    │   (.NET 4.7.2)     │   HTTPS/REST API   │   (Serverless)     │         │
│    │                    │                    │                    │         │
│    └─────────┬──────────┘                    └─────────┬──────────┘         │
│              │                                         │                     │
│              │                                         │                     │
│    ┌─────────▼──────────┐                    ┌─────────▼──────────┐         │
│    │   SQL Server       │                    │   AWS Services     │         │
│    │   ┌──────────────┐ │                    │   ┌──────────────┐ │         │
│    │   │AiContent     │ │                    │   │ API Gateway  │ │         │
│    │   │Prediction    │ │                    │   │ Lambda       │ │         │
│    │   ├──────────────┤ │                    │   │ SageMaker    │ │         │
│    │   │PersonaQuery  │ │                    │   │ Bedrock      │ │         │
│    │   │Result        │ │                    │   │ DynamoDB     │ │         │
│    │   └──────────────┘ │                    │   │ OpenSearch   │ │         │
│    │   (NEW TABLES)     │                    │   │ Neptune      │ │         │
│    └────────────────────┘                    │   └──────────────┘ │         │
│                                              └────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: User Requests Prediction

```
Step 1: User clicks "Predict Visibility" in Hub UI
        │
        ▼
Step 2: Hub frontend calls AWS API Gateway
        POST https://api.aws.../predict/123
        Headers: { "x-api-key": "aws-api-key" }
        │
        ▼
Step 3: AWS Lambda processes request
        - Extracts features from content
        - Calls SageMaker for ML prediction
        - Generates recommendations
        │
        ▼
Step 4: AWS Lambda stores result in Hub
        POST https://hub.brandpoint.com/api/AiPrediction/predictions
        Headers: { "X-Api-Key": "hub-service-key" }
        Body: { contentId, score, factors, recommendations }
        │
        ▼
Step 5: Hub API (AiPredictionController) saves to SQL Server
        INSERT INTO AiContentPrediction (...)
        │
        ▼
Step 6: Response returned to user with prediction displayed
```

### Data Flow: Persona Agent Execution

```
Step 1: User triggers persona execution
        │
        ▼
Step 2: AWS Step Functions orchestrates:
        - Load persona from DynamoDB
        - Generate queries via Bedrock
        - Execute against ChatGPT, Perplexity, Gemini, Claude
        - Analyze responses for brand mentions
        │
        ▼
Step 3: AWS Lambda stores results in Hub
        POST https://hub.brandpoint.com/api/AiPrediction/persona-results
        Body: { executionId, personaId, results: [...] }
        │
        ▼
Step 4: Hub API saves to SQL Server
        INSERT INTO PersonaQueryResult (...)
```

---

## Timeline & Dependencies

### Dependency Chain

```
WEEK 1 (Phase 0)                    WEEKS 2-5                    WEEK 6 (Phase 4)
─────────────────                   ─────────                    ────────────────

┌─────────────────┐                                             ┌─────────────────┐
│ Staging Access  │─────┐                                       │ Create Tables   │
│ (Brandpoint)    │     │                                       │ (Brandpoint)    │
└─────────────────┘     │                                       └────────┬────────┘
                        │                                                │
┌─────────────────┐     │     ┌─────────────────────────┐               │
│ Service Account │─────┼────►│ Codename 37 builds:     │               │
│ (Brandpoint)    │     │     │ - ML Model              │               │
└─────────────────┘     │     │ - Persona Agents        │               ▼
                        │     │ - Intelligence Engine   │      ┌─────────────────┐
┌─────────────────┐     │     │ - API Layer             │      │ Add Controller  │
│ API Key         │─────┤     └─────────────────────────┘      │ (Brandpoint)    │
│ (Brandpoint)    │     │                                       └────────┬────────┘
└─────────────────┘     │                                                │
                        │                                                ▼
┌─────────────────┐     │                                       ┌─────────────────┐
│ DB Access       │─────┘                                       │ End-to-End Test │
│ (Brandpoint)    │                                             │ (Both Teams)    │
└─────────────────┘                                             └─────────────────┘
```

### Critical Path

**Phase 0 tasks BLOCK all development.** We cannot proceed without:
1. Staging access (to test integration)
2. Service account (for API authentication)
3. API key (for secure communication)
4. Database access (for training data)

---

## Phase 0 Tasks (Week 1) - Due: December 29, 2025

### Task 1: Obtain Staging Environment Access

**GitHub Issue:** [#9](https://github.com/Codename-37/brandpoint_ie_poc/issues/9)
**Priority:** P0 - Critical
**Estimated Effort:** 30 minutes

#### Description

Brandpoint to provide access to staging environment for development and testing.

#### Requirements

| Requirement | Details |
|-------------|---------|
| Staging Hub URL | e.g., `https://staging.hub.brandpoint.com` |
| Network access | VPN credentials OR whitelist Codename 37 IPs |
| Test data | Representative content and client data |

#### Tasks Checklist

- [ ] Identify staging environment details
- [ ] Provide network access to Codename 37
- [ ] Confirm test data is available
- [ ] Document access procedures

#### Acceptance Criteria

- [ ] Codename 37 can access staging Hub via browser
- [ ] Test data is representative of production
- [ ] Access documented for future reference

#### Deliverables to Codename 37

```
Please provide:
1. Staging URL: ________________________
2. Access method: [ ] VPN  [ ] IP Whitelist  [ ] Other
3. VPN credentials (if applicable): ________________________
4. Test account login: ________________________
5. Test data confirmation: [ ] Yes, staging has test data
```

---

### Task 2: Create Service Account in Hub

**GitHub Issue:** [#10](https://github.com/Codename-37/brandpoint_ie_poc/issues/10)
**Priority:** P0 - Critical
**Estimated Effort:** 30 minutes

#### Description

Create a service account in Brandpoint Hub for AWS integration. This account will be used by AWS Lambda functions to authenticate when calling Hub APIs.

#### Requirements

| Requirement | Details |
|-------------|---------|
| Account type | Service account (non-human, API-only) |
| Username | Suggested: `aws-integration-service` |
| Authentication | API key or Bearer token |

#### Required Permissions

```
Service Account Permissions:
├── Content
│   ├── READ: Content data (headlines, body, metadata)
│   ├── READ: Client information
│   └── READ: Campaign data
│
├── AiContentPrediction (new table)
│   ├── CREATE: Insert prediction records
│   └── READ: Query predictions
│
└── PersonaQueryResult (new table)
    ├── CREATE: Insert result records
    └── READ: Query results
```

#### Tasks Checklist

- [ ] Create service account in Hub
- [ ] Configure appropriate permissions (see above)
- [ ] Document account capabilities
- [ ] Provide credentials securely to Codename 37

#### Acceptance Criteria

- [ ] Service account created and active
- [ ] Account can authenticate via API
- [ ] Permissions allow all required operations
- [ ] No unnecessary permissions granted (least privilege)

#### Deliverables to Codename 37

```
Please provide securely (encrypted email, secure file share, or password manager):
1. Service account username: ________________________
2. Authentication method: [ ] API Key  [ ] Bearer Token  [ ] Other
3. Credential value: ________________________
4. Any rate limits: ________________________
```

---

### Task 3: Generate API Key for Service Account

**GitHub Issue:** [#11](https://github.com/Codename-37/brandpoint_ie_poc/issues/11)
**Priority:** P0 - Critical
**Estimated Effort:** 15 minutes

#### Description

Generate an API key for the service account to enable AWS Lambda → Hub API calls.

#### How It Will Be Used

```http
POST /api/AiPrediction/predictions HTTP/1.1
Host: hub.brandpoint.com
X-Api-Key: <API_KEY_HERE>
Content-Type: application/json

{
  "contentId": 12345,
  "predictionScore": 0.72,
  ...
}
```

#### Tasks Checklist

- [ ] Generate API key for service account
- [ ] Securely transmit to Codename 37
- [ ] Document API authentication method
- [ ] Test API connectivity

#### Acceptance Criteria

- [ ] API key generated
- [ ] Key works for authentication
- [ ] Key will be stored in AWS Secrets Manager
- [ ] Lambda can authenticate with Hub API

#### Security Notes

- API key will be stored in AWS Secrets Manager (encrypted at rest)
- Key will only be used by AWS Lambda functions
- Key can be rotated if needed
- Recommend setting expiration and monitoring usage

---

### Task 4: Confirm Database Read Access for ML Training

**GitHub Issue:** [#12](https://github.com/Codename-37/brandpoint_ie_poc/issues/12)
**Priority:** P0 - Critical
**Estimated Effort:** 1 hour

#### Description

Confirm read access to SQL Server databases for extracting training data. We need the AI Monitor results (49K records) to train our ML model.

#### Databases Required

| Database | Purpose | Records |
|----------|---------|---------|
| **ARA3** | AI Monitor results | ~49,000 |
| **MasterTracker** | Content metadata | Reference |
| **Hub database** | Content, clients, campaigns | Reference |

#### Access Method Options

| Option | Pros | Cons | Brandpoint Effort |
|--------|------|------|-------------------|
| **A. VPC Peering + Direct SQL** | Real-time access, secure, can re-query | VPC peering setup | Medium |
| **B. Data Export to S3** | Simple, one-time | Data becomes stale | Low |
| **C. API Endpoints** | Secure, controlled | Development required | High |

**Selected Approach:** Option A (VPC Peering) - enables real-time data access for ML training, content ingestion, and prediction lookups.

**Note:** The AWS CloudFormation templates create a separate VPC (10.100.0.0/16 by default) that requires VPC Peering to access your existing RDS. See **DEPLOYMENT_GUIDE.md** Steps 12-13 for detailed setup instructions.

#### If Option A (VPC Peering) - Selected

AWS Lambda functions requiring database access:
- `feature-extraction` - ML training data extraction
- `content-ingestion` - Article metadata lookup
- `prediction-api` - Content lookup for predictions

See DEPLOYMENT_GUIDE.md Steps 12-13 for VPC Peering and RDS connectivity setup.

#### If Option B (Data Export) - Alternative

For initial ML model training, you may optionally export historical data to CSV or Parquet format:

**Export 1: AI Monitor Results**
```sql
SELECT
    ResultId,
    QueryText,
    ResponseText,
    BrandMentioned,
    Engine,
    WebSearchEnabled,
    ClientId,
    ExecutedAt
FROM AiMonitorResult
WHERE ExecutedAt >= '2024-01-01'
```

**Export 2: Content Data**
```sql
SELECT
    ContentId,
    Headline,
    BodyText,
    PublishDate,
    ClientId,
    PublisherId
FROM Content
WHERE ContentId IN (SELECT DISTINCT ContentId FROM AiMonitorResult)
```

#### Tasks Checklist

- [ ] Decide on access method (A, B, or C)
- [ ] If Option A: Provide connection string, whitelist AWS IPs
- [ ] If Option B: Run exports, upload to S3 bucket (we'll provide)
- [ ] If Option C: Create read-only API endpoint
- [ ] Document available tables and schemas
- [ ] Test data extraction

#### Acceptance Criteria

- [ ] Access method confirmed and documented
- [ ] Codename 37 can extract training data
- [ ] Data quality sufficient for ML (49K+ records)
- [ ] Schema documented for reference

---

## Phase 4 Tasks (Week 6) - Due: February 2, 2026

### Task 5: Create AiContentPrediction Database Table

**GitHub Issue:** [#39](https://github.com/Codename-37/brandpoint_ie_poc/issues/39)
**Priority:** P0 - Critical
**Estimated Effort:** 1 hour

#### Description

Create database table in Hub to store AI visibility predictions. This table stores the output from our ML model.

#### Complete SQL Schema

```sql
-- =====================================================
-- Table: AiContentPrediction
-- Purpose: Store AI visibility predictions from AWS
-- Created: [DATE]
-- Author: Brandpoint Team
-- =====================================================

-- Create the table
CREATE TABLE AiContentPrediction (
    -- Primary key
    PredictionId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),

    -- Foreign key to existing Content table
    ContentId INT NOT NULL,

    -- Prediction scores (0.0000 to 1.0000)
    PredictionScore DECIMAL(5,4) NOT NULL,
    ConfidenceScore DECIMAL(5,4) NOT NULL,

    -- JSON fields for detailed data
    TopFactors NVARCHAR(MAX) NULL,        -- JSON array of contributing factors
    Recommendations NVARCHAR(MAX) NULL,    -- JSON array of recommendations

    -- Metadata
    ModelVersion VARCHAR(20) NULL,         -- e.g., "v1.0.0"
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

    -- Foreign key constraint (adjust table name if different)
    CONSTRAINT FK_AiContentPrediction_Content
        FOREIGN KEY (ContentId) REFERENCES Content(ContentId)
);

-- Index for fast lookups by ContentId
CREATE INDEX IX_AiContentPrediction_ContentId
ON AiContentPrediction(ContentId);

-- Index for querying recent predictions
CREATE INDEX IX_AiContentPrediction_CreatedAt
ON AiContentPrediction(CreatedAt DESC);

-- =====================================================
-- Example JSON structure for TopFactors:
-- [
--   {"name": "query_type", "impact": 0.35, "value": "brand_specific"},
--   {"name": "web_search", "impact": 0.28, "value": true},
--   {"name": "publisher_authority", "impact": 0.15, "value": 0.82}
-- ]
--
-- Example JSON structure for Recommendations:
-- [
--   {"action": "Add specific statistics", "expectedLift": "+12%"},
--   {"action": "Include expert quote", "expectedLift": "+8%"}
-- ]
-- =====================================================
```

#### Tasks Checklist

- [ ] Review schema with DBA
- [ ] Create migration script
- [ ] Apply to staging database
- [ ] Verify foreign key relationship works
- [ ] Test INSERT operation
- [ ] Test SELECT operation
- [ ] Apply to production (post-POC)

#### Acceptance Criteria

- [ ] Table created in staging database
- [ ] Foreign key to Content table works
- [ ] AWS Lambda can INSERT records
- [ ] Hub can SELECT records for display
- [ ] Existing Hub code unaffected

#### Verification Query

```sql
-- Run this after creating table to verify
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'AiContentPrediction'
ORDER BY ORDINAL_POSITION;
```

---

### Task 6: Create PersonaQueryResult Database Table

**GitHub Issue:** [#40](https://github.com/Codename-37/brandpoint_ie_poc/issues/40)
**Priority:** P0 - Critical
**Estimated Effort:** 1 hour

#### Description

Create database table in Hub to store persona agent execution results. This table stores the results of our persona-based queries against AI engines.

#### Complete SQL Schema

```sql
-- =====================================================
-- Table: PersonaQueryResult
-- Purpose: Store persona agent execution results from AWS
-- Created: [DATE]
-- Author: Brandpoint Team
-- =====================================================

-- Create the table
CREATE TABLE PersonaQueryResult (
    -- Primary key
    ResultId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),

    -- Execution grouping (all results from one run share this)
    ExecutionId UNIQUEIDENTIFIER NOT NULL,

    -- Persona identification
    PersonaId VARCHAR(100) NOT NULL,       -- e.g., "us-army-prospect-male-18-24"

    -- Query details
    QueryText NVARCHAR(500) NOT NULL,      -- The generated query
    Engine VARCHAR(50) NOT NULL,           -- chatgpt, perplexity, gemini, claude

    -- Response details
    ResponseText NVARCHAR(MAX) NULL,       -- Full AI response (can be large)
    BrandMentioned BIT NOT NULL,           -- Was the brand mentioned?
    VisibilityScore DECIMAL(5,4) NULL,     -- 0.0000 to 1.0000

    -- Timestamps
    ExecutedAt DATETIME2 NOT NULL,         -- When the query was executed
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

-- Index for querying by persona
CREATE INDEX IX_PersonaQueryResult_PersonaId
ON PersonaQueryResult(PersonaId);

-- Index for querying by execution (get all results from one run)
CREATE INDEX IX_PersonaQueryResult_ExecutionId
ON PersonaQueryResult(ExecutionId);

-- Index for querying by engine
CREATE INDEX IX_PersonaQueryResult_Engine
ON PersonaQueryResult(Engine);

-- Index for time-based queries
CREATE INDEX IX_PersonaQueryResult_ExecutedAt
ON PersonaQueryResult(ExecutedAt DESC);

-- =====================================================
-- Example data:
-- ResultId: 'a1b2c3d4-...'
-- ExecutionId: 'exec-12345-...'  (shared by all queries in one run)
-- PersonaId: 'us-army-prospect-male-18-24'
-- QueryText: 'is joining the army worth it in 2025'
-- Engine: 'chatgpt'
-- ResponseText: 'The US Army offers several benefits...'
-- BrandMentioned: 1 (true)
-- VisibilityScore: 0.8500
-- ExecutedAt: '2025-12-22 10:30:00'
-- =====================================================
```

#### Tasks Checklist

- [ ] Review schema with DBA
- [ ] Create migration script
- [ ] Apply to staging database
- [ ] Test INSERT operation (single record)
- [ ] Test INSERT operation (batch - multiple records)
- [ ] Test SELECT by PersonaId
- [ ] Test SELECT by ExecutionId
- [ ] Apply to production (post-POC)

#### Acceptance Criteria

- [ ] Table created in staging database
- [ ] AWS Lambda can INSERT records (single and batch)
- [ ] Hub can SELECT records for display
- [ ] Query by persona works efficiently
- [ ] Query by execution works efficiently

#### Verification Query

```sql
-- Run this after creating table to verify
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'PersonaQueryResult'
ORDER BY ORDINAL_POSITION;
```

---

### Task 7: Add AiPredictionController to Hub API

**GitHub Issue:** [#41](https://github.com/Codename-37/brandpoint_ie_poc/issues/41)
**Priority:** P0 - Critical
**Estimated Effort:** 2-3 hours

#### Description

Add minimal API controller to Hub for receiving predictions from AWS. This is the only code change required in Hub.

#### Files to Create

```
Hub/
├── Api/
│   └── AiPredictionController.cs    (NEW - ~80 lines)
│
└── Models/
    └── AiPredictionModels.cs        (NEW - ~60 lines)
```

#### Total Lines of Code: ~140 lines

---

## Complete Code Samples

### File 1: AiPredictionController.cs

```csharp
// =====================================================
// File: Api/AiPredictionController.cs
// Purpose: API endpoints for AWS Lambda to store AI predictions
// Author: Brandpoint Team
// Created: [DATE]
// =====================================================

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using YourNamespace.Models;  // Adjust to your namespace

namespace YourNamespace.Api  // Adjust to your namespace
{
    [ApiController]
    [Route("api/[controller]")]
    [Authorize]  // Uses existing Hub authentication
    public class AiPredictionController : ControllerBase
    {
        private readonly YourDbContext _db;  // Adjust to your DbContext class
        private readonly ILogger<AiPredictionController> _logger;

        public AiPredictionController(
            YourDbContext db,
            ILogger<AiPredictionController> logger)
        {
            _db = db;
            _logger = logger;
        }

        // ─────────────────────────────────────────────────────────
        // POST: /api/AiPrediction/predictions
        // Purpose: AWS Lambda calls this to store prediction results
        // ─────────────────────────────────────────────────────────
        [HttpPost("predictions")]
        public async Task<IActionResult> StorePrediction(
            [FromBody] StorePredictionRequest request)
        {
            try
            {
                // Validate request
                if (request.ContentId <= 0)
                {
                    return BadRequest(new { error = "Invalid ContentId" });
                }

                // Create prediction record
                var prediction = new AiContentPrediction
                {
                    PredictionId = Guid.NewGuid(),
                    ContentId = request.ContentId,
                    PredictionScore = request.PredictionScore,
                    ConfidenceScore = request.ConfidenceScore,
                    TopFactors = request.TopFactors != null
                        ? JsonSerializer.Serialize(request.TopFactors)
                        : null,
                    Recommendations = request.Recommendations != null
                        ? JsonSerializer.Serialize(request.Recommendations)
                        : null,
                    ModelVersion = request.ModelVersion,
                    CreatedAt = DateTime.UtcNow
                };

                // Save to database
                await _db.AiContentPredictions.AddAsync(prediction);
                await _db.SaveChangesAsync();

                _logger.LogInformation(
                    "Stored prediction {PredictionId} for content {ContentId}",
                    prediction.PredictionId,
                    prediction.ContentId);

                return Ok(new
                {
                    predictionId = prediction.PredictionId,
                    message = "Prediction stored successfully"
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to store prediction for content {ContentId}",
                    request.ContentId);
                return StatusCode(500, new { error = "Failed to store prediction" });
            }
        }

        // ─────────────────────────────────────────────────────────
        // GET: /api/AiPrediction/predictions/{contentId}
        // Purpose: Retrieve predictions for a specific content item
        // ─────────────────────────────────────────────────────────
        [HttpGet("predictions/{contentId}")]
        public async Task<IActionResult> GetPredictions(int contentId)
        {
            try
            {
                var predictions = await _db.AiContentPredictions
                    .Where(p => p.ContentId == contentId)
                    .OrderByDescending(p => p.CreatedAt)
                    .Select(p => new
                    {
                        p.PredictionId,
                        p.ContentId,
                        p.PredictionScore,
                        p.ConfidenceScore,
                        TopFactors = p.TopFactors != null
                            ? JsonSerializer.Deserialize<List<TopFactor>>(p.TopFactors)
                            : null,
                        Recommendations = p.Recommendations != null
                            ? JsonSerializer.Deserialize<List<Recommendation>>(p.Recommendations)
                            : null,
                        p.ModelVersion,
                        p.CreatedAt
                    })
                    .ToListAsync();

                return Ok(predictions);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to get predictions for content {ContentId}",
                    contentId);
                return StatusCode(500, new { error = "Failed to retrieve predictions" });
            }
        }

        // ─────────────────────────────────────────────────────────
        // POST: /api/AiPrediction/persona-results
        // Purpose: AWS Lambda calls this to store persona execution results
        // ─────────────────────────────────────────────────────────
        [HttpPost("persona-results")]
        public async Task<IActionResult> StorePersonaResults(
            [FromBody] StorePersonaResultsRequest request)
        {
            try
            {
                // Validate request
                if (string.IsNullOrEmpty(request.PersonaId))
                {
                    return BadRequest(new { error = "PersonaId is required" });
                }

                if (request.Results == null || !request.Results.Any())
                {
                    return BadRequest(new { error = "Results array is required" });
                }

                // Create result records
                var results = request.Results.Select(r => new PersonaQueryResult
                {
                    ResultId = Guid.NewGuid(),
                    ExecutionId = request.ExecutionId,
                    PersonaId = request.PersonaId,
                    QueryText = r.QueryText,
                    Engine = r.Engine,
                    ResponseText = r.ResponseText,
                    BrandMentioned = r.BrandMentioned,
                    VisibilityScore = r.VisibilityScore,
                    ExecutedAt = r.ExecutedAt,
                    CreatedAt = DateTime.UtcNow
                }).ToList();

                // Batch insert
                await _db.PersonaQueryResults.AddRangeAsync(results);
                await _db.SaveChangesAsync();

                _logger.LogInformation(
                    "Stored {Count} persona results for execution {ExecutionId}",
                    results.Count,
                    request.ExecutionId);

                return Ok(new
                {
                    executionId = request.ExecutionId,
                    count = results.Count,
                    message = "Results stored successfully"
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to store persona results for execution {ExecutionId}",
                    request.ExecutionId);
                return StatusCode(500, new { error = "Failed to store results" });
            }
        }

        // ─────────────────────────────────────────────────────────
        // GET: /api/AiPrediction/persona-results/{personaId}
        // Purpose: Retrieve results for a specific persona
        // ─────────────────────────────────────────────────────────
        [HttpGet("persona-results/{personaId}")]
        public async Task<IActionResult> GetPersonaResults(
            string personaId,
            [FromQuery] int limit = 100)
        {
            try
            {
                var results = await _db.PersonaQueryResults
                    .Where(r => r.PersonaId == personaId)
                    .OrderByDescending(r => r.ExecutedAt)
                    .Take(limit)
                    .ToListAsync();

                // Calculate aggregate visibility
                var aggregateVisibility = results.Any()
                    ? results.Average(r => r.BrandMentioned ? 1.0 : 0.0)
                    : 0.0;

                return Ok(new
                {
                    personaId,
                    totalResults = results.Count,
                    aggregateVisibility,
                    results
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to get results for persona {PersonaId}",
                    personaId);
                return StatusCode(500, new { error = "Failed to retrieve results" });
            }
        }
    }
}
```

### File 2: AiPredictionModels.cs

```csharp
// =====================================================
// File: Models/AiPredictionModels.cs
// Purpose: Request/Response models for AI Prediction API
// Author: Brandpoint Team
// Created: [DATE]
// =====================================================

using System;
using System.Collections.Generic;

namespace YourNamespace.Models  // Adjust to your namespace
{
    // ─────────────────────────────────────────────────────────
    // Request Models
    // ─────────────────────────────────────────────────────────

    /// <summary>
    /// Request to store a prediction result from AWS
    /// </summary>
    public class StorePredictionRequest
    {
        public int ContentId { get; set; }
        public decimal PredictionScore { get; set; }
        public decimal ConfidenceScore { get; set; }
        public List<TopFactor> TopFactors { get; set; }
        public List<Recommendation> Recommendations { get; set; }
        public string ModelVersion { get; set; }
    }

    /// <summary>
    /// A factor contributing to the visibility prediction
    /// </summary>
    public class TopFactor
    {
        public string Name { get; set; }
        public decimal Impact { get; set; }
        public object Value { get; set; }
    }

    /// <summary>
    /// A recommendation to improve visibility
    /// </summary>
    public class Recommendation
    {
        public string Action { get; set; }
        public string ExpectedLift { get; set; }
        public string Priority { get; set; }
    }

    /// <summary>
    /// Request to store persona execution results from AWS
    /// </summary>
    public class StorePersonaResultsRequest
    {
        public Guid ExecutionId { get; set; }
        public string PersonaId { get; set; }
        public List<PersonaResultItem> Results { get; set; }
    }

    /// <summary>
    /// A single query result from persona execution
    /// </summary>
    public class PersonaResultItem
    {
        public string QueryText { get; set; }
        public string Engine { get; set; }
        public string ResponseText { get; set; }
        public bool BrandMentioned { get; set; }
        public decimal? VisibilityScore { get; set; }
        public DateTime ExecutedAt { get; set; }
    }

    // ─────────────────────────────────────────────────────────
    // Entity Models (for Entity Framework)
    // ─────────────────────────────────────────────────────────

    /// <summary>
    /// Entity: AI Content Prediction stored in database
    /// </summary>
    public class AiContentPrediction
    {
        public Guid PredictionId { get; set; }
        public int ContentId { get; set; }
        public decimal PredictionScore { get; set; }
        public decimal ConfidenceScore { get; set; }
        public string TopFactors { get; set; }      // JSON string
        public string Recommendations { get; set; } // JSON string
        public string ModelVersion { get; set; }
        public DateTime CreatedAt { get; set; }
    }

    /// <summary>
    /// Entity: Persona Query Result stored in database
    /// </summary>
    public class PersonaQueryResult
    {
        public Guid ResultId { get; set; }
        public Guid ExecutionId { get; set; }
        public string PersonaId { get; set; }
        public string QueryText { get; set; }
        public string Engine { get; set; }
        public string ResponseText { get; set; }
        public bool BrandMentioned { get; set; }
        public decimal? VisibilityScore { get; set; }
        public DateTime ExecutedAt { get; set; }
        public DateTime CreatedAt { get; set; }
    }
}
```

### File 3: DbContext Addition

```csharp
// =====================================================
// Add to your existing DbContext class
// =====================================================

public class YourDbContext : DbContext  // Your existing DbContext
{
    // ... existing DbSets ...

    // Add these two lines:
    public DbSet<AiContentPrediction> AiContentPredictions { get; set; }
    public DbSet<PersonaQueryResult> PersonaQueryResults { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // ... existing configurations ...

        // Add these configurations:
        modelBuilder.Entity<AiContentPrediction>(entity =>
        {
            entity.ToTable("AiContentPrediction");
            entity.HasKey(e => e.PredictionId);
            entity.Property(e => e.PredictionScore).HasColumnType("decimal(5,4)");
            entity.Property(e => e.ConfidenceScore).HasColumnType("decimal(5,4)");
        });

        modelBuilder.Entity<PersonaQueryResult>(entity =>
        {
            entity.ToTable("PersonaQueryResult");
            entity.HasKey(e => e.ResultId);
            entity.Property(e => e.VisibilityScore).HasColumnType("decimal(5,4)");
        });
    }
}
```

---

## Tasks Checklist for Controller

- [ ] Create `Models/AiPredictionModels.cs`
- [ ] Create `Api/AiPredictionController.cs`
- [ ] Add DbSets to DbContext
- [ ] Add model configurations to OnModelCreating
- [ ] Register controller in Startup.cs (if needed)
- [ ] Test POST /api/AiPrediction/predictions
- [ ] Test GET /api/AiPrediction/predictions/{contentId}
- [ ] Test POST /api/AiPrediction/persona-results
- [ ] Test GET /api/AiPrediction/persona-results/{personaId}
- [ ] Deploy to staging

## Acceptance Criteria

- [ ] All 4 endpoints respond correctly
- [ ] POST endpoints accept requests from AWS Lambda
- [ ] Data persisted to database tables
- [ ] GET endpoints return stored data
- [ ] Authentication works (service account can access)
- [ ] No impact on existing Hub functionality
- [ ] Error handling returns appropriate status codes

---

## Testing & Validation

### Test 1: Store Prediction

```bash
# Using curl (replace with your staging URL and API key)
curl -X POST https://staging.hub.brandpoint.com/api/AiPrediction/predictions \
  -H "X-Api-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contentId": 12345,
    "predictionScore": 0.72,
    "confidenceScore": 0.85,
    "topFactors": [
      {"name": "query_type", "impact": 0.35, "value": "brand_specific"}
    ],
    "recommendations": [
      {"action": "Add statistics", "expectedLift": "+12%"}
    ],
    "modelVersion": "v1.0.0"
  }'

# Expected response:
# {"predictionId": "...", "message": "Prediction stored successfully"}
```

### Test 2: Get Predictions

```bash
curl -X GET https://staging.hub.brandpoint.com/api/AiPrediction/predictions/12345 \
  -H "X-Api-Key: YOUR_API_KEY"

# Expected response:
# [{"predictionId": "...", "contentId": 12345, "predictionScore": 0.72, ...}]
```

### Test 3: Store Persona Results

```bash
curl -X POST https://staging.hub.brandpoint.com/api/AiPrediction/persona-results \
  -H "X-Api-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "executionId": "550e8400-e29b-41d4-a716-446655440000",
    "personaId": "us-army-prospect-male-18-24",
    "results": [
      {
        "queryText": "is joining the army worth it in 2025",
        "engine": "chatgpt",
        "responseText": "The US Army offers...",
        "brandMentioned": true,
        "visibilityScore": 0.85,
        "executedAt": "2025-12-22T10:30:00Z"
      }
    ]
  }'

# Expected response:
# {"executionId": "...", "count": 1, "message": "Results stored successfully"}
```

### Test 4: Verify Data in Database

```sql
-- Check predictions
SELECT TOP 10 * FROM AiContentPrediction ORDER BY CreatedAt DESC;

-- Check persona results
SELECT TOP 10 * FROM PersonaQueryResult ORDER BY CreatedAt DESC;
```

---

## FAQ & Troubleshooting

### Q: What if we use a different authentication method?

The controller uses `[Authorize]` which hooks into your existing auth. If you use a different method (e.g., API key header), adjust the attribute:

```csharp
// Option: Custom API key authentication
[ApiKeyAuth]  // Your custom attribute
public class AiPredictionController : ControllerBase
```

### Q: What if our Content table has a different name?

Adjust the foreign key in the SQL schema:

```sql
CONSTRAINT FK_AiContentPrediction_Content
    FOREIGN KEY (ContentId) REFERENCES YourContentTable(YourContentIdColumn)
```

### Q: What if we don't use Entity Framework?

Replace the EF code with your data access pattern (Dapper, ADO.NET, etc.):

```csharp
// Example with Dapper
await connection.ExecuteAsync(
    "INSERT INTO AiContentPrediction (...) VALUES (...)",
    prediction);
```

### Q: What about CORS?

If the Hub UI needs to call these endpoints directly, add CORS:

```csharp
[EnableCors("AllowHub")]
public class AiPredictionController : ControllerBase
```

### Q: How do we monitor these endpoints?

Add logging (already included in the code) and consider:
- Application Insights for Azure
- CloudWatch for AWS-side monitoring
- Custom metrics in your existing monitoring

---

## Contacts

### Codename 37 Team

| Name | Role | Contact |
|------|------|---------|
| Jake Trippel | Technical Lead | jake@codename37.com |
| Michael Brendon | Project Lead | michael@codename37.com |

### Brandpoint Team

| Name | Role | Responsibility |
|------|------|----------------|
| Adam McBroom | Technology SME | Phase 0 tasks, technical decisions |
| Brendan Malone | Technology SME | Code implementation, testing |
| Stacy Stusynski | Strategy | Requirements validation |
| Libby Schulzetenberg | Product | Acceptance testing |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-22 | Jake Trippel / Claude | Initial handoff guide |
| 2.0 | 2026-01 | Jake Trippel / Claude | Updated auth header to X-Api-Key, added VPC Peering for RDS access |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    BRANDPOINT QUICK REFERENCE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PHASE 0 (Week 1 - Due Dec 29)        PHASE 4 (Week 6 - Due Feb 2)
│  ─────────────────────────────        ───────────────────────────│
│  □ Staging access                     □ AiContentPrediction table│
│  □ Service account                    □ PersonaQueryResult table │
│  □ API key                            □ AiPredictionController   │
│  □ Database access                                               │
│                                                                  │
│  TOTAL EFFORT: ~6-8 hours                                        │
│  TOTAL CODE: ~140 lines                                          │
│                                                                  │
│  ENDPOINTS TO CREATE:                                            │
│  ────────────────────                                            │
│  POST /api/AiPrediction/predictions                              │
│  GET  /api/AiPrediction/predictions/{contentId}                  │
│  POST /api/AiPrediction/persona-results                          │
│  GET  /api/AiPrediction/persona-results/{personaId}              │
│                                                                  │
│  QUESTIONS? Contact jake@codename37.com                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
