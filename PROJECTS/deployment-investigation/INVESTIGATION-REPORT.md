# Deployment Failure Investigation Report

**Date:** 2026-01-21
**Investigator:** Claude (codename37)
**Environment:** AWS Brandpoint (Account: 144105412483)
**Status:** ROOT CAUSE IDENTIFIED

---

## Executive Summary

The Brandpoint IT team has attempted to deploy the `brandpoint-ai-dev` infrastructure **at least 10+ times today**, and all deployments have failed. The root cause is a **CloudFormation template bug** in `infrastructure/cloudformation/05-api.yaml` where the `APIKey` resource has an incorrect dependency, causing a race condition.

---

## Evidence: Failed Deployment Attempts

### CloudFormation Stack History (Today)

| Time (UTC) | Stack Name | Status | Notes |
|------------|------------|--------|-------|
| 22:33 | brandpoint-ai-dev | ROLLBACK_COMPLETE | Most recent |
| 21:07 | brandpoint-ai-dev | DELETE_COMPLETE | |
| 19:59 | brandpoint-ai-dev | DELETE_COMPLETE | |
| 18:53 | brandpoint-ai-dev | DELETE_COMPLETE | |
| 16:56 | brandpoint-ai-dev | DELETE_COMPLETE | |
| 16:17 | brandpoint-ai-dev | DELETE_COMPLETE | |
| 15:57 | brandpoint-ai-dev | DELETE_COMPLETE | |
| 15:35 | brandpoint-ai-dev | DELETE_COMPLETE | |
| 15:21 | brandpoint-ai-dev | DELETE_COMPLETE | |
| 14:54 | brandpoint-ai-dev | DELETE_COMPLETE | |
| 14:32 | brandpoint-ai-dev | DELETE_COMPLETE | |

**Pattern:** Every deployment reaches the API layer and then fails, triggering automatic rollback.

---

## Root Cause Analysis

### The Failure Point

```
ROLLBACK_IN_PROGRESS: The following resource(s) failed to create: [APIStack, OrchestrationStack]

APIStack CREATE_FAILED: Embedded stack was not successfully created:
The following resource(s) failed to create: [APIKey]
```

### The Bug Location

**File:** `infrastructure/cloudformation/05-api.yaml`
**Lines:** 41-50

```yaml
APIKey:
  Type: AWS::ApiGateway::ApiKey
  DependsOn: APIDeployment        # <-- BUG: Wrong dependency
  Properties:
    Name: !Sub ${ProjectName}-${Environment}-api-key
    Description: API key for Brandpoint Hub integration
    Enabled: true
    StageKeys:
      - RestApiId: !Ref BrandpointAPI
        StageName: !Ref APIStageName
```

### Why This Fails

1. The `APIKey` resource uses `StageKeys` to associate the API key with a stage
2. For `StageKeys` to work, the **stage must already exist**
3. The dependency chain is:
   ```
   Methods → APIDeployment → APIStage → APIKey (should be)
   Methods → APIDeployment → APIKey (current - broken)
   ```
4. `APIKey` depends on `APIDeployment`, but `APIStage` is created from `APIDeployment`
5. CloudFormation creates `APIKey` before `APIStage` exists, causing the failure

### The Fix (DO NOT APPLY - Investigation Only)

The `DependsOn` should reference `APIStage` instead of `APIDeployment`:

```yaml
APIKey:
  Type: AWS::ApiGateway::ApiKey
  DependsOn: APIStage              # <-- Correct dependency
```

---

## Deployment Flow Analysis

### Successful Stages (Before Failure)

| Layer | Stack | Status | Duration |
|-------|-------|--------|----------|
| 0 | FoundationStack | CREATE_COMPLETE | ~3 min |
| 1 | StorageStack | CREATE_COMPLETE | ~1 min |
| 2 | DatabasesStack | CREATE_COMPLETE | ~14 min |
| 3 | SecretsStack | CREATE_COMPLETE | ~1 min |
| 4 | ComputeStack | CREATE_COMPLETE | ~8 min |
| 5 | OrchestrationStack | CREATE_FAILED | - |
| 6 | APIStack | CREATE_FAILED | - |

### Nested Stack Dependency Graph

```
FoundationStack
    ├── StorageStack
    ├── DatabasesStack
    └── SecretsStack
            └── ComputeStack
                    ├── OrchestrationStack  ← FAILS (cancelled)
                    └── APIStack            ← FAILS (APIKey bug)
                            └── MonitoringStack (never reached)
```

---

## CloudWatch Logs Analysis

