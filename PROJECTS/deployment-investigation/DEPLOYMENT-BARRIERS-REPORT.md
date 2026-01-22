# Deployment Barriers Analysis Report

**Date:** 2026-01-21
**Investigator:** Claude (codename37)
**Environment:** AWS Brandpoint (Account: 144105412483)

---

## Executive Summary

After investigating the AWS environment for potential deployment barriers, I identified **2 critical issues** and **1 minor issue** that need attention before the next deployment attempt.

| Severity | Issue | Impact |
|----------|-------|--------|
| **CRITICAL** | S3 templates bucket contains buggy code | Deployment will fail |
| **CRITICAL** | Elastic IP quota is tight | Deployment may fail |
| **MINOR** | Orphaned CloudWatch Log Group | No impact, cleanup recommended |

---

## Critical Issue #1: S3 Templates Bucket Has Old Buggy Code

### The Problem

The S3 bucket `brandpoint-ai-dev-templates-144105412483` contains CloudFormation templates that were uploaded **before** we fixed the APIKey bug.

**Evidence:**
```bash
$ aws s3 cp s3://brandpoint-ai-dev-templates-144105412483/cloudformation/05-api.yaml - | grep -A2 "APIKey:"

  APIKey:
    Type: AWS::ApiGateway::ApiKey
    DependsOn: APIDeployment    # <-- STILL HAS THE BUG!
```

### Why This Matters

The `deploy.sh` script:
1. Uploads templates to S3 (Step 2)
2. CloudFormation reads templates from S3 URLs

The templates were last uploaded at **2026-01-21 16:29:42** (before our fix).

### Resolution

When the IT team runs `deploy.sh` after pulling the fix, it will:
```bash
aws s3 sync ${INFRA_DIR}/cloudformation/ s3://${TEMPLATES_BUCKET}/cloudformation/ --delete
```

This **will overwrite** the buggy templates with the fixed versions. **No manual action needed** as long as they `git pull` first.

### Verification Required

After next deployment attempt, verify the fix was uploaded:
```bash
aws s3 cp s3://brandpoint-ai-dev-templates-144105412483/cloudformation/05-api.yaml - | grep -A2 "APIKey:"
# Should show: DependsOn: APIStage
```

---

## Critical Issue #2: Elastic IP Quota is Tight

### Current State

| Metric | Value |
|--------|-------|
| EIP Quota | 5 |
| EIPs in Use | 3 |
| EIPs Available | **2** |

### Existing EIPs

| Public IP | Allocation ID | Notes |
|-----------|---------------|-------|
| 23.21.230.73 | eipalloc-adea809c | Production |
| 23.23.188.123 | eipalloc-08cd5acc84a36ea77 | WIN-PROD Main Server |
| 3.209.100.143 | eipalloc-0534fdfb8463a60ee | Unknown |

### Deployment Requirement

The foundation template creates **1 NAT Gateway EIP**:
```yaml
NatGatewayEIP:
  Type: AWS::EC2::EIP
  Properties:
    Domain: vpc
```

### Risk Assessment

- **Current:** 2 available, 1 needed = **OK for single deployment**
- **Risk:** If deployment fails and retries, orphaned EIPs could accumulate
- **Risk:** No headroom for production environment deployment

### Recommendation

1. **Before prod deployment:** Request EIP quota increase to 10
2. **Monitor:** Check EIP count after each failed deployment
3. **Optional:** Investigate if `3.209.100.143` is still needed

---

## Minor Issue: Orphaned CloudWatch Log Group

### The Problem

A CloudWatch Log Group was created during a previous deployment attempt and not cleaned up:

```
/aws/sagemaker/Endpoints/brandpoint-ai-dev-visibility-predictor
```

### Impact

- **No deployment impact** - CloudFormation will reuse or recreate as needed
- **Cost:** Negligible (0 bytes stored)
- **Clutter:** Shows up in CloudWatch console

### Recommendation

Optional cleanup after successful deployment:
```bash
aws logs delete-log-group \
  --log-group-name /aws/sagemaker/Endpoints/brandpoint-ai-dev-visibility-predictor \
  --profile brandpoint
```

---

## Resources That Are Ready (No Conflicts)

### S3 Buckets (Pre-created, Ready to Use)

| Bucket | Contents | Status |
|--------|----------|--------|
| brandpoint-ai-dev-lambda-code-144105412483 | 16 Lambda zips | Ready |
| brandpoint-ai-dev-templates-144105412483 | CF templates | **Needs update (auto)** |
| brandpoint-ai-dev-model-artifacts-144105412483 | model.tar.gz | Ready |

### Lambda Functions Ready

