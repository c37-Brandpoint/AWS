# Brandpoint AWS Environment - CLI Access Guide

**Document ID:** BP-AWS-ACCESS-001
**Version:** 1.0
**Date:** 2026-01-21
**Author:** Codename 37
**Classification:** Internal - Technical Operations

---

## Overview

This guide provides comprehensive instructions for accessing the Brandpoint AWS environment using the AWS CLI. This is the production AWS account used by Brandpoint for all their infrastructure.

### Account Information

| Property | Value |
|----------|-------|
| AWS Account ID | `144105412483` |
| Account Alias | Brandpoint (Production) |
| Primary Region | `us-east-1` |
| IAM User | `codename37` |
| CLI Profile Name | `brandpoint` |

---

## Prerequisites

### 1. AWS CLI Installation

The AWS CLI v2 must be installed. We use a user-local installation (no sudo required).

**Check if installed:**
```bash
aws --version
# Expected: aws-cli/2.x.x Python/3.x.x Linux/...
```

**Install AWS CLI v2 (user-local):**
```bash
# Download installer
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"

# Unzip
cd /tmp && unzip -o awscliv2.zip

# Install to user directory (no sudo)
./aws/install -i ~/.local/aws-cli -b ~/.local/bin --update

# Add to PATH (add to ~/.bashrc for persistence)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
aws --version
```

### 2. AWS Credentials

Credentials are stored securely in Bitwarden under "Brandpoint AWS access key".

| Credential | Value |
|------------|-------|
| Access Key ID | `AKIASDDK2C6BXPLTPZOL` |
| Secret Access Key | *(Retrieve from Bitwarden)* |
| Region | `us-east-1` |

**SECURITY NOTES:**
- NEVER commit credentials to the repository
- NEVER share credentials via unencrypted channels
- Credentials are stored in `~/.aws/credentials` (local machine only)
- Rotate credentials periodically

---

## Configuration

### Step 1: Configure AWS Profile

Run the AWS configure command to set up the `brandpoint` profile:

```bash
aws configure --profile brandpoint
```

When prompted, enter:
```
AWS Access Key ID [None]: AKIASDDK2C6BXPLTPZOL
AWS Secret Access Key [None]: <from Bitwarden>
Default region name [None]: us-east-1
Default output format [None]: json
```

### Step 2: Verify Configuration

Check that the profile was created:
```bash
cat ~/.aws/credentials
```

Expected output:
```ini
[brandpoint]
aws_access_key_id = AKIASDDK2C6BXPLTPZOL
aws_secret_access_key = ****
```

Check the config:
```bash
cat ~/.aws/config
```

Expected output:
```ini
[profile brandpoint]
region = us-east-1
output = json
```

### Step 3: Test Connection

Verify you can connect to AWS:
```bash
aws sts get-caller-identity --profile brandpoint
```

Expected output:
```json
{
    "UserId": "AIDASDDK2C6BZONVJD5IX",
    "Account": "144105412483",
    "Arn": "arn:aws:iam::144105412483:user/codename37"
}
```

---

## Usage

### Using the Profile

Always include `--profile brandpoint` in your AWS CLI commands:

```bash
# List S3 buckets
aws s3 ls --profile brandpoint

# Describe EC2 instances
aws ec2 describe-instances --profile brandpoint

# List CloudFormation stacks
aws cloudformation list-stacks --profile brandpoint
```

### Setting Default Profile (Optional)

To avoid typing `--profile brandpoint` every time:

```bash
# For current session
export AWS_PROFILE=brandpoint

# Verify
aws sts get-caller-identity
# Should show Brandpoint account without --profile flag
```

Add to `~/.bashrc` for persistence:
```bash
echo 'export AWS_PROFILE=brandpoint' >> ~/.bashrc
source ~/.bashrc
```

---

## Current Permissions

The `codename37` user has the following verified permissions:

### Allowed Operations

| Service | Permission | Status |
|---------|------------|--------|
| CloudFormation | CreateStack, DeleteStack, DescribeStacks | ✅ Allowed |
| EC2 | CreateVpc, DescribeVpcs, DescribeInstances | ✅ Allowed |
| S3 | ListBuckets, GetObject, PutObject, DeleteObject | ✅ Allowed |
| Lambda | ListFunctions, InvokeFunction | ✅ Allowed |
| IAM | ListRoles | ✅ Allowed |
| Bedrock | InvokeModel, ListFoundationModels | ✅ Allowed |
| RDS | DescribeDBInstances | ✅ Allowed |
| Secrets Manager | GetSecretValue, PutSecretValue | ✅ Allowed |

### Denied Operations (Requires Escalation)

| Service | Permission | Status | Notes |
|---------|------------|--------|-------|
| IAM | CreateRole | ❌ Denied | Required for CloudFormation deployment |
| IAM | PutRolePolicy | ❌ Denied | Required for CloudFormation deployment |
| IAM | AttachRolePolicy | ❌ Denied | Required for CloudFormation deployment |
| IAM | GetUser | ❌ Denied | Cannot view own user details |
| IAM | ListAttachedUserPolicies | ❌ Denied | Cannot view own policies |

