# Repository Validation Report

**Date:** 2026-01-21
**Investigator:** Claude (codename37)
**Purpose:** Validate repo assumptions against actual AWS Brandpoint environment

---

## Executive Summary

The repo was created "flying blind" without access to the actual AWS environment. Now that we have access, this report documents mismatches and issues that need attention.

### Issue Summary

| Severity | Count | Category |
|----------|-------|----------|
| **CRITICAL** | 3 | Must fix before deployment |
| **HIGH** | 3 | Must fix for full functionality |
| **MEDIUM** | 2 | Should fix, has workarounds |
| **LOW** | 2 | Nice to have |

---

## CRITICAL Issues (Must Fix)

### 1. Hub Staging URL Does Not Exist

**File:** `infrastructure/cloudformation/parameters/dev.json` (line 24)

**Problem:**
```json
"ParameterValue": "https://hub-staging.brandpoint.com"
```

**Reality:**
```
$ host hub-staging.brandpoint.com
Host hub-staging.brandpoint.com not found: 3(NXDOMAIN)
```

**Impact:** Lambda functions will fail when trying to store predictions/results to Hub API.

**Evidence:**
- `hub-staging.brandpoint.com` → DNS NXDOMAIN (does not exist)
- `hub.brandpoint.com` → Resolves correctly (302 redirect)

**Files Affected:**
- `infrastructure/cloudformation/parameters/dev.json`

**Recommendation:**
- Ask Brandpoint if there IS a staging environment URL
- If not, use `https://hub.brandpoint.com` for dev (with caution)
- Or create a mock endpoint for dev testing

---

### 2. Lambda Security Group CIDR Mismatch for RDS

**File:** `infrastructure/cloudformation/00-foundation.yaml` (line 222)

**Problem:**
```yaml
SecurityGroupEgress:
  - IpProtocol: tcp
    FromPort: 1433
    ToPort: 1433
    CidrIp: 10.0.0.0/8  # <-- WRONG!
```

**Reality:**
```
Existing RDS VPC CIDR: 172.30.0.0/16
RDS Endpoint: brandpointdb.c5rp85tg25on.us-east-1.rds.amazonaws.com:1433
```

**Impact:** Lambda functions cannot connect to RDS for ML training data extraction.

**Why it's wrong:** The egress rule allows outbound traffic to `10.0.0.0/8`, but the existing RDS is in `172.30.0.0/16`. Even after VPC peering, Lambda won't be able to reach the RDS.

**Recommendation:**
Change line 222 from:
```yaml
CidrIp: 10.0.0.0/8
```
To:
```yaml
CidrIp: 172.30.0.0/16
```

---

### 3. RDS Security Group Must Be Updated

**Current RDS Security Group (sg-5f91623b) allows only:**

| Source | Port | Description |
|--------|------|-------------|
| 172.30.0.153/32 | 1433 | Internal server |
| 172.30.0.251/32 | 1433 | Internal server |
| 172.30.0.91/32 | 1433 | Internal server |
| 23.20.101.74/32 | 1433 | Metabase |
| 23.21.230.73/32 | 0-65535 | External |
| 50.253.86.25/32 | 0-65535 | External |

**Missing:** No rule for the new VPC CIDR (10.x.x.x)

**Impact:** Even after VPC peering, Lambda cannot reach RDS.

**Recommendation:**
After VPC peering is established, add to RDS security group:
```
Source: 10.200.0.0/16 (or whatever CIDR is used)
Port: 1433
Protocol: TCP
Description: Brandpoint AI Lambda access
```

---

## HIGH Issues (Must Fix for Functionality)

### 4. Bedrock Model Agreement Not Accepted

**Problem:**
```json
{
  "modelId": "anthropic.claude-3-sonnet-20240229-v1",
  "agreementAvailability": {
    "status": "NOT_AVAILABLE"
  }
}
```

**Impact:** Lambda functions using Bedrock Claude will fail with access denied.

**Recommendation:**
1. Go to AWS Console → Bedrock → Model Access
2. Request access to:
   - `anthropic.claude-3-5-sonnet-20241022-v2:0`
   - `amazon.titan-embed-text-v2:0`
   - Other Claude models as needed
3. Accept the End User License Agreement (EULA)

---

### 5. S3 Templates Bucket Contains Old Buggy Code

**Problem:** Already documented in DEPLOYMENT-BARRIERS-REPORT.md

```
s3://brandpoint-ai-dev-templates-144105412483/cloudformation/05-api.yaml
→ Still has: DependsOn: APIDeployment (bug)
→ Should be: DependsOn: APIStage (fix)
```

**Impact:** Deployment will fail until deploy.sh syncs the fixed templates.

**Resolution:** Automatic when IT team runs deploy.sh after git pull.

---

### 6. Secrets Have Placeholder Values

**File:** `infrastructure/cloudformation/07-secrets.yaml`

**Secrets requiring manual configuration after deployment:**

| Secret Name | Current Value | Required |
|-------------|---------------|----------|
| `brandpoint-ai-dev-openai-api-key` | PLACEHOLDER | OpenAI API key |
| `brandpoint-ai-dev-perplexity-api-key` | PLACEHOLDER | Perplexity API key |
| `brandpoint-ai-dev-gemini-api-key` | PLACEHOLDER | Google Gemini API key |
| `brandpoint-ai-dev-hub-service-account-key` | PLACEHOLDER | Hub service account |
| `brandpoint-ai-dev-ara3-database-readonly` | PLACEHOLDER | RDS connection string |