All 16 Lambda packages are uploaded and ready:
- analyze-visibility.zip (14 MB)
- common.zip (19 MB)
- content-ingestion.zip (16 MB)
- execute-query.zip (15 MB)
- feature-extraction.zip (14 MB)
- generate-queries.zip (14 MB)
- graph-query.zip (18 MB)
- graph-update.zip (18 MB)
- health-check.zip (14 MB)
- insights-generator.zip (14 MB)
- intelligence-api.zip (14 MB)
- load-persona.zip (14 MB)
- persona-api.zip (14 MB)
- prediction-api.zip (14 MB)
- similarity-search.zip (16 MB)
- store-results.zip (15 MB)

### VPC CIDR (No Conflict)

| Existing VPC | CIDR | Deployment CIDR |
|--------------|------|-----------------|
| vpc-d26af3b7 (Default) | 172.30.0.0/16 | 10.200.0.0/16 (auto-selected) |

**No overlap** - VPC peering will be possible.

### Service Quotas (Sufficient)

| Service | Quota | Used | Available | Required |
|---------|-------|------|-----------|----------|
| VPCs | 5 | 1 | 4 | 1 |
| Elastic IPs | 5 | 3 | 2 | 1 |
| Lambda Concurrent | 1000 | ~0 | ~1000 | 15 |
| API Gateway APIs | 600 | 1 | 599 | 1 |
| API Keys | 10000 | ~0 | ~10000 | 1 |

### Clean State (No Leftover Resources)

The following have **no brandpoint-ai resources** (rollbacks cleaned up properly):
- IAM Roles
- Secrets Manager Secrets
- Lambda Functions
- SageMaker Endpoints
- SageMaker Models
- SageMaker Endpoint Configs
- API Gateway REST APIs
- Step Functions State Machines
- OpenSearch Domains
- Neptune Clusters
- DynamoDB Tables
- EventBridge Rules
- CloudWatch Alarms
- SNS Topics
- KMS Aliases

---

## Pre-Deployment Checklist

### For Brandpoint IT Team

```bash
# 1. Pull the latest code (includes the bug fix)
git pull origin main

# 2. Verify the fix is present locally
grep "DependsOn: APIStage" infrastructure/cloudformation/05-api.yaml
# Should return a match

# 3. Run the deployment
./scripts/brandpoint-deploy.sh --env dev

# 4. The script will automatically:
#    - Upload fixed templates to S3
#    - Deploy the infrastructure
```

### Post-Deployment Verification

```bash
# Check EIP usage
aws ec2 describe-addresses --query 'length(Addresses)'

# Verify templates in S3 are fixed
aws s3 cp s3://brandpoint-ai-dev-templates-144105412483/cloudformation/05-api.yaml - | grep -A2 "APIKey:"
```

---

## Appendix: Full Resource Inventory

### Existing S3 Buckets in Account

| Bucket | Created | Category |
|--------|---------|----------|
| brandpoint-ai-dev-lambda-code-144105412483 | 2026-01-20 | Deployment |
| brandpoint-ai-dev-model-artifacts-144105412483 | 2026-01-21 | Deployment |
| brandpoint-ai-dev-templates-144105412483 | 2026-01-21 | Deployment |
| HouseTopia | 2014-07-21 | Legacy |
| aracontent | 2010-02-22 | Production |
| brandpoint-admin-assets | 2019-04-17 | Production |
| brandpoint-corp-backup | 2025-09-16 | Backup |
| brandpoint-hub-assets | 2015-05-27 | Production |
| brandpoint-hub-files | 2017-08-15 | Production |
| brandpoint-images | 2014-04-09 | Production |
| brandpoint-pubdocs | 2013-04-04 | Production |
| brandpoint-restic | 2021-11-17 | Backup |
| brandpoint-wpvivid | 2021-01-15 | Backup |
| brandpoint-xdata-backup | 2022-10-13 | Backup |
| elasticbeanstalk-us-east-1-144105412483 | 2017-02-10 | Legacy |
| images.brandpointcontent | 2014-05-02 | Production |
| infographics.brandpointcontent | 2014-06-04 | Production |

### Existing Production Resources (Will Not Conflict)

- 4 Running EC2 Instances (production workloads)
- 1 RDS SQL Server Instance (brandpointdb)
- 3 CloudFront Distributions
- 1 NAT Gateway (in production VPC)
- 1 API Gateway (event-analytics-backend)

---

## Conclusion

The deployment should succeed on the next attempt, provided:

1. **IT team pulls the latest code** with the APIKey bug fix
2. **deploy.sh uploads the fixed templates** to S3 (automatic)
3. **EIP quota is monitored** (currently OK but tight)

No manual resource cleanup or quota increases are required for the dev deployment.

---

*Report generated from live AWS environment analysis.*
