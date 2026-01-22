# Brandpoint AI Platform - Enterprise Fix Plan

**Document ID:** BP-AI-FIX-2026-001
**Version:** 1.0
**Date:** 2026-01-21
**Author:** Codename 37 (Claude)
**Classification:** Internal - Technical Operations

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-21 | Codename 37 | Initial fix plan |
| 1.1 | 2026-01-21 | Codename 37 | Phase 1 complete, added IAM permission blocker (NEW-001) |

---

## Executive Summary

This document provides a comprehensive remediation plan for 10 identified issues in the Brandpoint AI Platform deployment configuration. Issues range from critical infrastructure misconfigurations to documentation updates.

### Risk Assessment

| Risk Level | Issues | Deployment Impact |
|------------|--------|-------------------|
| Critical | 3 | Blocks deployment or causes immediate failure |
| High | 3 | Causes functionality failure post-deployment |
| Medium | 2 | Degraded functionality, workarounds available |
| Low | 2 | No functional impact, housekeeping |

### Estimated Remediation Timeline

| Phase | Duration | Activities |
|-------|----------|------------|
| Phase 1: Pre-Deployment Fixes | 1-2 hours | Code changes, Bedrock access |
| Phase 2: Deployment | 45-60 minutes | Run deployment script |
| Phase 3: Post-Deployment Config | 2-3 hours | VPC peering, security groups, secrets |
| Phase 4: Validation | 1 hour | End-to-end testing |
| **Total** | **5-7 hours** | |

---

## Issue Registry

| ID | Severity | Issue | Owner | Status |
|----|----------|-------|-------|--------|
| FIX-001 | CRITICAL | Hub staging URL does not exist | Codename 37 | ✅ COMPLETE |
| FIX-002 | CRITICAL | Lambda security group CIDR mismatch | Codename 37 | ✅ COMPLETE |
| FIX-003 | CRITICAL | RDS security group update required | Brandpoint IT | Open |
| FIX-004 | HIGH | Bedrock model agreement not accepted | Brandpoint IT | ✅ VERIFIED OK |
| FIX-005 | HIGH | S3 templates contain buggy code | Auto-resolves | Open |
| FIX-006 | HIGH | Secrets require real values | Brandpoint IT | Open |
| FIX-007 | MEDIUM | Elastic IP quota is tight | Brandpoint IT | Open |
| FIX-008 | MEDIUM | Orphaned CloudWatch log group | Optional | Open |
| FIX-009 | LOW | Template bucket name in parameters | Optional | Open |
| FIX-010 | LOW | Documentation references invalid URL | Codename 37 | Open |
| **NEW-001** | **BLOCKER** | **IAM CreateRole permission missing** | **Brandpoint IT** | **⚠️ BLOCKING** |

### NEW-001: IAM Permission Blocker (Discovered 2026-01-21)

**Severity:** BLOCKER
**Type:** IAM Permissions
**Owner:** Brandpoint IT
**Status:** Awaiting IT response

**Problem:** The `codename37` IAM user lacks `iam:CreateRole` permission. CloudFormation deployment creates 6 IAM roles and will fail without this permission.

**Permissions Verified:**
| Permission | Status |
|------------|--------|
| CloudFormation: CreateStack | ✅ Pass |
| EC2: CreateVpc | ✅ Pass |
| S3: Read/Write/Delete | ✅ Pass |
| IAM: ListRoles | ✅ Pass |
| Bedrock: InvokeModel | ✅ Pass |
| **IAM: CreateRole** | ❌ **DENIED** |

**Resolution Options:**
1. Grant `codename37` user IAM write permissions (CreateRole, PutRolePolicy, AttachRolePolicy, PassRole)
2. Add `PowerUserAccess` + limited IAM permissions
3. Have Brandpoint IT (with admin access) run the deployment

**Verification:**
```bash
aws iam create-role --role-name permission-test --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' --profile brandpoint && aws iam delete-role --role-name permission-test --profile brandpoint
```

---

## Phase 1: Pre-Deployment Fixes

### FIX-001: Hub Staging URL Does Not Exist

**Severity:** CRITICAL
**Type:** Configuration Error
**Estimated Time:** 15 minutes
**Owner:** Codename 37
**Requires:** Code change + git commit

#### Problem Statement

The `dev.json` parameters file references `https://hub-staging.brandpoint.com` which does not exist (DNS NXDOMAIN).

#### Current State

