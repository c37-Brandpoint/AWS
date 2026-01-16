# Brandpoint AI Platform - Deployment Runbook

**One page. Three steps. That's it.**

---

## Prerequisites

Before you start, ensure you have:

- [ ] **AWS CLI** installed ([download](https://aws.amazon.com/cli/))
- [ ] **AWS credentials** configured (`aws configure` or SSO login)
- [ ] **Linux environment** (native Linux, WSL on Windows, or EC2)
- [ ] **Python 3** installed
- [ ] **API keys** ready: OpenAI, Perplexity, Gemini, Hub service account

---

## Step 1: Deploy

Run one command:

```bash
./scripts/brandpoint-deploy.sh --env dev
```

That's it. The script will:
- Check your AWS credentials and quotas
- Auto-select a safe VPC CIDR (no network conflicts)
- Deploy all infrastructure (30-45 min for first deploy)
- Run verification tests
- Guide you through secrets configuration

**For production:**
```bash
./scripts/brandpoint-deploy.sh --env prod
```

---

## Step 2: Configure Secrets

When prompted, copy and run these commands with your real API keys:

```bash
# OpenAI
aws secretsmanager put-secret-value \
  --secret-id brandpoint-ai-dev-openai-api-key \
  --secret-string '{"apiKey":"sk-YOUR-REAL-KEY"}' \
  --region us-east-1

# Perplexity
aws secretsmanager put-secret-value \
  --secret-id brandpoint-ai-dev-perplexity-api-key \
  --secret-string '{"apiKey":"pplx-YOUR-REAL-KEY"}' \
  --region us-east-1

# Gemini
aws secretsmanager put-secret-value \
  --secret-id brandpoint-ai-dev-gemini-api-key \
  --secret-string '{"apiKey":"YOUR-REAL-KEY"}' \
  --region us-east-1

# Hub Service Account
aws secretsmanager put-secret-value \
  --secret-id brandpoint-ai-dev-hub-service-account-key \
  --secret-string '{"apiKey":"YOUR-REAL-KEY"}' \
  --region us-east-1
```

---

## Step 3: Enable Scheduled Jobs

After secrets are configured:

```bash
./scripts/ignite.sh --env dev
```

This enables the Persona Agent schedule. The script will verify secrets are not placeholders before enabling.

---

## Common Issues & Fixes

| Problem | Solution |
|---------|----------|
| **"AWS credentials not configured"** | Run `aws configure` or check your AWS_PROFILE |
| **"Lambda builds require Linux"** | Use WSL on Windows, or run from Linux/EC2 |
| **"CIDR overlap detected"** | Script auto-selects safe CIDR, or use `--cidr 10.200.0.0/16` |
| **"No Elastic IPs available"** | Release unused EIPs or request quota increase in AWS Console |
| **"Secrets contain placeholder"** | Update secrets with real API keys (Step 2) |
| **Stack stuck in CREATE_IN_PROGRESS** | Wait - OpenSearch/Neptune take 15-30 min to provision |
| **Smoke test failures** | Re-run after 10-15 min - resources may still be provisioning |

---

## Useful Commands

```bash
# Check deployment status
aws cloudformation describe-stacks --stack-name brandpoint-ai-dev

# Re-run smoke tests
./scripts/smoke-test.sh dev us-east-1

# View API endpoint
aws cloudformation describe-stacks --stack-name brandpoint-ai-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' --output text

# Disable scheduled jobs
aws events disable-rule --name brandpoint-ai-dev-persona-agent-schedule --region us-east-1

# Complete rollback (deletes everything)
./scripts/rollback.sh dev us-east-1
```

---

## Resume After Interruption

If deployment was interrupted:

```bash
./scripts/brandpoint-deploy.sh --env dev --resume
```

---

## Support

**Technical Issues:** jake@codename37.com

**Full Documentation:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

*Document Version: 1.0 | January 2026*
