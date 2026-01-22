# Execution Checklist

**Print this page and check off items as you complete them.**

---

## Phase 1: Pre-Deployment Fixes

### Codename 37 Tasks

- [ ] **FIX-001:** Update `infrastructure/cloudformation/parameters/dev.json` line 24
  ```
  "ParameterValue": "https://hub.brandpoint.com"
  ```

- [ ] **FIX-002:** Update `infrastructure/cloudformation/00-foundation.yaml` line 222
  ```
  CidrIp: 172.30.0.0/16
  ```

- [ ] **Commit changes:**
  ```bash
  git add -A
  git commit -m "Fix Hub URL and Lambda CIDR for Brandpoint environment"
  git push origin main
  ```

### Brandpoint IT Tasks

- [ ] **FIX-004:** Enable Bedrock models in AWS Console
  - [ ] Navigate to: AWS Console → Amazon Bedrock → Model access
  - [ ] Request access to: `anthropic.claude-3-5-sonnet-*`
  - [ ] Request access to: `amazon.titan-embed-text-v2:0`
  - [ ] Accept EULA
  - [ ] Wait for approval confirmation

---

## Phase 2: Deployment

- [ ] **Pull latest code:**
  ```bash
  cd /path/to/AWS
  git pull origin main
  ```

- [ ] **Run deployment:**
  ```bash
  ./scripts/brandpoint-deploy.sh --env dev --profile brandpoint
  ```

- [ ] **Note the VPC CIDR selected:** `____________` (e.g., 10.200.0.0/16)

- [ ] **Wait for completion:** ~45-60 minutes

- [ ] **Verify status:**
  ```bash
  aws cloudformation describe-stacks --stack-name brandpoint-ai-dev --profile brandpoint --query "Stacks[0].StackStatus"
  ```
  Expected: `CREATE_COMPLETE`

---

## Phase 3: Post-Deployment Configuration

### VPC Peering (FIX-003a)

- [ ] **Get new VPC ID:**
  ```bash
  aws cloudformation describe-stacks --stack-name brandpoint-ai-dev --profile brandpoint --query "Stacks[0].Outputs[?OutputKey=='VPCId'].OutputValue" --output text
  ```
  VPC ID: `____________`

- [ ] **Create peering connection:**
  ```bash
  aws ec2 create-vpc-peering-connection --vpc-id [NEW_VPC_ID] --peer-vpc-id vpc-d26af3b7 --profile brandpoint
  ```
  Peering ID: `____________`

- [ ] **Accept peering:**
  ```bash
  aws ec2 accept-vpc-peering-connection --vpc-peering-connection-id [PEERING_ID] --profile brandpoint
  ```

- [ ] **Add route in new VPC** (to reach RDS):
  ```bash
  # Get private route table ID
  aws cloudformation describe-stacks --stack-name brandpoint-ai-dev --profile brandpoint --query "Stacks[0].Outputs[?OutputKey=='PrivateRouteTableId'].OutputValue" --output text

  # Add route
  aws ec2 create-route --route-table-id [PRIVATE_RT_ID] --destination-cidr-block 172.30.0.0/16 --vpc-peering-connection-id [PEERING_ID] --profile brandpoint
  ```

- [ ] **Add route in existing VPC** (to reach Lambda):
  ```bash
  # Get existing VPC route table
  aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-d26af3b7" "Name=association.main,Values=true" --profile brandpoint --query "RouteTables[0].RouteTableId" --output text

  # Add route (use the VPC CIDR you noted earlier)
  aws ec2 create-route --route-table-id [EXISTING_RT_ID] --destination-cidr-block [NEW_VPC_CIDR] --vpc-peering-connection-id [PEERING_ID] --profile brandpoint
  ```

### RDS Security Group (FIX-003b)

- [ ] **Add inbound rule:**
  ```bash
  aws ec2 authorize-security-group-ingress --group-id sg-5f91623b --protocol tcp --port 1433 --cidr [NEW_VPC_CIDR] --profile brandpoint
  ```