```json
// File: infrastructure/cloudformation/parameters/dev.json (line 24)
{
  "ParameterKey": "HubApiBaseUrl",
  "ParameterValue": "https://hub-staging.brandpoint.com"  // DOES NOT EXIST
}
```

#### Root Cause

Configuration was created without access to Brandpoint's actual environment. Assumption was made that a staging environment existed.

#### Resolution Options

| Option | Description | Risk | Recommendation |
|--------|-------------|------|----------------|
| A | Use production Hub URL | Medium - dev traffic to prod | For POC only |
| B | Create mock endpoint | Low - isolated testing | Best for dev |
| C | Ask Brandpoint for staging URL | None | If it exists |

#### Recommended Resolution (Option A for POC)

**Step 1:** Verify with Brandpoint if staging URL exists
```bash
# Ask Brandpoint IT:
# "Do you have a staging Hub environment? If so, what is the URL?"
```

**Step 2:** If no staging exists, update to production URL

```json
// File: infrastructure/cloudformation/parameters/dev.json
// Change line 24 from:
"ParameterValue": "https://hub-staging.brandpoint.com"

// To:
"ParameterValue": "https://hub.brandpoint.com"
```

**Step 3:** Add warning comment to secrets template

```yaml
# File: infrastructure/cloudformation/07-secrets.yaml
# Update line 62 comment to note dev uses prod Hub
```

#### Verification

```bash
# Test DNS resolution
host hub.brandpoint.com
# Expected: Returns IP addresses

# Test HTTPS connectivity
curl -s -o /dev/null -w "%{http_code}" https://hub.brandpoint.com
# Expected: 200 or 302
```

#### Rollback Procedure

```bash
git checkout infrastructure/cloudformation/parameters/dev.json
```

---

### FIX-002: Lambda Security Group CIDR Mismatch

**Severity:** CRITICAL
**Type:** Infrastructure Misconfiguration
**Estimated Time:** 15 minutes
**Owner:** Codename 37
**Requires:** Code change + git commit

#### Problem Statement

Lambda security group egress rule allows outbound SQL Server traffic to `10.0.0.0/8`, but the existing RDS is in VPC `172.30.0.0/16`.

#### Current State

```yaml
# File: infrastructure/cloudformation/00-foundation.yaml (line 220-223)
- IpProtocol: tcp
  FromPort: 1433
  ToPort: 1433
  CidrIp: 10.0.0.0/8  # WRONG - RDS is in 172.30.0.0/16
```

#### Root Cause

Assumption was made that existing Brandpoint VPC would be in the 10.x.x.x range. Actual VPC uses 172.30.0.0/16.

#### Resolution

**Step 1:** Edit foundation template

```yaml
# File: infrastructure/cloudformation/00-foundation.yaml
# Change line 222 from:
CidrIp: 10.0.0.0/8

# To:
CidrIp: 172.30.0.0/16
```

**Step 2:** Update description comment

```yaml
# Change line 223 from:
Description: SQL Server RDS (via VPC peering to existing Brandpoint VPC)

# To:
Description: SQL Server RDS (via VPC peering to Brandpoint VPC 172.30.0.0/16)
```

#### Verification

```bash
# Validate template syntax
aws cloudformation validate-template \
  --template-body file://infrastructure/cloudformation/00-foundation.yaml

# Verify CIDR is correct
grep -A2 "FromPort: 1433" infrastructure/cloudformation/00-foundation.yaml
# Expected output should show: CidrIp: 172.30.0.0/16
```

#### Rollback Procedure

```bash
git checkout infrastructure/cloudformation/00-foundation.yaml
```

---

### FIX-004: Bedrock Model Agreement Not Accepted

**Severity:** HIGH
**Type:** AWS Service Configuration
**Estimated Time:** 30 minutes (includes approval wait time)
**Owner:** Brandpoint IT
**Requires:** AWS Console access with appropriate permissions

#### Problem Statement

```json
{
  "modelId": "anthropic.claude-3-sonnet-20240229-v1",
  "agreementAvailability": {
    "status": "NOT_AVAILABLE"
  }
}
```

Lambda functions using Bedrock will fail with access denied until the EULA is accepted.

#### Resolution

**Step 1:** Navigate to Bedrock Console
```
AWS Console → Amazon Bedrock → Model access (left sidebar)
```

**Step 2:** Request access to required models