### Log Groups Present

| Log Group | Status |
|-----------|--------|
| /aws/sagemaker/Endpoints/brandpoint-ai-dev-visibility-predictor | Active (health pings OK) |
| /aws/api-gateway/event-analytics-backend-dev | Active (legacy) |
| /aws/lambda/event-analytics-backend-dev-cubejs | Active (legacy) |

### SageMaker Endpoint Logs

The SageMaker endpoint was successfully created and is responding to health checks:
```
2026-01-21T23:07:00,201 [INFO] "GET /ping HTTP/1.1" 200
```

**Note:** SageMaker resources were provisioned successfully before the API layer failure caused rollback.

---

## AWS Resource State

### Resources Successfully Created (Then Rolled Back)

- VPC with CIDR 10.200.0.0/16
- Security Groups
- IAM Roles
- S3 Buckets (brandpoint-ai-dev-*)
- DynamoDB Tables
- OpenSearch Domain
- Neptune Cluster
- Lambda Functions (15)
- SageMaker Endpoint
- Secrets Manager Secrets

### Resources That Failed

- API Gateway REST API (partially created)
- API Gateway API Key (root cause of failure)
- API Gateway Stage
- Step Functions State Machines (cancelled due to parallel failure)

---

## Service Quotas (Verified OK)

| Service | Quota | Used | Available |
|---------|-------|------|-----------|
| VPCs | 5 | 1 | 4 |
| Elastic IPs | 5 | 0 | 5 |
| API Keys | 10000 | ~0 | ~10000 |
| Regional APIs | 600 | 1 | 599 |

Quotas are not the issue.

---

## Impact Assessment

### Time Wasted
- 10+ deployment attempts
- Each deployment takes ~25-30 minutes to reach failure point
- Each rollback takes ~45 minutes
- **Estimated wasted time: 10+ hours**

### Cost Impact
- SageMaker endpoints provisioned and deleted multiple times
- OpenSearch clusters provisioned and deleted multiple times
- Neptune clusters provisioned and deleted multiple times
- **Estimated wasted cost: $50-100 in ephemeral resources**

---

## Recommendations

### Immediate Fix Required

1. **Update `infrastructure/cloudformation/05-api.yaml` line 43:**
   - Change `DependsOn: APIDeployment` to `DependsOn: APIStage`

### Pre-Deployment Validation

2. **Add template validation to preflight checks:**
   - Validate all nested templates individually
   - Check for dependency cycles

### Testing Recommendations

3. **Before next deployment attempt:**
   - Deploy templates individually to isolate failures
   - Test API stack in isolation first
   - Consider using CloudFormation change sets to preview

---

## Files Involved

| File | Issue |
|------|-------|
| `infrastructure/cloudformation/05-api.yaml` | **BUG: Line 43 wrong dependency** |
| `infrastructure/cloudformation/main.yaml` | OK (orchestration is correct) |
| `scripts/deploy.sh` | OK |
| `scripts/brandpoint-deploy.sh` | OK |

---

## Appendix: Raw CloudFormation Events

### Most Recent Failure (2026-01-21 22:59 UTC)

```
22:59:59 brandpoint-ai-dev         ROLLBACK_IN_PROGRESS  [APIStack, OrchestrationStack] failed
22:59:59 OrchestrationStack        CREATE_FAILED         Resource creation cancelled
22:59:59 APIStack                  CREATE_FAILED         APIKey resource failed
22:59:25 OrchestrationStack        CREATE_IN_PROGRESS
22:59:25 APIStack                  CREATE_IN_PROGRESS
22:59:24 ComputeStack              CREATE_COMPLETE
22:51:00 ComputeStack              CREATE_IN_PROGRESS
22:50:59 DatabasesStack            CREATE_COMPLETE
22:37:09 StorageStack              CREATE_COMPLETE
22:36:33 SecretsStack              CREATE_COMPLETE
22:33:44 FoundationStack           CREATE_COMPLETE
22:33:35 brandpoint-ai-dev         CREATE_IN_PROGRESS
```

---

## Conclusion

The deployment failures are caused by a single bug in the CloudFormation template. The `APIKey` resource in `05-api.yaml` has an incorrect `DependsOn` directive pointing to `APIDeployment` when it should point to `APIStage`. This causes CloudFormation to attempt creating the API Key before the stage exists, which fails because `StageKeys` requires an existing stage.

**The fix is a one-line change.** Once corrected, deployments should complete successfully.

---

*Report generated from AWS CloudWatch Logs, CloudFormation Events, and CloudTrail data.*
