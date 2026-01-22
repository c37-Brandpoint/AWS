# Fix Plan - Executive Summary

**Date:** 2026-01-21
**Project:** Brandpoint AI Platform
**Status:** Ready for Execution

---

## Overview

10 issues identified during repo validation. 3 critical, 3 high, 2 medium, 2 low.

**Total Remediation Time:** 5-7 hours

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

| Owner | Tasks | Time |
|-------|-------|------|
| **Codename 37** | FIX-001, FIX-002, FIX-010 (code changes) | 30 min |
| **Brandpoint IT** | FIX-003, FIX-004, FIX-006, FIX-007 (AWS config) | 3-4 hours |
| **Auto** | FIX-005 (S3 sync during deploy) | 0 min |
| **Optional** | FIX-008, FIX-009 (cleanup) | 15 min |

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

### Phase 1 Go Criteria
- [ ] Hub URL decision made
- [ ] Code changes committed and pushed
- [ ] Bedrock model access approved

### Phase 2 Go Criteria
- [ ] Phase 1 complete
- [ ] Deployment machine has latest code
- [ ] AWS credentials configured

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