| Model ID | Purpose | Required |
|----------|---------|----------|
| anthropic.claude-3-5-sonnet-20241022-v2:0 | Query generation, analysis | Yes |
| amazon.titan-embed-text-v2:0 | Vector embeddings | Yes |
| anthropic.claude-3-sonnet-* | Fallback models | Recommended |
| anthropic.claude-3-haiku-* | Fast inference | Recommended |

**Step 3:** Accept End User License Agreement (EULA)

1. Click "Manage model access"
2. Select required models
3. Click "Request model access"
4. Review and accept terms
5. Wait for approval (usually immediate for Claude/Titan)

**Step 4:** Verify access

```bash
aws bedrock get-foundation-model-availability \
  --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --profile brandpoint

# Expected:
# "agreementAvailability": { "status": "AVAILABLE" }
```

#### Verification

```bash
# Test model invocation
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Say hello"}]}' \
  --profile brandpoint \
  output.json

# Expected: Successful response in output.json
```

#### Rollback Procedure

N/A - This is an enable-only action. Models can be disabled via console if needed.

---

## Phase 2: Deployment

### FIX-005: S3 Templates Contain Buggy Code

**Severity:** HIGH
**Type:** Stale Artifacts
**Estimated Time:** Auto-resolves during deployment
**Owner:** Auto
**Requires:** Git pull + deploy.sh execution

#### Problem Statement

S3 bucket `brandpoint-ai-dev-templates-144105412483` contains CloudFormation templates uploaded before the APIKey bug fix.

#### Current State (S3)

```yaml
# s3://brandpoint-ai-dev-templates-144105412483/cloudformation/05-api.yaml
APIKey:
  Type: AWS::ApiGateway::ApiKey
  DependsOn: APIDeployment  # BUG - causes deployment failure
```

#### Resolution

**No manual action required.** The `deploy.sh` script includes:

```bash
aws s3 sync ${INFRA_DIR}/cloudformation/ s3://${TEMPLATES_BUCKET}/cloudformation/ --delete
```

This will automatically upload the fixed templates when deployment runs.

#### Verification

After running deploy.sh Step 2, verify:

```bash
aws s3 cp s3://brandpoint-ai-dev-templates-144105412483/cloudformation/05-api.yaml - \
  --profile brandpoint | grep -A2 "APIKey:"

# Expected:
#   APIKey:
#     Type: AWS::ApiGateway::ApiKey
#     DependsOn: APIStage  # FIXED
```

---

### Deployment Execution

**Prerequisites Checklist:**
- [ ] FIX-001 committed (Hub URL)
- [ ] FIX-002 committed (Lambda CIDR)
- [ ] FIX-004 completed (Bedrock access)
- [ ] Git repository is up to date
- [ ] AWS CLI configured with `brandpoint` profile

**Execution:**

```bash
cd /home/jaket/dev_c37/AWS

# Ensure latest code
git pull origin main

# Run deployment
./scripts/brandpoint-deploy.sh --env dev --profile brandpoint

# Monitor CloudFormation in separate terminal
watch -n 30 'aws cloudformation describe-stack-events \
  --stack-name brandpoint-ai-dev \
  --profile brandpoint \
  --query "StackEvents[0:5].[Timestamp,ResourceStatus,LogicalResourceId]" \
  --output table'
```

**Expected Duration:** 45-60 minutes

---

## Phase 3: Post-Deployment Configuration

### FIX-003: RDS Security Group Update Required

**Severity:** CRITICAL
**Type:** AWS Security Configuration
**Estimated Time:** 15 minutes
**Owner:** Brandpoint IT
**Requires:** AWS Console or CLI access, deployment must be complete

#### Problem Statement

The existing RDS security group (`sg-5f91623b`) does not allow inbound connections from the new AI platform VPC.

#### Current State

```
Security Group: sg-5f91623b (SQLServer)
Inbound Rules:
  - 172.30.0.153/32:1433 (internal)
  - 172.30.0.251/32:1433 (internal)
  - 172.30.0.91/32:1433 (internal)
  - 23.20.101.74/32:1433 (metabase)
  - Plus external IPs for full access

MISSING: New AI platform VPC CIDR
```

#### Prerequisites

1. Deployment must be complete
2. Note the VPC CIDR used (likely 10.200.0.0/16)
3. VPC Peering must be established first (see FIX-003a below)

#### FIX-003a: Establish VPC Peering

**Step 1:** Get VPC IDs