### Secrets Configuration (FIX-006)

- [ ] **OpenAI API Key:**
  ```bash
  aws secretsmanager put-secret-value --secret-id brandpoint-ai-dev-openai-api-key --secret-string '{"apiKey":"sk-ACTUAL-KEY"}' --profile brandpoint
  ```

- [ ] **Perplexity API Key:**
  ```bash
  aws secretsmanager put-secret-value --secret-id brandpoint-ai-dev-perplexity-api-key --secret-string '{"apiKey":"pplx-ACTUAL-KEY"}' --profile brandpoint
  ```

- [ ] **Gemini API Key:**
  ```bash
  aws secretsmanager put-secret-value --secret-id brandpoint-ai-dev-gemini-api-key --secret-string '{"apiKey":"ACTUAL-KEY"}' --profile brandpoint
  ```

- [ ] **Hub Service Account:**
  ```bash
  aws secretsmanager put-secret-value --secret-id brandpoint-ai-dev-hub-service-account-key --secret-string '{"apiKey":"ACTUAL-KEY","baseUrl":"https://hub.brandpoint.com/api"}' --profile brandpoint
  ```

- [ ] **ARA3 Database:**
  ```bash
  aws secretsmanager put-secret-value --secret-id brandpoint-ai-dev-ara3-database-readonly --secret-string '{"host":"brandpointdb.c5rp85tg25on.us-east-1.rds.amazonaws.com","port":"1433","database":"ARA3","username":"READONLY_USER","password":"PASSWORD","driver":"ODBC Driver 17 for SQL Server"}' --profile brandpoint
  ```

---

## Phase 4: Validation

- [ ] **Get API endpoint:**
  ```bash
  API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name brandpoint-ai-dev --profile brandpoint --query "Stacks[0].Outputs[?OutputKey=='APIEndpoint'].OutputValue" --output text)
  echo $API_ENDPOINT
  ```

- [ ] **Health check (no auth):**
  ```bash
  curl $API_ENDPOINT/health
  ```
  Expected: `{"status": "healthy", ...}`

- [ ] **Test OpenSearch connectivity:**
  ```bash
  aws lambda invoke --function-name brandpoint-ai-dev-health-check --profile brandpoint --payload '{"checkOpenSearch": true}' /tmp/r.json && cat /tmp/r.json
  ```

- [ ] **Test Neptune connectivity:**
  ```bash
  aws lambda invoke --function-name brandpoint-ai-dev-health-check --profile brandpoint --payload '{"checkNeptune": true}' /tmp/r.json && cat /tmp/r.json
  ```

- [ ] **Test RDS connectivity:**
  ```bash
  aws lambda invoke --function-name brandpoint-ai-dev-health-check --profile brandpoint --payload '{"checkDatabase": true}' /tmp/r.json && cat /tmp/r.json
  ```

---

## Final Steps

- [ ] **Enable scheduled jobs (optional):**
  ```bash
  ./scripts/ignite.sh --env dev --profile brandpoint
  ```

- [ ] **Document completion:**
  - Deployment successful: YES / NO
  - All tests passing: YES / NO
  - Date/Time completed: ____________
  - Completed by: ____________

---

## Quick Troubleshooting

| Symptom | Likely Cause | Check |
|---------|--------------|-------|
| Stack stuck in CREATE_IN_PROGRESS | OpenSearch/Neptune provisioning | Wait 15-20 more minutes |
| Stack ROLLBACK_COMPLETE | Resource creation failed | Check CloudFormation events |
| Lambda timeout on RDS | VPC peering not configured | Verify peering and routes |
| Bedrock access denied | EULA not accepted | Check Bedrock model access |
| API 403 error | Missing or invalid API key | Get key from API Gateway |

---

## Emergency Rollback

```bash
# Full stack deletion (DESTRUCTIVE - all data lost)
aws cloudformation delete-stack --stack-name brandpoint-ai-dev --profile brandpoint
```

---

*Keep this checklist with you during execution.*