**Note:** IAM write permissions have been requested from Brandpoint IT (2026-01-21).

---

## Common Commands

### Account & Identity
```bash
# Who am I?
aws sts get-caller-identity --profile brandpoint

# List available regions
aws ec2 describe-regions --profile brandpoint --query "Regions[].RegionName"
```

### S3 Operations
```bash
# List all buckets
aws s3 ls --profile brandpoint

# List bucket contents
aws s3 ls s3://bucket-name --profile brandpoint

# Copy file to S3
aws s3 cp localfile.txt s3://bucket-name/ --profile brandpoint

# Sync directory
aws s3 sync ./local-dir s3://bucket-name/prefix --profile brandpoint
```

### EC2 & VPC
```bash
# List VPCs
aws ec2 describe-vpcs --profile brandpoint

# List instances
aws ec2 describe-instances --profile brandpoint --query "Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key=='Name'].Value|[0]]" --output table

# List security groups
aws ec2 describe-security-groups --profile brandpoint
```

### CloudFormation
```bash
# List stacks
aws cloudformation list-stacks --profile brandpoint --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Describe stack
aws cloudformation describe-stacks --stack-name stack-name --profile brandpoint

# Get stack outputs
aws cloudformation describe-stacks --stack-name stack-name --profile brandpoint --query "Stacks[0].Outputs"

# Watch stack events
watch -n 10 'aws cloudformation describe-stack-events --stack-name stack-name --profile brandpoint --query "StackEvents[0:5]" --output table'
```

### Lambda
```bash
# List functions
aws lambda list-functions --profile brandpoint

# Invoke function
aws lambda invoke --function-name function-name --profile brandpoint --payload '{}' response.json
```

### Bedrock
```bash
# List foundation models
aws bedrock list-foundation-models --profile brandpoint --region us-east-1

# Test model invocation (Claude 3 Sonnet)
echo '{"anthropic_version": "bedrock-2023-05-31", "max_tokens": 100, "messages": [{"role": "user", "content": "Hello"}]}' > /tmp/request.json

aws bedrock-runtime invoke-model \
  --profile brandpoint \
  --region us-east-1 \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --body fileb:///tmp/request.json \
  --content-type application/json \
  --accept application/json \
  /tmp/response.json

cat /tmp/response.json
```

### Secrets Manager
```bash
# List secrets
aws secretsmanager list-secrets --profile brandpoint

# Get secret value
aws secretsmanager get-secret-value --secret-id secret-name --profile brandpoint

# Update secret
aws secretsmanager put-secret-value --secret-id secret-name --secret-string '{"key":"value"}' --profile brandpoint
```

---

## Environment Details

### Existing Infrastructure

| Resource | Details |
|----------|---------|
| VPC | `vpc-d26af3b7` (172.30.0.0/16) - Main Brandpoint VPC |
| RDS | `brandpointdb.c5rp85tg25on.us-east-1.rds.amazonaws.com` (SQL Server) |
| RDS Security Group | `sg-5f91623b` |
| EC2 Instances | 5 total (4 running, 1 stopped) |
| S3 Buckets | 17 buckets |
| CloudFront | 3 distributions |

### AI Platform Resources (Post-Deployment)

| Resource | Expected Name |
|----------|---------------|
| CloudFormation Stack | `brandpoint-ai-dev` |
| VPC | New VPC (10.x.0.0/16 range) |
| Lambda Functions | `brandpoint-ai-dev-*` |
| API Gateway | `brandpoint-ai-dev-api` |
| OpenSearch | `brandpoint-ai-dev` |
| Neptune | `brandpoint-ai-dev` |

---

## Troubleshooting

### "Unable to locate credentials"
```bash
# Check if profile exists
cat ~/.aws/credentials | grep brandpoint

# Reconfigure if needed
aws configure --profile brandpoint
```

### "Access Denied" errors
```bash
# Verify identity
aws sts get-caller-identity --profile brandpoint

# Check if permission is in denied list above
# If new denial, document and escalate to Brandpoint IT
```

### "The config profile (brandpoint) could not be found"
```bash
# Check config file
cat ~/.aws/config

# Should have:
# [profile brandpoint]
# region = us-east-1
```

### Timeout on AWS commands
```bash
# Check network connectivity
curl -I https://sts.us-east-1.amazonaws.com

# Try with explicit region
aws sts get-caller-identity --profile brandpoint --region us-east-1
```

---

## Security Best Practices

1. **Never commit credentials** - AWS credentials must never be in git
2. **Use profiles** - Always use named profiles, never default credentials
3. **Principle of least privilege** - Only request permissions you need
4. **Audit trail** - All API calls are logged in CloudTrail
5. **Credential rotation** - Request new keys periodically
6. **MFA** - Enable MFA on IAM user if available

---

## Support Contacts

| Role | Contact | Responsibility |
|------|---------|----------------|
| AWS Access Issues | Brandpoint IT (Adam McBroom) | IAM permissions, account access |
| Technical Support | jake@codename37.com | CLI usage, deployment issues |
| Security Concerns | Brandpoint IT | Credential rotation, access review |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-21 | Codename 37 | Initial document |

---

*Document End*