```bash
# Get new AI platform VPC ID
NEW_VPC_ID=$(aws cloudformation describe-stacks \
  --stack-name brandpoint-ai-dev \
  --profile brandpoint \
  --query "Stacks[0].Outputs[?OutputKey=='VPCId'].OutputValue" \
  --output text)

echo "New VPC ID: $NEW_VPC_ID"

# Existing Brandpoint VPC
EXISTING_VPC_ID="vpc-d26af3b7"
echo "Existing VPC ID: $EXISTING_VPC_ID"
```

**Step 2:** Create VPC Peering Connection

```bash
PEERING_ID=$(aws ec2 create-vpc-peering-connection \
  --vpc-id $NEW_VPC_ID \
  --peer-vpc-id $EXISTING_VPC_ID \
  --profile brandpoint \
  --query "VpcPeeringConnection.VpcPeeringConnectionId" \
  --output text)

echo "Peering Connection ID: $PEERING_ID"
```

**Step 3:** Accept VPC Peering Connection

```bash
aws ec2 accept-vpc-peering-connection \
  --vpc-peering-connection-id $PEERING_ID \
  --profile brandpoint
```

**Step 4:** Add Route to New VPC's Private Route Table

```bash
# Get private route table ID from stack outputs
PRIVATE_RT_ID=$(aws cloudformation describe-stacks \
  --stack-name brandpoint-ai-dev \
  --profile brandpoint \
  --query "Stacks[0].Outputs[?OutputKey=='PrivateRouteTableId'].OutputValue" \
  --output text)

# Add route to existing VPC
aws ec2 create-route \
  --route-table-id $PRIVATE_RT_ID \
  --destination-cidr-block 172.30.0.0/16 \
  --vpc-peering-connection-id $PEERING_ID \
  --profile brandpoint
```

**Step 5:** Add Route to Existing VPC's Route Table

```bash
# Get existing VPC's main route table
EXISTING_RT_ID=$(aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=$EXISTING_VPC_ID" "Name=association.main,Values=true" \
  --profile brandpoint \
  --query "RouteTables[0].RouteTableId" \
  --output text)

# Get new VPC CIDR
NEW_VPC_CIDR=$(aws cloudformation describe-stacks \
  --stack-name brandpoint-ai-dev \
  --profile brandpoint \
  --query "Stacks[0].Outputs[?OutputKey=='VPCCidr'].OutputValue" \
  --output text)

# Add route
aws ec2 create-route \
  --route-table-id $EXISTING_RT_ID \
  --destination-cidr-block $NEW_VPC_CIDR \
  --vpc-peering-connection-id $PEERING_ID \
  --profile brandpoint
```

#### FIX-003b: Update RDS Security Group

**Step 1:** Add inbound rule for new VPC

```bash
# Get new VPC CIDR (should be 10.200.0.0/16 or similar)
NEW_VPC_CIDR=$(aws cloudformation describe-stacks \
  --stack-name brandpoint-ai-dev \
  --profile brandpoint \
  --query "Stacks[0].Outputs[?OutputKey=='VPCCidr'].OutputValue" \
  --output text)

echo "Adding rule for CIDR: $NEW_VPC_CIDR"

# Add security group rule
aws ec2 authorize-security-group-ingress \
  --group-id sg-5f91623b \
  --protocol tcp \
  --port 1433 \
  --cidr $NEW_VPC_CIDR \
  --profile brandpoint

# Verify
aws ec2 describe-security-groups \
  --group-ids sg-5f91623b \
  --profile brandpoint \
  --query "SecurityGroups[0].IpPermissions"
```

#### Verification

```bash
# Test connectivity from Lambda (after deployment)
# Invoke health check Lambda which tests RDS connectivity
aws lambda invoke \
  --function-name brandpoint-ai-dev-health-check \
  --profile brandpoint \
  --payload '{"checkDatabase": true}' \
  response.json

cat response.json
# Expected: Database connectivity status
```

#### Rollback Procedure

```bash
# Remove security group rule
aws ec2 revoke-security-group-ingress \
  --group-id sg-5f91623b \
  --protocol tcp \
  --port 1433 \
  --cidr $NEW_VPC_CIDR \
  --profile brandpoint

# Delete VPC peering routes (reverse order)
aws ec2 delete-route \
  --route-table-id $EXISTING_RT_ID \
  --destination-cidr-block $NEW_VPC_CIDR \
  --profile brandpoint

aws ec2 delete-route \
  --route-table-id $PRIVATE_RT_ID \
  --destination-cidr-block 172.30.0.0/16 \
  --profile brandpoint

# Delete VPC peering connection
aws ec2 delete-vpc-peering-connection \
  --vpc-peering-connection-id $PEERING_ID \
  --profile brandpoint
```