**ARA3 Database Secret needs real values:**
```json
{
  "host": "brandpointdb.c5rp85tg25on.us-east-1.rds.amazonaws.com",
  "port": "1433",
  "database": "ARA3",
  "username": "ACTUAL_READONLY_USER",
  "password": "ACTUAL_PASSWORD",
  "driver": "ODBC Driver 17 for SQL Server"
}
```

---

## MEDIUM Issues (Should Fix)

### 7. Elastic IP Quota is Tight

**Current State:**
| Quota | Used | Available | Needed |
|-------|------|-----------|--------|
| 5 | 3 | 2 | 1 |

**Risk:** If deployment fails and retries, orphaned EIPs could block future attempts.

**Recommendation:** Request quota increase to 10 before production deployment.

---

### 8. Orphaned CloudWatch Log Group

**Resource:** `/aws/sagemaker/Endpoints/brandpoint-ai-dev-visibility-predictor`

**Impact:** None (CloudFormation will handle it)

**Recommendation:** Optional cleanup after successful deployment.

---

## LOW Issues (Nice to Have)

### 9. Template Bucket Name Mismatch in Parameters

**File:** `infrastructure/cloudformation/parameters/dev.json`

```json
"ParameterKey": "TemplatesBucket",
"ParameterValue": "brandpoint-ai-dev-templates"
```

**Reality:** Actual bucket is `brandpoint-ai-dev-templates-144105412483`

**Why it's OK:** The `deploy.sh` script correctly appends the account ID, so this works. But it's confusing.

---

### 10. Documentation Mentions Non-Existent Staging URL

**Files:**
- `docs/integration/BRANDPOINT_HANDOFF_GUIDE.md` (line 196)
- Various places reference `https://staging.hub.brandpoint.com`

**Recommendation:** Update documentation to reflect reality.

---

## What's Correct (No Changes Needed)

### VPC CIDR Configuration ✓
- Template defaults to `10.100.0.0/16`
- Deploy script auto-selects safe CIDR (10.200.0.0/16)
- No overlap with existing `172.30.0.0/16`

### Service Quotas ✓
| Service | Quota | Required | Status |
|---------|-------|----------|--------|
| VPCs | 5 | 1 | ✓ OK (4 available) |
| Lambda Concurrent | 1000 | 15 | ✓ OK |
| API Gateway APIs | 600 | 1 | ✓ OK |
| API Keys | 10000 | 1 | ✓ OK |

### S3 Bucket Contents ✓
- 16 Lambda packages uploaded and ready
- CloudFormation templates present (need sync for fix)
- Model artifacts present (placeholder model)

### Lambda Code Structure ✓
- All 16 Lambda functions have proper index.py
- Environment variables correctly referenced
- Dependencies bundled in zip files

### Deployment Script ✓
- Properly validates credentials
- Auto-selects safe CIDR
- Checks quotas
- Has proper error handling and resume capability

---

## Pre-Deployment Checklist

### Before Running deploy.sh

- [ ] **Fix dev.json Hub URL** (Critical #1)
- [ ] **Fix Lambda security group CIDR** (Critical #2)
- [ ] **Request Bedrock model access** (High #4)
- [ ] Ensure git is up to date with APIKey bug fix
- [ ] Have API keys ready for secrets configuration

### During Deployment

- [ ] Monitor CloudFormation for any new errors
- [ ] Note the selected VPC CIDR for RDS security group update

### After Deployment

- [ ] **Update RDS security group** to allow new VPC CIDR (Critical #3)
- [ ] **Configure all secrets** with real values (High #6)
- [ ] Set up VPC peering between new VPC and existing VPC
- [ ] Add VPC peering route to private route table
- [ ] Test Lambda → RDS connectivity
- [ ] Test Lambda → Hub API connectivity

---

## Environment Comparison

### Expected (from templates) vs Actual (from AWS)

| Resource | Template Assumes | Actual in AWS |
|----------|------------------|---------------|
| Existing VPC CIDR | 10.0.0.0/8 (egress rule) | 172.30.0.0/16 |
| RDS Endpoint | PLACEHOLDER | brandpointdb.c5rp85tg25on.us-east-1.rds.amazonaws.com |
| RDS Port | 1433 | 1433 ✓ |
| RDS Database | ARA3 | ARA3 ✓ (assumed) |
| Hub API (dev) | hub-staging.brandpoint.com | Does not exist |
| Hub API (prod) | hub.brandpoint.com | Exists ✓ |
| Region | us-east-1 | us-east-1 ✓ |

---

## Appendix: File Change Summary

### Files Requiring Changes

| File | Line | Issue | Change |
|------|------|-------|--------|
| `infrastructure/cloudformation/parameters/dev.json` | 24 | Wrong Hub URL | Update to valid URL |
| `infrastructure/cloudformation/00-foundation.yaml` | 222 | Wrong CIDR | `10.0.0.0/8` → `172.30.0.0/16` |
| `infrastructure/cloudformation/05-api.yaml` | 43 | Already fixed | ✓ Done |

### AWS Console Actions Required

| Action | Location | Details |
|--------|----------|---------|
| Accept Bedrock EULA | Bedrock → Model Access | Request Claude, Titan models |
| Update RDS SG | EC2 → Security Groups → sg-5f91623b | Add new VPC CIDR |
| VPC Peering | VPC → Peering Connections | Create after deployment |

---

*Report generated from live AWS environment analysis and repo code review.*
