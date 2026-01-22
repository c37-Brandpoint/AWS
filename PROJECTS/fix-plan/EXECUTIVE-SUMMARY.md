# Fix Plan - Executive Summary

**Date:** 2026-01-21
**Project:** Brandpoint AI Platform
**Status:** ⚠️ Phase 1 Complete - Blocked on IAM Permissions
**Last Updated:** 2026-01-21

---

## Current Status

| Phase | Status |
|-------|--------|
| Phase 1: Pre-Deployment Fixes | ✅ **COMPLETE** |
| Phase 2: Deployment | ⚠️ **BLOCKED** - Awaiting IAM permissions |
| Phase 3: Post-Deployment Config | Pending |
| Phase 4: Validation | Pending |

**Blocker:** `codename37` IAM user lacks `iam:CreateRole` permission. Email sent to Brandpoint IT requesting admin access.

---

## Overview

11 issues identified (10 original + 1 discovered during execution). 3 critical, 3 high, 2 medium, 2 low, 1 blocker.

**Total Remediation Time:** 5-7 hours (once IAM permissions granted)

---

## Critical Path

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXECUTION TIMELINE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 1: Pre-Deployment (1-2 hours)                                        │
│  ─────────────────────────────────────                                      │
│  ├── FIX-001: Update Hub URL in dev.json ──────────────► Codename 37       │
│  ├── FIX-002: Fix Lambda CIDR in foundation.yaml ──────► Codename 37       │
│  ├── FIX-004: Enable Bedrock models ───────────────────► Brandpoint IT     │
│  └── Git commit & push ────────────────────────────────► Codename 37       │
│                                                                              │
│  PHASE 2: Deployment (45-60 minutes)                                        │
│  ───────────────────────────────────                                        │
│  ├── Git pull on deployment machine                                         │
│  ├── Run: ./scripts/brandpoint-deploy.sh --env dev                         │
│  └── FIX-005: Auto-resolves (templates sync to S3)                         │
│                                                                              │
│  PHASE 3: Post-Deployment (2-3 hours)                                       │
│  ────────────────────────────────────                                       │
│  ├── FIX-003a: Create VPC Peering ─────────────────────► Brandpoint IT     │
│  ├── FIX-003b: Update RDS Security Group ──────────────► Brandpoint IT     │
│  └── FIX-006: Configure all secrets ───────────────────► Brandpoint IT     │
│                                                                              │
│  PHASE 4: Validation (1 hour)                                               │
│  ─────────────────────────────                                              │
│  ├── Health check tests                                                     │
│  ├── Connectivity tests                                                     │
│  └── End-to-end API tests                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Who Does What

| Owner | Tasks | Status |
|-------|-------|--------|
| **Codename 37** | FIX-001, FIX-002, FIX-010 (code changes) | ✅ FIX-001, FIX-002 COMPLETE |
| **Brandpoint IT** | FIX-003, FIX-004, FIX-006, FIX-007, **NEW-001** (AWS config) | FIX-004 verified OK, **NEW-001 BLOCKING** |
| **Auto** | FIX-005 (S3 sync during deploy) | Pending deployment |
| **Optional** | FIX-008, FIX-009 (cleanup) | Pending |

### ⚠️ Immediate Action Required

**Brandpoint IT must grant IAM permissions** before deployment can proceed:
- User: `codename37`
- Required: `iam:CreateRole`, `iam:PutRolePolicy`, `iam:AttachRolePolicy`, `iam:PassRole`
- Alternative: Grant admin access or run deployment with admin user

---

## Risk Matrix

| Issue | If Not Fixed | Likelihood | Impact |
|-------|--------------|------------|--------|
| FIX-001 | Lambda API calls fail | 100% | Deployment works, runtime fails |
| FIX-002 | Lambda can't reach RDS | 100% | ML training impossible |
| FIX-003 | Same as FIX-002 | 100% | ML training impossible |
| FIX-004 | Bedrock calls fail | 100% | Query generation fails |
| FIX-006 | External APIs fail | 100% | Persona agent fails |

---

## Decision Points

### Before Phase 1

**Q: Does Brandpoint have a staging Hub environment?**
- If YES → Use that URL in dev.json
- If NO → Use production URL (acceptable for POC)

### Before Phase 3

**Q: What VPC CIDR was selected during deployment?**
- Note this value (likely 10.200.0.0/16)
- Use it for RDS security group update

### After Phase 4

**Q: Are all validation tests passing?**
- If YES → Enable scheduled jobs (ignite.sh)
- If NO → Review logs, troubleshoot, retry

---

## Quick Commands

### Check Deployment Status
```bash
aws cloudformation describe-stacks --stack-name brandpoint-ai-dev --profile brandpoint --query "Stacks[0].StackStatus"
```

### Get API Endpoint
```bash
aws cloudformation describe-stacks --stack-name brandpoint-ai-dev --profile brandpoint --query "Stacks[0].Outputs[?OutputKey=='APIEndpoint'].OutputValue" --output text
```

### Test Health
```bash
curl $(aws cloudformation describe-stacks --stack-name brandpoint-ai-dev --profile brandpoint --query "Stacks[0].Outputs[?OutputKey=='APIEndpoint'].OutputValue" --output text)/health
```

---

## Go/No-Go Checklist

### Phase 1 Go Criteria ✅ COMPLETE
- [x] Hub URL decision made → Using production `hub.brandpoint.com`
- [x] Code changes committed and pushed → Commit `098abc7`
- [x] Bedrock model access approved → Already configured and verified

### Phase 2 Go Criteria ⚠️ BLOCKED
- [x] Phase 1 complete
- [x] Deployment machine has latest code
- [x] AWS credentials configured
- [ ] **IAM CreateRole permission granted** ← BLOCKING

### Phase 3 Go Criteria
- [ ] Deployment successful (CREATE_COMPLETE)
- [ ] VPC CIDR noted
- [ ] API keys ready

### Phase 4 Go Criteria
- [ ] VPC peering established
- [ ] RDS security group updated
- [ ] All secrets configured

---

## Escalation Path

| Issue | First Contact | Escalation |
|-------|---------------|------------|
| Code changes | jake@codename37.com | michael@codename37.com |
| AWS access | Adam McBroom | Brandpoint IT Manager |
| RDS credentials | Brandpoint DBA | Adam McBroom |
| API keys | External vendor | Brandpoint IT |

---

*See FIX-PLAN.md for detailed procedures.*