---

### FIX-006: Secrets Require Real Values

**Severity:** HIGH
**Type:** Configuration
**Estimated Time:** 30 minutes
**Owner:** Brandpoint IT
**Requires:** API keys from external services, RDS credentials

#### Problem Statement

Deployed secrets contain placeholder values that must be replaced with actual credentials.

#### Secrets to Configure

| Secret ID | Required Value | Source |
|-----------|----------------|--------|
| `brandpoint-ai-dev-openai-api-key` | OpenAI API key | OpenAI dashboard |
| `brandpoint-ai-dev-perplexity-api-key` | Perplexity API key | Perplexity dashboard |
| `brandpoint-ai-dev-gemini-api-key` | Google Gemini API key | Google AI Studio |
| `brandpoint-ai-dev-hub-service-account-key` | Hub service account key | Brandpoint Hub admin |
| `brandpoint-ai-dev-ara3-database-readonly` | RDS connection JSON | Brandpoint DBA |

#### Resolution

**Secret 1: OpenAI API Key**

```bash
aws secretsmanager put-secret-value \
  --secret-id brandpoint-ai-dev-openai-api-key \
  --secret-string '{"apiKey":"sk-YOUR-ACTUAL-OPENAI-KEY"}' \
  --profile brandpoint
```

**Secret 2: Perplexity API Key**

```bash
aws secretsmanager put-secret-value \
  --secret-id brandpoint-ai-dev-perplexity-api-key \
  --secret-string '{"apiKey":"pplx-YOUR-ACTUAL-PERPLEXITY-KEY"}' \
  --profile brandpoint
```

**Secret 3: Google Gemini API Key**

```bash
aws secretsmanager put-secret-value \
  --secret-id brandpoint-ai-dev-gemini-api-key \
  --secret-string '{"apiKey":"YOUR-ACTUAL-GEMINI-KEY"}' \
  --profile brandpoint
```

**Secret 4: Hub Service Account Key**

```bash
aws secretsmanager put-secret-value \
  --secret-id brandpoint-ai-dev-hub-service-account-key \
  --secret-string '{"apiKey":"YOUR-HUB-SERVICE-ACCOUNT-KEY","baseUrl":"https://hub.brandpoint.com/api"}' \
  --profile brandpoint
```

**Secret 5: ARA3 Database Connection**

```bash
aws secretsmanager put-secret-value \
  --secret-id brandpoint-ai-dev-ara3-database-readonly \
  --secret-string '{
    "host": "brandpointdb.c5rp85tg25on.us-east-1.rds.amazonaws.com",
    "port": "1433",
    "database": "ARA3",
    "username": "READONLY_USER_FROM_DBA",
    "password": "PASSWORD_FROM_DBA",
    "driver": "ODBC Driver 17 for SQL Server"
  }' \
  --profile brandpoint
```

#### Verification

```bash
# Verify each secret (shows last 4 chars only for security)
for secret in openai-api-key perplexity-api-key gemini-api-key hub-service-account-key ara3-database-readonly; do
  echo "Checking brandpoint-ai-dev-$secret..."
  aws secretsmanager get-secret-value \
    --secret-id brandpoint-ai-dev-$secret \
    --profile brandpoint \
    --query "SecretString" \
    --output text | head -c 50
  echo "..."
done
```

#### Rollback Procedure

Secrets can be restored to placeholder values:

```bash
aws secretsmanager put-secret-value \
  --secret-id brandpoint-ai-dev-openai-api-key \
  --secret-string '{"apiKey":"PLACEHOLDER_REPLACE_AFTER_DEPLOY"}' \
  --profile brandpoint
```

---

## Phase 4: Validation

### End-to-End Testing Checklist

#### Infrastructure Tests

```bash
# 1. Stack status
aws cloudformation describe-stacks \
  --stack-name brandpoint-ai-dev \
  --profile brandpoint \
  --query "Stacks[0].StackStatus"
# Expected: CREATE_COMPLETE

# 2. API Gateway endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name brandpoint-ai-dev \
  --profile brandpoint \
  --query "Stacks[0].Outputs[?OutputKey=='APIEndpoint'].OutputValue" \
  --output text)
echo "API Endpoint: $API_ENDPOINT"

# 3. Health check
curl -s "$API_ENDPOINT/health"
# Expected: {"status": "healthy", ...}
```

#### Connectivity Tests

```bash
# 4. Lambda → OpenSearch
aws lambda invoke \
  --function-name brandpoint-ai-dev-health-check \
  --profile brandpoint \
  --payload '{"checkOpenSearch": true}' \
  /tmp/response.json && cat /tmp/response.json

# 5. Lambda → Neptune
aws lambda invoke \
  --function-name brandpoint-ai-dev-health-check \
  --profile brandpoint \
  --payload '{"checkNeptune": true}' \
  /tmp/response.json && cat /tmp/response.json

# 6. Lambda → RDS (requires VPC peering)
aws lambda invoke \
  --function-name brandpoint-ai-dev-health-check \
  --profile brandpoint \
  --payload '{"checkDatabase": true}' \
  /tmp/response.json && cat /tmp/response.json
```

#### Integration Tests

```bash
# 7. Bedrock integration
aws lambda invoke \
  --function-name brandpoint-ai-dev-generate-queries \
  --profile brandpoint \
  --payload '{"test": true}' \
  /tmp/response.json && cat /tmp/response.json

# 8. API with key
API_KEY=$(aws apigateway get-api-keys \
  --profile brandpoint \
  --include-values \
  --query "items[?name=='brandpoint-ai-dev-api-key'].value" \
  --output text)

curl -s -H "x-api-key: $API_KEY" "$API_ENDPOINT/health"
```

---

## Appendix A: Complete Fix Summary

### Code Changes Required

| File | Line | Current | New |
|------|------|---------|-----|
| `infrastructure/cloudformation/parameters/dev.json` | 24 | `https://hub-staging.brandpoint.com` | `https://hub.brandpoint.com` |
| `infrastructure/cloudformation/00-foundation.yaml` | 222 | `CidrIp: 10.0.0.0/8` | `CidrIp: 172.30.0.0/16` |

### AWS Console Actions Required

| Action | Service | Details |
|--------|---------|---------|
| Accept Bedrock EULA | Bedrock | Request access to Claude 3.5, Titan Embed |
| Update RDS Security Group | EC2 | Add new VPC CIDR to sg-5f91623b |
| Create VPC Peering | VPC | Connect new VPC to vpc-d26af3b7 |
| Configure Routes | VPC | Add peering routes to both VPCs |

### Secrets to Configure

| Secret | Format |
|--------|--------|
| OpenAI | `{"apiKey":"sk-..."}` |
| Perplexity | `{"apiKey":"pplx-..."}` |
| Gemini | `{"apiKey":"..."}` |
| Hub Service Account | `{"apiKey":"...","baseUrl":"https://hub.brandpoint.com/api"}` |
| ARA3 Database | `{"host":"...","port":"1433","database":"ARA3","username":"...","password":"..."}` |

---

## Appendix B: Rollback Procedures

### Full Stack Rollback

```bash
# Delete the entire stack (DESTRUCTIVE)
aws cloudformation delete-stack \
  --stack-name brandpoint-ai-dev \
  --profile brandpoint

# Monitor deletion
aws cloudformation wait stack-delete-complete \
  --stack-name brandpoint-ai-dev \
  --profile brandpoint
```

### Partial Rollbacks

See individual fix sections for targeted rollback procedures.

---

## Appendix C: Support Contacts

| Role | Contact | Responsibility |
|------|---------|----------------|
| Technical Lead | jake@codename37.com | Code fixes, deployment support |
| Brandpoint IT | Adam McBroom | AWS access, security groups, VPC peering |
| Brandpoint DBA | (Internal) | RDS credentials, read-only user |
| External APIs | (Various) | API key management |

---

## Appendix D: Change Request Template

For enterprise change management systems:

```
CHANGE REQUEST
==============
Title: Brandpoint AI Platform - Pre-Deployment Fixes
Category: Infrastructure Configuration
Priority: High
Risk: Medium

Affected Systems:
- AWS CloudFormation Templates
- AWS Bedrock Service
- AWS RDS Security Groups
- AWS VPC Configuration

Change Window: [Scheduled Date/Time]
Rollback Window: 4 hours

Approvals Required:
- [ ] Technical Lead
- [ ] Brandpoint IT Manager
- [ ] Security Review (for SG changes)

Testing Requirements:
- [ ] CloudFormation validation
- [ ] Connectivity tests
- [ ] End-to-end API tests
```

---

*Document End*
