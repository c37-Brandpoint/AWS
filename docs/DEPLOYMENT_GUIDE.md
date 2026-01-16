# Brandpoint AI Platform - Complete Deployment Guide

## For Brandpoint IT Team

**Document Version:** 3.0
**Last Updated:** January 2026

---

## CHOOSE YOUR PATH

### Option A: One-Command Deployment (Recommended - 30-45 minutes)

**Run one command and follow the prompts:**

```bash
git clone git@github.com:c37-Brandpoint/AWS.git && cd AWS
./scripts/brandpoint-deploy.sh --env dev
```

The script handles everything:
1. Validates your AWS credentials and quotas
2. **Auto-selects a safe VPC CIDR** (no manual network configuration needed!)
3. Deploys all infrastructure
4. Runs verification tests
5. Shows you exactly which commands to run for secrets
6. Enables scheduled jobs when you're ready

**Prerequisites:**
- AWS CLI installed and configured (`aws configure`)
- Python 3.11+ with pip
- Git
- **Linux environment** (required for Lambda packaging - use WSL on Windows)

**For production:**
```bash
./scripts/brandpoint-deploy.sh --env prod
```

**Resume interrupted deployment:**
```bash
./scripts/brandpoint-deploy.sh --env dev --resume
```

**Rollback (if needed):**
```bash
./scripts/rollback.sh dev us-east-1
```

**For a one-page reference guide, see: [BRANDPOINT_RUNBOOK.md](BRANDPOINT_RUNBOOK.md)**

After deployment, continue to [Step 12: Network Configuration for RDS Access](#step-12-network-configuration-for-rds-access) for VPC peering setup.

---

### Option B: Step-by-Step Guide (Detailed - 3-4 hours)

If you prefer a detailed walkthrough with screenshots and explanations, continue to the full guide below.

---

## TABLE OF CONTENTS

1. [Before You Begin](#1-before-you-begin)
2. [Prerequisites Checklist](#2-prerequisites-checklist)
3. [Step 1: AWS Console Access](#step-1-aws-console-access)
4. [Step 2: Create S3 Buckets](#step-2-create-s3-buckets)
5. [Step 3: Install Required Tools](#step-3-install-required-tools)
6. [Step 4: Clone the Repository](#step-4-clone-the-repository)
7. [Step 5: Package Lambda Functions](#step-5-package-lambda-functions)
8. [Step 6: Upload Files to S3](#step-6-upload-files-to-s3)
9. [Step 7: Deploy CloudFormation Stack](#step-7-deploy-cloudformation-stack)
10. [Step 8: Configure Secrets](#step-8-configure-secrets)
11. [Step 9: Verify Deployment](#step-9-verify-deployment)
12. [Step 10: Test the System](#step-10-test-the-system)
13. [Step 11: Grant Consultant Access](#step-11-grant-consultant-access)
14. [Step 12: Network Configuration for RDS Access](#step-12-network-configuration-for-rds-access)
15. [Step 13: Set Up VPC Peering](#step-13-set-up-vpc-peering)
16. [Troubleshooting Guide](#troubleshooting-guide)
17. [Rollback Instructions](#rollback-instructions)
18. [Support Contacts](#support-contacts)

---

## 1. BEFORE YOU BEGIN

### What This Guide Will Help You Deploy

You are deploying the **Brandpoint AI Platform**, which includes:
- A web API for AI visibility predictions
- Lambda functions (serverless code that runs automatically)
- Databases for storing data (DynamoDB, OpenSearch, Neptune)
- Machine learning endpoints (SageMaker)
- Workflow automation (Step Functions)

### Important Notes

> ⚠️ **READ THIS FIRST**
> - Follow each step in order. Do not skip steps.
> - If something fails, stop and refer to the Troubleshooting section.
> - All commands should be run exactly as shown (copy/paste recommended).
> - This deployment is for the **dev** environment. Do NOT deploy to prod without approval.

### Terminology Quick Reference

| Term | What It Means |
|------|---------------|
| S3 Bucket | A folder in the cloud for storing files |
| CloudFormation | AWS tool that creates resources from a template file |
| Lambda | Code that runs without a server |
| Stack | A group of AWS resources created together |
| ARN | Amazon Resource Name - a unique ID for AWS resources |
| Region | Physical location of AWS data centers (we use us-east-1) |

---

## 2. PREREQUISITES CHECKLIST

Before starting, confirm you have the following:

### AWS Account Requirements

- [ ] AWS Console login credentials (username and password)
- [ ] IAM user with **AdministratorAccess** permission
- [ ] Access to the **us-east-1** region (N. Virginia)

### API Keys Required (Get from Project Manager)

- [ ] OpenAI API key (for ChatGPT)
- [ ] Perplexity API key
- [ ] Google Gemini API key
- [ ] Anthropic API key (for Claude - may not be needed if using Bedrock)
- [ ] Hub service account API key (from Brandpoint Hub team)

### Your Computer Requirements

- [ ] Windows 10/11, Mac, or Linux computer
- [ ] Internet connection
- [ ] Ability to install software (admin rights)
- [ ] At least 2GB free disk space

### Software You Will Install (Step 3 covers this)

These tools are required. Step 3 provides detailed installation instructions.

- [ ] **AWS CLI** - Command-line tool to interact with AWS
- [ ] **Python 3.11+** - Required for packaging Lambda functions
- [ ] **pip** - Python package manager (included with Python)
- [ ] **Git** - Version control (also provides Git Bash on Windows)
- [ ] **zip** - For creating Lambda deployment packages
  - *Windows:* Included with Git Bash (installed with Git)
  - *Mac/Linux:* Pre-installed on most systems

> **Windows Users:** You will need **Git Bash** (comes with Git) or **WSL** to run the deployment scripts. The scripts are bash scripts and won't run in standard Command Prompt.

### Information to Collect Before Starting

Write these down - you'll need them:

```
AWS Account ID: ______________________ (12-digit number)
AWS Region: us-east-1 (do not change)
Environment: dev (do not change for initial deployment)
```

---

## STEP 1: AWS CONSOLE ACCESS

### 1.1 Log Into AWS Console

1. Open your web browser (Chrome recommended)

2. Go to: **https://console.aws.amazon.com**

3. You will see a login page. Enter:
   - **Account ID or alias**: (provided by your AWS administrator)
   - Click **Next**

4. Enter your:
   - **IAM user name**: (your username)
   - **Password**: (your password)
   - Click **Sign in**

### 1.2 Select the Correct Region

**THIS IS CRITICAL - WRONG REGION = DEPLOYMENT FAILURE**

1. Look at the top-right corner of the AWS Console

2. You will see a region name (e.g., "Ohio" or "N. Virginia")

3. Click on the region name

4. A dropdown menu appears. Select: **US East (N. Virginia) us-east-1**

5. Verify it now shows **N. Virginia** in the top-right corner

```
✅ CHECKPOINT: You should see "N. Virginia" in the top-right corner
```

### 1.3 Find Your AWS Account ID

1. Click on your username in the top-right corner (next to the region)

2. A dropdown appears showing:
   - Account ID: **123456789012** (this is a 12-digit number)

3. Write down your Account ID: ______________________

4. You'll need this later

---

## STEP 2: CREATE S3 BUCKETS

You need to create 2 storage buckets before deployment.

### 2.1 Navigate to S3

1. In the AWS Console, click the **Search bar** at the top

2. Type: **S3**

3. Click on **S3** in the search results (it has an icon of green buckets)

4. You are now in the S3 Dashboard

### 2.2 Create the Lambda Code Bucket

This bucket stores the Lambda function code.

1. Click the orange **Create bucket** button

2. Fill in the following:

   **General configuration**
   - **Bucket name**: `brandpoint-ai-dev-lambda-code-ACCOUNTID`
     - Replace ACCOUNTID with your 12-digit account ID
     - Example: `brandpoint-ai-dev-lambda-code-123456789012`

   - **AWS Region**: US East (N. Virginia) us-east-1
     - ⚠️ Make sure this says us-east-1

   **Object Ownership**
   - Keep default: **ACLs disabled (recommended)**

   **Block Public Access settings**
   - Keep default: ✅ **Block all public access** (checkmark should be ON)

   **Bucket Versioning**
   - Select: **Enable**

   **Default encryption**
   - Keep default: **Server-side encryption with Amazon S3 managed keys (SSE-S3)**

3. Scroll down and click **Create bucket**

4. You should see a green banner: "Successfully created bucket"

```
✅ CHECKPOINT: You should see your new bucket in the S3 bucket list
   Bucket name: brandpoint-ai-dev-lambda-code-YOURACCOUNTID
```

### 2.3 Create the CloudFormation Templates Bucket

This bucket stores the deployment templates.

1. Click **Create bucket** again

2. Fill in:

   **General configuration**
   - **Bucket name**: `brandpoint-ai-dev-templates-ACCOUNTID`
     - Replace ACCOUNTID with your 12-digit account ID
     - Example: `brandpoint-ai-dev-templates-123456789012`

   - **AWS Region**: US East (N. Virginia) us-east-1

   **All other settings**: Keep the same defaults as above
   - Block public access: ON
   - Versioning: Enable

3. Click **Create bucket**

```
✅ CHECKPOINT: You now have 2 buckets in S3:
   1. brandpoint-ai-dev-lambda-code-ACCOUNTID
   2. brandpoint-ai-dev-templates-ACCOUNTID
```

---

## STEP 3: INSTALL REQUIRED TOOLS

You need to install command-line tools on your computer.

### 3.1 For Windows Users

#### Install AWS CLI

1. Download AWS CLI:
   - Go to: https://awscli.amazonaws.com/AWSCLIV2.msi
   - The download should start automatically

2. Run the installer:
   - Double-click the downloaded file `AWSCLIV2.msi`
   - Click **Next** on each screen
   - Click **Install**
   - Click **Finish**

3. Verify installation:
   - Press `Windows Key + R`
   - Type `cmd` and press Enter
   - In the black command window, type:
     ```
     aws --version
     ```
   - You should see something like: `aws-cli/2.x.x Python/3.x.x Windows/10`

#### Install Python

1. Download Python:
   - Go to: https://www.python.org/downloads/
   - Click **Download Python 3.11.x** (or latest)

2. Run the installer:
   - **IMPORTANT**: Check the box ✅ **Add Python to PATH** at the bottom
   - Click **Install Now**
   - Click **Close** when done

3. Verify installation:
   - Open a new Command Prompt (close the old one first)
   - Type:
     ```
     python --version
     ```
   - You should see: `Python 3.11.x`

#### Install Git

1. Download Git:
   - Go to: https://git-scm.com/download/win
   - Download should start automatically

2. Run the installer:
   - Click **Next** on all screens (accept defaults)
   - Click **Install**
   - Click **Finish**

3. Verify installation:
   - Open a new Command Prompt
   - Type:
     ```
     git --version
     ```
   - You should see: `git version 2.x.x`

### 3.2 For Mac Users

#### Install Homebrew (Package Manager)

1. Open Terminal:
   - Press `Command + Space`
   - Type `Terminal` and press Enter

2. Install Homebrew by pasting this command:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. Press Enter and wait (this takes a few minutes)

4. When prompted for your password, type it (you won't see characters as you type)

#### Install AWS CLI, Python, and Git

In Terminal, run these commands one at a time:

```bash
brew install awscli
```

```bash
brew install python@3.11
```

```bash
brew install git
```

#### Verify Installations

```bash
aws --version
python3 --version
git --version
```

### 3.3 Configure AWS CLI

This connects your command line to your AWS account.

1. Open Command Prompt (Windows) or Terminal (Mac)

2. Type:
   ```
   aws configure
   ```

3. You will be prompted for 4 things. Enter them one at a time:

   ```
   AWS Access Key ID [None]: YOUR_ACCESS_KEY_ID
   AWS Secret Access Key [None]: YOUR_SECRET_ACCESS_KEY
   Default region name [None]: us-east-1
   Default output format [None]: json
   ```

   > **Where do I get my Access Key?**
   > - Go to AWS Console → Search for "IAM" → Click IAM
   > - In the left menu, click "Users"
   > - Click on your username
   > - Click the "Security credentials" tab
   > - Under "Access keys", click "Create access key"
   > - Select "Command Line Interface (CLI)"
   > - Check the confirmation box and click "Next"
   > - Click "Create access key"
   > - **SAVE THESE IMMEDIATELY** - you can only see the secret key once!
   > - Download the .csv file as backup

4. Verify AWS CLI is connected:
   ```
   aws sts get-caller-identity
   ```

   You should see your account ID and username in the output.

```
✅ CHECKPOINT: AWS CLI shows your account information
```

---

## STEP 4: CLONE THE REPOSITORY

Download the deployment files to your computer.

### 4.1 Create a Working Directory

**For Windows:**
```cmd
mkdir C:\brandpoint
cd C:\brandpoint
```

**For Mac:**
```bash
mkdir ~/brandpoint
cd ~/brandpoint
```

### 4.2 Clone the Repository

> **Note**: You may need a GitHub account and SSH key configured. If the command below fails, contact the development team for repository access.

```bash
git clone git@github.com:c37-Brandpoint/AWS.git
```

If you don't have SSH configured, try HTTPS instead:
```bash
git clone https://github.com/c37-Brandpoint/AWS.git
```

### 4.3 Navigate to the Project Directory

**For Windows:**
```cmd
cd AWS
dir
```

**For Mac:**
```bash
cd AWS
ls -la
```

You should see folders like:
- `docs/`
- `infrastructure/`
- `scripts/`

```
✅ CHECKPOINT: You can see the infrastructure and scripts folders
```

---

## STEP 5: PACKAGE LAMBDA FUNCTIONS

Create deployment packages for all Lambda functions.

### 5.1 Install Python Dependencies

**For Windows:**
```cmd
pip install boto3 requests opensearch-py gremlinpython requests-aws4auth
```

**For Mac:**
```bash
pip3 install boto3 requests opensearch-py gremlinpython requests-aws4auth
```

### 5.2 Run the Packaging Script

**For Windows:**
```cmd
cd scripts
bash package-lambdas.sh
```

> If `bash` doesn't work on Windows, you have two options:
>
> **Option A**: Use Git Bash
> - Right-click in the scripts folder
> - Select "Git Bash Here"
> - Run: `./package-lambdas.sh`
>
> **Option B**: Use WSL (Windows Subsystem for Linux)
> - Open PowerShell as Administrator
> - Run: `wsl --install`
> - Restart your computer
> - Open "Ubuntu" from Start Menu
> - Navigate to your project and run the script

**For Mac:**
```bash
cd scripts
chmod +x package-lambdas.sh
./package-lambdas.sh
```

### 5.3 Verify Packages Were Created

Check that ZIP files were created:

**For Windows (in Git Bash or WSL):**
```bash
ls -la ../build/lambda/*.zip
```

**For Mac:**
```bash
ls -la ../build/lambda/*.zip
```

You should see approximately 15 ZIP files, including:
- `load-persona.zip`
- `generate-queries.zip`
- `execute-query.zip`
- `analyze-visibility.zip`
- `store-results.zip`
- ... and more

```
✅ CHECKPOINT: You see 15 .zip files in the build/lambda directory
```

---

## STEP 6: UPLOAD FILES TO S3

Upload the Lambda packages and CloudFormation templates to S3.

### 6.1 Upload Lambda Packages

Replace `ACCOUNTID` with your 12-digit AWS account ID in the commands below.

**For Windows (Git Bash) and Mac:**

```bash
# Navigate to project root
cd /path/to/brandpoint/AWS

# Upload all Lambda ZIP files
aws s3 sync build/lambda/ s3://brandpoint-ai-dev-lambda-code-ACCOUNTID/functions/ --exclude "*" --include "*.zip"
```

Example with real account ID:
```bash
aws s3 sync build/lambda/ s3://brandpoint-ai-dev-lambda-code-123456789012/functions/ --exclude "*" --include "*.zip"
```

### 6.2 Upload CloudFormation Templates

```bash
aws s3 sync infrastructure/cloudformation/ s3://brandpoint-ai-dev-templates-ACCOUNTID/cloudformation/ --exclude "parameters/*"
```

### 6.3 Verify Uploads

Check Lambda code bucket:
```bash
aws s3 ls s3://brandpoint-ai-dev-lambda-code-ACCOUNTID/functions/
```

Check templates bucket:
```bash
aws s3 ls s3://brandpoint-ai-dev-templates-ACCOUNTID/cloudformation/
```

You should see all your files listed.

```
✅ CHECKPOINT:
   - Lambda bucket contains 15 ZIP files in functions/
   - Templates bucket contains 9 YAML files in cloudformation/
```

---

## STEP 7: DEPLOY CLOUDFORMATION STACK

This is the main deployment step that creates all AWS resources.

### 7.1 Navigate to CloudFormation in AWS Console

1. Go to AWS Console: https://console.aws.amazon.com

2. Verify you're in **N. Virginia (us-east-1)** region

3. In the search bar, type: **CloudFormation**

4. Click on **CloudFormation** in the results

### 7.2 Create a New Stack

1. Click the orange **Create stack** button

2. Select **With new resources (standard)**

### 7.3 Specify Template

1. Under "Prerequisite - Prepare template", select:
   - ✅ **Template is ready**

2. Under "Specify template", select:
   - ✅ **Amazon S3 URL**

3. In the "Amazon S3 URL" text box, enter:
   ```
   https://brandpoint-ai-dev-templates-ACCOUNTID.s3.amazonaws.com/cloudformation/main.yaml
   ```
   (Replace ACCOUNTID with your 12-digit account ID)

4. Click **Next**

### 7.4 Specify Stack Details

1. **Stack name**: Enter `brandpoint-ai-dev`

2. **Parameters** - Fill in each field:

   | Parameter | Value to Enter |
   |-----------|----------------|
   | Environment | `dev` |
   | ProjectName | `brandpoint-ai` |
   | TemplatesBucket | `brandpoint-ai-dev-templates-ACCOUNTID` |
   | LambdaCodeBucket | `brandpoint-ai-dev-lambda-code-ACCOUNTID` |
   | HubApiBaseUrl | `https://hub-staging.brandpoint.com` |
   | OpenSearchInstanceType | `t3.small.search` |
   | OpenSearchInstanceCount | `2` |
   | OpenSearchVolumeSize | `20` |
   | NeptuneInstanceClass | `db.t3.medium` |
   | SageMakerInstanceType | `ml.t3.medium` |
   | AlertEmail | `your-email@brandpoint.com` |
   | MonthlyBudgetLimit | `700` |
   | PersonaAgentSchedule | `cron(0 6 * * ? *)` |

3. Click **Next**

### 7.5 Configure Stack Options

1. **Tags** (optional but recommended):
   - Click "Add new tag"
   - Key: `Project` Value: `brandpoint-ai`
   - Click "Add new tag"
   - Key: `Environment` Value: `dev`

2. **Permissions**:
   - Leave as default (use IAM role from your account)

3. **Stack failure options**:
   - Select: ✅ **Roll back all stack resources**

4. Click **Next**

### 7.6 Review and Create

1. Scroll down and review all your settings

2. At the bottom, you'll see checkboxes for acknowledgments:
   - ✅ Check: "I acknowledge that AWS CloudFormation might create IAM resources with custom names"
   - ✅ Check: "I acknowledge that AWS CloudFormation might require the following capability: CAPABILITY_AUTO_EXPAND"

3. Click **Submit**

### 7.7 Monitor Deployment Progress

1. You'll see the stack with status **CREATE_IN_PROGRESS**

2. Click on the stack name **brandpoint-ai-dev**

3. Click the **Events** tab to see progress

4. Click the 🔄 refresh button every 30-60 seconds to see new events

5. **This deployment takes approximately 30-45 minutes** because:
   - OpenSearch cluster takes ~15-20 minutes
   - Neptune cluster takes ~10-15 minutes
   - Other resources take ~5-10 minutes

### 7.8 Deployment Status Meanings

| Status | Meaning | Action |
|--------|---------|--------|
| CREATE_IN_PROGRESS | Still deploying | Wait and refresh |
| CREATE_COMPLETE | Success! | Proceed to next step |
| CREATE_FAILED | Something went wrong | See Troubleshooting section |
| ROLLBACK_IN_PROGRESS | Cleaning up after failure | Wait, then troubleshoot |
| ROLLBACK_COMPLETE | Cleanup done | Fix issue and redeploy |

```
✅ CHECKPOINT: Stack status shows CREATE_COMPLETE
   (All nested stacks should also show CREATE_COMPLETE)
```

---

## STEP 8: CONFIGURE SECRETS

Now you need to add the actual API keys to AWS Secrets Manager.

### 8.1 Navigate to Secrets Manager

1. In AWS Console search bar, type: **Secrets Manager**

2. Click on **Secrets Manager**

### 8.2 Update OpenAI API Key

1. Find and click on: `brandpoint-ai-dev-openai-api-key`

2. Click **Retrieve secret value**

3. Click **Edit**

4. Replace the placeholder with your actual API key:
   ```json
   {"apiKey": "sk-your-actual-openai-api-key-here"}
   ```

5. Click **Save**

### 8.3 Update Perplexity API Key

1. Go back to Secrets Manager list

2. Click on: `brandpoint-ai-dev-perplexity-api-key`

3. Click **Retrieve secret value** → **Edit**

4. Enter:
   ```json
   {"apiKey": "pplx-your-actual-perplexity-api-key-here"}
   ```

5. Click **Save**

### 8.4 Update Gemini API Key

1. Click on: `brandpoint-ai-dev-gemini-api-key`

2. Click **Retrieve secret value** → **Edit**

3. Enter:
   ```json
   {"apiKey": "your-actual-gemini-api-key-here"}
   ```

4. Click **Save**

### 8.5 Update Hub Service Account Key

1. Click on: `brandpoint-ai-dev-hub-service-account-key`

2. Click **Retrieve secret value** → **Edit**

3. Enter:
   ```json
   {"apiKey": "your-hub-service-account-api-key-here"}
   ```

4. Click **Save**

### 8.6 Update Database Connection (if needed)

1. Click on: `brandpoint-ai-dev-hub-database-readonly`

2. This is for direct database access. Fill in if provided:
   ```json
   {
     "host": "your-database-server.brandpoint.com",
     "port": "1433",
     "database": "ARA3",
     "username": "readonly_user",
     "password": "your-password-here"
   }
   ```

3. Click **Save**

```
✅ CHECKPOINT: All 5 secrets have been updated with real values
```

---

## STEP 9: VERIFY DEPLOYMENT

Confirm everything was created correctly.

> **Quick Verification:** Run the automated smoke test to verify all resources:
> ```bash
> ./scripts/smoke-test.sh dev us-east-1
> ```
> This checks all major components automatically. Continue below for manual verification.

### 9.1 Check CloudFormation Outputs

1. Go to **CloudFormation** in AWS Console

2. Click on the main stack: `brandpoint-ai-dev`

3. Click the **Outputs** tab

4. You should see values for:
   - APIEndpoint (something like `https://xxxxxxx.execute-api.us-east-1.amazonaws.com/dev`)
   - OpenSearchEndpoint
   - NeptuneEndpoint
   - SageMakerEndpoint

5. **Write down the APIEndpoint** - you'll need it for testing:
   ```
   API Endpoint: ________________________________
   ```

### 9.2 Verify Lambda Functions

1. Search for **Lambda** in AWS Console

2. Click on **Lambda**

3. You should see 15 functions starting with `brandpoint-ai-dev-`:
   - [ ] brandpoint-ai-dev-load-persona
   - [ ] brandpoint-ai-dev-generate-queries
   - [ ] brandpoint-ai-dev-execute-query-chatgpt
   - [ ] brandpoint-ai-dev-execute-query-perplexity
   - [ ] brandpoint-ai-dev-execute-query-gemini
   - [ ] brandpoint-ai-dev-execute-query-claude
   - [ ] brandpoint-ai-dev-analyze-visibility
   - [ ] brandpoint-ai-dev-store-results
   - [ ] brandpoint-ai-dev-content-ingestion
   - [ ] brandpoint-ai-dev-graph-update
   - [ ] brandpoint-ai-dev-similarity-search
   - [ ] brandpoint-ai-dev-graph-query
   - [ ] brandpoint-ai-dev-insights-generator
   - [ ] brandpoint-ai-dev-prediction-api
   - [ ] brandpoint-ai-dev-persona-api
   - [ ] brandpoint-ai-dev-intelligence-api
   - [ ] brandpoint-ai-dev-health-check

### 9.3 Verify DynamoDB Tables

1. Search for **DynamoDB** in AWS Console

2. Click on **Tables** in the left menu

3. You should see 3 tables:
   - [ ] brandpoint-ai-dev-personas
   - [ ] brandpoint-ai-dev-query-results
   - [ ] brandpoint-ai-dev-predictions

### 9.4 Verify OpenSearch Domain

1. Search for **OpenSearch** in AWS Console

2. Click on **Amazon OpenSearch Service**

3. You should see a domain: `brandpoint-ai-dev-vectors`

4. Status should be **Active** (green)

### 9.5 Verify Neptune Cluster

1. Search for **Neptune** in AWS Console

2. Click on **Amazon Neptune**

3. Click **Databases** in left menu

4. You should see: `brandpoint-ai-dev-knowledge-graph`

5. Status should be **Available**

```
✅ CHECKPOINT: All resources verified
   - 15+ Lambda functions
   - 3 DynamoDB tables
   - 1 OpenSearch domain (Active)
   - 1 Neptune cluster (Available)
   - API Gateway endpoint noted
```

---

## STEP 10: TEST THE SYSTEM

Run basic tests to confirm the system works.

### 10.1 Test Health Check Endpoint

In your terminal, run (replace YOUR_API_ENDPOINT):

```bash
curl https://YOUR_API_ENDPOINT/dev/health
```

Expected response:
```json
{"status": "healthy", "environment": "dev"}
```

### 10.2 Test from AWS Console

1. Go to **API Gateway** in AWS Console

2. Click on **brandpoint-ai-dev-api**

3. In the left menu, click **Stages**

4. Click **dev**

5. Click on **GET** under **/health**

6. Click **Test** (lightning bolt icon)

7. Click **Test** button

8. You should see:
   - Status: 200
   - Response body: `{"status": "healthy", ...}`

### 10.3 Create a Test Persona

1. Go to **DynamoDB** in AWS Console

2. Click on table: `brandpoint-ai-dev-personas`

3. Click **Explore table items**

4. Click **Create item**

5. Click **JSON view** toggle

6. Paste this test persona:
   ```json
   {
     "personaId": {"S": "test-persona-001"},
     "name": {"S": "Test Persona"},
     "brandId": {"S": "us-army"},
     "clientId": {"S": "test-client"},
     "description": {"S": "A test persona for deployment verification"},
     "demographics": {"M": {
       "ageRange": {"S": "18-24"},
       "gender": {"S": "male"}
     }},
     "interests": {"L": [
       {"S": "military"},
       {"S": "career"}
     ]},
     "preferredEngines": {"L": [
       {"S": "chatgpt"},
       {"S": "perplexity"}
     ]},
     "isActive": {"BOOL": true},
     "createdAt": {"S": "2026-01-01T00:00:00Z"},
     "updatedAt": {"S": "2026-01-01T00:00:00Z"}
   }
   ```

7. Click **Create item**

### 10.4 Test Load Persona Lambda

1. Go to **Lambda** in AWS Console

2. Click on: `brandpoint-ai-dev-load-persona`

3. Click **Test** tab

4. Create a new test event:
   - Event name: `TestLoadPersona`
   - Event JSON:
     ```json
     {
       "personaId": "test-persona-001"
     }
     ```

5. Click **Save**

6. Click **Test**

7. You should see:
   - Status: **Succeeded**
   - Response showing the persona data

```
✅ CHECKPOINT: All tests passed
   - Health check returns 200 with "healthy" status
   - Test persona created in DynamoDB
   - Load persona Lambda successfully retrieves the persona
```

---

## STEP 11: GRANT CONSULTANT ACCESS

After deployment is complete, you need to grant the Codename37 consultant access to the AWS environment for ongoing development and support.

### 11.1 Information to Collect First

Before creating access, collect the following from the consultant:

```
Consultant Name: Jake Trippel
Consultant Email: jake@codename37.com
Company: Codename37
```

### 11.2 Create an IAM User for the Consultant

1. In AWS Console, search for **IAM** and click on it

2. In the left menu, click **Users**

3. Click the **Create user** button (top right)

4. **Step 1 - User details**:
   - **User name**: `codename37-consultant`
   - ✅ Check **Provide user access to the AWS Management Console**
   - Select **I want to create an IAM user**
   - **Console password**: Select **Autogenerated password**
   - ✅ Check **Users must create a new password at next sign-in**
   - Click **Next**

5. **Step 2 - Set permissions**:
   - Select **Attach policies directly**
   - In the search box, search for and check these policies:
     - ✅ `PowerUserAccess` (provides full access except IAM user management)
   - Click **Next**

6. **Step 3 - Review and create**:
   - Review the settings
   - Click **Create user**

7. **IMPORTANT - Save credentials**:
   - You will see a success page with:
     - Console sign-in URL
     - User name
     - Console password
   - Click **Download .csv file** to save these credentials
   - **This is the ONLY time you can see this password**

### 11.3 Create Access Keys for CLI/API Access

The consultant will need programmatic access for development work.

1. Click on the user you just created: `codename37-consultant`

2. Click the **Security credentials** tab

3. Scroll down to **Access keys** section

4. Click **Create access key**

5. **Step 1 - Use case**:
   - Select **Command Line Interface (CLI)**
   - ✅ Check the confirmation box at the bottom
   - Click **Next**

6. **Step 2 - Description**:
   - Description tag: `Codename37 consultant development access`
   - Click **Create access key**

7. **Step 3 - Retrieve access keys**:
   - You will see:
     - **Access key ID**: (starts with AKIA...)
     - **Secret access key**: (click "Show" to reveal)
   - Click **Download .csv file**
   - **This is the ONLY time you can see the secret key**

### 11.4 Send Credentials to Consultant

Send the following information to the consultant via a **secure method** (encrypted email, password manager sharing, or secure file transfer):

```
=== AWS CONSOLE ACCESS ===
Console URL: https://YOUR-ACCOUNT-ID.signin.aws.amazon.com/console
Account ID: [Your 12-digit AWS account ID]
Username: codename37-consultant
Temporary Password: [From downloaded CSV file]
Region: us-east-1 (N. Virginia)

=== PROGRAMMATIC ACCESS (CLI/API) ===
Access Key ID: [From downloaded CSV file]
Secret Access Key: [From downloaded CSV file]
Region: us-east-1

=== RESOURCE INFORMATION ===
API Gateway Endpoint: [From CloudFormation outputs]
OpenSearch Endpoint: [From CloudFormation outputs]
Neptune Endpoint: [From CloudFormation outputs]
Environment: dev
```

### 11.5 Alternative: Use IAM Identity Center (Recommended for Production)

For more secure, federated access management, consider setting up IAM Identity Center (formerly AWS SSO):

1. Search for **IAM Identity Center** in AWS Console

2. Click **Enable** if not already enabled

3. Add the consultant as a user with their email

4. Create a Permission Set with appropriate access

5. Assign the user to the AWS account

This method is more secure because:
- No long-lived access keys
- Temporary credentials that auto-rotate
- Easier to revoke access
- Audit trail of all access

### 11.6 Security Best Practices

> ⚠️ **IMPORTANT SECURITY NOTES**

1. **Never send credentials via unencrypted email or Slack**
   - Use a password manager like 1Password, LastPass, or Bitwarden to share
   - Or use encrypted email

2. **Enable MFA (Multi-Factor Authentication)**:
   - Ask the consultant to set up MFA on their account
   - In IAM → Users → codename37-consultant → Security credentials
   - Under MFA, click **Assign MFA device**

3. **Set credential rotation reminders**:
   - Access keys should be rotated every 90 days
   - Set a calendar reminder

4. **Review access periodically**:
   - Check CloudTrail logs monthly
   - Remove access immediately when project ends

### 11.7 Verify Consultant Access

After the consultant receives credentials, have them verify access:

1. **Console Access Test**:
   - Log into AWS Console with provided credentials
   - Change password on first login
   - Navigate to CloudFormation → verify they can see the stack
   - Navigate to Lambda → verify they can see functions

2. **CLI Access Test** (consultant runs these commands):
   ```bash
   # Configure CLI
   aws configure
   # Enter Access Key ID, Secret Access Key, region (us-east-1), output (json)

   # Verify identity
   aws sts get-caller-identity

   # Verify Lambda access
   aws lambda list-functions --region us-east-1

   # Verify CloudFormation access
   aws cloudformation describe-stacks --stack-name brandpoint-ai-dev --region us-east-1
   ```

3. **Expected Output**: Commands should return successfully without "Access Denied" errors

```
✅ CHECKPOINT: Consultant access configured
   - IAM user created: codename37-consultant
   - Console access credentials sent securely
   - Programmatic access keys created and sent
   - Consultant verified they can access the environment
```

---

## STEP 12: NETWORK CONFIGURATION FOR RDS ACCESS

The AI Platform needs to connect to the existing Brandpoint ARA3 SQL Server database. This requires VPC Peering between the new AI Platform VPC and your existing VPC where RDS is hosted.

### 12.1 Network Configuration Worksheet

**Fill out this worksheet before proceeding:**

```
================================================================================
BRANDPOINT NETWORK CONFIGURATION WORKSHEET
================================================================================

EXISTING BRANDPOINT INFRASTRUCTURE
----------------------------------
1. Existing VPC ID:           vpc-________________________
2. Existing VPC CIDR:         _____._____._____._____/_____ (e.g., 10.0.0.0/16)
3. AWS Region:                us-east-1 (confirm this matches)

RDS DATABASE INFORMATION
------------------------
4. RDS Instance Identifier:   _________________________________
5. RDS Endpoint:              _________________________________.rds.amazonaws.com
6. RDS Port:                  1433 (SQL Server default)
7. RDS Security Group ID:     sg-________________________
8. Database Name:             ARA3

NEW AI PLATFORM (from CloudFormation Outputs)
---------------------------------------------
9. AI Platform VPC ID:        vpc-________________________
10. AI Platform VPC CIDR:     10.100.0.0/16 (default, confirm in CloudFormation)
11. AI Platform Route Table:  rtb-________________________
    (Get from CloudFormation Outputs → PrivateRouteTableId)

READ-ONLY DATABASE USER (Create this user in SQL Server)
--------------------------------------------------------
12. Username:                 brandpoint_ai_readonly
13. Password:                 ________________________ (generate secure password)
    Permissions needed:       db_datareader role on ARA3 database

================================================================================
```

### 12.2 Verify No CIDR Overlap

**CRITICAL**: The two VPC CIDR ranges must NOT overlap.

| VPC | CIDR | Status |
|-----|------|--------|
| Existing Brandpoint VPC | ___.___.___.___ / ___ | |
| New AI Platform VPC | 10.100.0.0/16 | Default |

**Check for overlap:**
- If existing VPC uses `10.0.0.0/16` → ✅ No overlap with `10.100.0.0/16`
- If existing VPC uses `10.100.0.0/16` → ❌ CONFLICT! Contact consultant before proceeding

If there's a conflict, the AI Platform VPC CIDR must be changed before deployment. Contact the Codename37 consultant.

---

## STEP 13: SET UP VPC PEERING

VPC Peering allows the AI Platform Lambda functions to communicate with the RDS database in your existing VPC.

### 13.1 Create VPC Peering Connection

1. Go to **VPC** in AWS Console (search for "VPC")

2. In the left menu, click **Peering connections**

3. Click **Create peering connection**

4. Fill in the details:

   | Field | Value |
   |-------|-------|
   | Name | `brandpoint-ai-to-existing-vpc` |
   | VPC ID (Requester) | Select the AI Platform VPC (from worksheet #9) |
   | Account | My account |
   | Region | This Region (us-east-1) |
   | VPC ID (Accepter) | Select your existing Brandpoint VPC (from worksheet #1) |

5. Click **Create peering connection**

6. You'll see the peering connection with status **Pending Acceptance**

### 13.2 Accept the Peering Connection

1. Select the peering connection you just created

2. Click **Actions** → **Accept request**

3. Click **Accept request** to confirm

4. Status should change to **Active**

```
✅ CHECKPOINT: Peering connection status is "Active"
```

### 13.3 Update Route Tables

You need to add routes in both VPCs so they can communicate.

#### Update AI Platform Route Table (New VPC)

1. In VPC console, click **Route tables** in left menu

2. Find the route table for the AI Platform private subnets:
   - Look for name containing `brandpoint-ai-dev-private-rt`
   - Or use the Route Table ID from worksheet #11

3. Select it and click the **Routes** tab

4. Click **Edit routes** → **Add route**

5. Add this route:

   | Destination | Target |
   |-------------|--------|
   | [Existing VPC CIDR from worksheet #2] | Select the peering connection (pcx-...) |

   Example: If existing VPC is `10.0.0.0/16`:
   | Destination | Target |
   |-------------|--------|
   | 10.0.0.0/16 | pcx-xxxxxxxxxx |

6. Click **Save changes**

#### Update Existing VPC Route Table

1. Find the route table associated with your existing VPC's private subnets
   - This is where your RDS instance is located

2. Select it and click **Edit routes** → **Add route**

3. Add this route:

   | Destination | Target |
   |-------------|--------|
   | 10.100.0.0/16 | Select the peering connection (pcx-...) |

4. Click **Save changes**

```
✅ CHECKPOINT: Routes added to both route tables
```

### 13.4 Update RDS Security Group

Allow the AI Platform Lambda functions to connect to RDS.

1. Go to **EC2** in AWS Console (search for "EC2")

2. In left menu, click **Security Groups**

3. Find the security group attached to your RDS instance (from worksheet #7)

4. Select it and click **Inbound rules** tab

5. Click **Edit inbound rules** → **Add rule**

6. Add this rule:

   | Type | Port | Source | Description |
   |------|------|--------|-------------|
   | MSSQL | 1433 | 10.100.0.0/16 | Brandpoint AI Platform Lambda access |

7. Click **Save rules**

```
✅ CHECKPOINT: RDS security group allows inbound from 10.100.0.0/16 on port 1433
```

### 13.5 Create Read-Only Database User

Connect to your SQL Server RDS instance and create a read-only user for the AI Platform.

**Using SQL Server Management Studio (SSMS):**

```sql
-- Connect to the ARA3 database as admin

-- Create login
CREATE LOGIN brandpoint_ai_readonly WITH PASSWORD = 'YourSecurePassword123!';

-- Create user in ARA3 database
USE ARA3;
CREATE USER brandpoint_ai_readonly FOR LOGIN brandpoint_ai_readonly;

-- Grant read-only access
ALTER ROLE db_datareader ADD MEMBER brandpoint_ai_readonly;

-- Verify permissions
SELECT dp.name, dp.type_desc, p.permission_name
FROM sys.database_principals dp
LEFT JOIN sys.database_permissions p ON dp.principal_id = p.grantee_principal_id
WHERE dp.name = 'brandpoint_ai_readonly';
```

### 13.6 Update Secrets Manager with RDS Credentials

1. Go to **Secrets Manager** in AWS Console

2. Find and click on: `brandpoint-ai-dev-ara3-database-readonly`

3. Click **Retrieve secret value** → **Edit**

4. Update with actual values:

```json
{
  "host": "your-rds-endpoint.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com",
  "port": "1433",
  "database": "ARA3",
  "username": "brandpoint_ai_readonly",
  "password": "YourSecurePassword123!",
  "driver": "ODBC Driver 17 for SQL Server"
}
```

5. Click **Save**

### 13.7 Test Database Connectivity

Test that Lambda can connect to RDS through the VPC peering.

1. Go to **Lambda** in AWS Console

2. Click on `brandpoint-ai-dev-feature-extraction` function

3. Click **Test** tab

4. Create a test event:
   ```json
   {
     "test": "connectivity"
   }
   ```

5. Click **Test**

6. Check CloudWatch Logs for any connection errors

**Expected behavior**: The function should execute without "connection timeout" or "network unreachable" errors. It may fail for other reasons (missing data, etc.) but network connectivity should work.

```
✅ CHECKPOINT: VPC Peering Complete
   - Peering connection active
   - Route tables updated in both VPCs
   - RDS security group allows Lambda access
   - Read-only database user created
   - Secrets Manager updated with credentials
   - Lambda can reach RDS (no network timeout errors)
```

---

## PRODUCTION HARDENING NOTES

> **Important:** This POC deployment is optimized for development and testing. Before deploying to production, review these hardening recommendations.

### Logging Configuration

The POC uses verbose logging for debugging. For production:

1. **API Gateway**: In `05-api.yaml`, set `DataTraceEnabled: false` to prevent logging request/response bodies
2. **Step Functions**: In `04-orchestration.yaml`, set `IncludeExecutionData: false` and `Level: ERROR` to reduce log volume and prevent sensitive data in logs

### IAM Permissions

The POC uses broader IAM permissions for simplicity. For production:

1. Scope Secrets Manager access to exact secret ARNs instead of wildcards
2. Scope OpenSearch access to the specific domain ARN
3. Scope Neptune permissions to specific actions used by the application

### Lambda Packaging

For production deployments with compiled dependencies:

1. Use **AWS SAM** (`sam build`) for consistent Lambda packaging
2. Or use Docker with Amazon Linux 2 base image to ensure binary compatibility
3. This ensures compiled Python packages (if any) match the Lambda runtime

### Secrets Management

For production:

1. Avoid storing placeholder values in CloudFormation templates
2. Use `GenerateSecretString` for database passwords
3. Configure secrets out-of-band using `aws secretsmanager put-secret-value`

---

## TROUBLESHOOTING GUIDE

### Problem: CloudFormation Stack Failed

**Symptoms**: Stack shows `CREATE_FAILED` or `ROLLBACK_COMPLETE`

**Steps to Fix**:

1. In CloudFormation, click on the failed stack

2. Click **Events** tab

3. Look for events with status `CREATE_FAILED` (red text)

4. The "Status reason" column tells you what went wrong

**Common Errors and Solutions**:

| Error Message | Cause | Solution |
|--------------|-------|----------|
| "S3 bucket does not exist" | Wrong bucket name | Check bucket names match exactly |
| "Template format error" | YAML syntax issue | Check template files for typos |
| "Resource limit exceeded" | Account limits | Contact AWS support to increase limits |
| "Access Denied" | Permission issue | Verify IAM user has AdministratorAccess |
| "Invalid parameter" | Wrong parameter value | Check parameter values match expected formats |

### Problem: Lambda Function Errors

**Symptoms**: Lambda returns errors when tested

**Steps to Fix**:

1. Go to Lambda function in console

2. Click **Monitor** tab

3. Click **View CloudWatch logs**

4. Look at the most recent log stream

5. Search for error messages

**Common Lambda Errors**:

| Error | Cause | Solution |
|-------|-------|----------|
| "ModuleNotFoundError" | Missing dependency | Re-run package-lambdas.sh and re-upload |
| "AccessDenied" | IAM permission missing | Check Lambda role permissions |
| "Task timed out" | Function too slow | Increase timeout in Lambda config |
| "Secret not found" | Wrong secret name | Verify secret exists in Secrets Manager |

### Problem: API Gateway Returns 403

**Symptoms**: API calls return "Forbidden"

**Steps to Fix**:

1. Check if API key is required

2. Go to API Gateway → API Keys

3. Copy the API key value

4. Add header to your request: `x-api-key: YOUR_API_KEY`

### Problem: OpenSearch Domain Not Active

**Symptoms**: Domain stuck in "Processing" state

**Solution**: Wait longer. OpenSearch can take up to 30 minutes to provision. If still processing after 45 minutes, check CloudWatch logs for the OpenSearch service.

### Problem: Neptune Connection Timeout

**Symptoms**: Lambda can't connect to Neptune

**Solution**:
1. Verify Lambda is in the VPC
2. Check security group allows port 8182
3. Verify Neptune status is "Available"

### Problem: "Template is too large"

**Symptoms**: CloudFormation says template exceeds size limit

**Solution**: Make sure you're using the S3 URL method, not uploading the file directly.

### Problem: VPC Peering Connection Failed

**Symptoms**: Peering connection shows "Failed" or stays in "Pending"

**Steps to Fix**:

1. Verify both VPCs are in the same region (us-east-1)
2. Check that CIDR ranges don't overlap:
   - AI Platform: 10.100.0.0/16
   - Existing VPC: Should NOT be 10.100.x.x
3. Ensure you have permissions to create peering connections
4. Try deleting and recreating the peering connection

### Problem: Lambda Cannot Connect to RDS (Timeout)

**Symptoms**: Lambda times out when trying to connect to SQL Server RDS

**Steps to Fix**:

1. **Verify VPC Peering is Active**:
   - Go to VPC → Peering connections
   - Status should be "Active"

2. **Check Route Tables**:
   - AI Platform private route table should have route to existing VPC CIDR via peering connection
   - Existing VPC route table should have route to 10.100.0.0/16 via peering connection

3. **Check RDS Security Group**:
   - Must allow inbound on port 1433 from 10.100.0.0/16

4. **Verify Lambda is in VPC**:
   - Go to Lambda function → Configuration → VPC
   - Should show the AI Platform VPC and private subnets

5. **Check Lambda Security Group**:
   - Must allow outbound on port 1433

### Problem: RDS Connection Refused (Not Timeout)

**Symptoms**: Connection refused immediately (not timeout)

**Steps to Fix**:

1. Verify RDS endpoint is correct in Secrets Manager
2. Verify port is 1433
3. Verify database name is "ARA3"
4. Verify username and password are correct
5. Test connection from an EC2 instance in the same VPC as RDS first

### Problem: CIDR Overlap Error

**Symptoms**: VPC peering fails with "CIDR overlap" error

**Solution**:
1. Check your existing VPC CIDR (VPC → Your VPCs → CIDR column)
2. If it conflicts with 10.100.0.0/16, contact the Codename37 consultant
3. The AI Platform VPC CIDR will need to be changed before deployment

---

## ROLLBACK INSTRUCTIONS

If you need to completely remove the deployment:

### Option A: Automated Rollback Script (Recommended)

Use the rollback script which handles everything automatically:

```bash
./scripts/rollback.sh dev us-east-1
```

The script will:
1. Disable EventBridge rules (stop new executions)
2. Stop any running Step Function executions
3. Empty S3 buckets (required before stack deletion)
4. Delete the CloudFormation stack
5. Clean up deployment buckets

**WARNING**: This deletes all data. Type `ROLLBACK` when prompted to confirm.

### Option B: Manual Rollback via AWS Console

If the script fails or you prefer manual deletion:

#### Delete the CloudFormation Stack

1. Go to **CloudFormation** in AWS Console

2. Select the stack: `brandpoint-ai-dev`

3. Click **Delete**

4. Confirm by clicking **Delete stack**

5. Wait for deletion to complete (15-30 minutes)

#### Delete S3 Buckets (if needed)

**Note**: You must empty buckets before deleting them.

1. Go to **S3** in AWS Console

2. Click on the bucket name

3. Select all objects (checkbox at top)

4. Click **Delete**

5. Type `permanently delete` to confirm

6. Once empty, go back to bucket list

7. Select the bucket and click **Delete**

8. Type the bucket name to confirm

---

## SUPPORT CONTACTS

### For Deployment & Technical Issues (Primary)
- **Company**: Codename37
- **Consultant**: Jake Trippel
- **Email**: jake@codename37.com
- **Role**: Lead developer and architect for this solution

### For Brandpoint Internal Support
- **Slack**: #brandpoint-ai-support
- **Internal IT**: [Your IT team contact]

### For AWS Account Issues
- **AWS Support**: Sign in to AWS Console → Support → Create case
- **AWS Account Team**: [Your AWS account manager if you have one]

### For API Key Issues
- **OpenAI**: https://platform.openai.com/account/api-keys
- **Perplexity**: https://www.perplexity.ai/settings/api
- **Google AI**: https://makersuite.google.com/app/apikey
- **Anthropic (Claude)**: https://console.anthropic.com/settings/keys

---

## APPENDIX A: QUICK REFERENCE COMMANDS

```bash
# Check AWS credentials
aws sts get-caller-identity

# List S3 buckets
aws s3 ls

# Upload file to S3
aws s3 cp localfile.zip s3://bucket-name/path/

# Sync directory to S3
aws s3 sync ./local-dir s3://bucket-name/remote-dir/

# Describe CloudFormation stack
aws cloudformation describe-stacks --stack-name brandpoint-ai-dev

# List Lambda functions
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'brandpoint-ai-dev')]"

# Invoke Lambda function
aws lambda invoke --function-name brandpoint-ai-dev-health-check output.json

# Check stack events
aws cloudformation describe-stack-events --stack-name brandpoint-ai-dev
```

---

## APPENDIX B: ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BRANDPOINT AI PLATFORM                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────────────────────────────────┐    │
│  │  API Gateway │───▶│  Lambda Functions (15 functions)        │    │
│  │  (REST API)  │    │  - Persona management                   │    │
│  └─────────────┘    │  - Query execution (4 AI engines)       │    │
│                      │  - Visibility analysis                   │    │
│                      │  - Intelligence engine                   │    │
│                      └─────────────────────────────────────────┘    │
│                                     │                                │
│          ┌──────────────────────────┼──────────────────────────┐    │
│          │                          │                          │    │
│          ▼                          ▼                          ▼    │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐ │
│  │  DynamoDB   │          │  OpenSearch │          │   Neptune   │ │
│  │  (Personas, │          │  (Vectors,  │          │  (Knowledge │ │
│  │   Results)  │          │   k-NN)     │          │    Graph)   │ │
│  └─────────────┘          └─────────────┘          └─────────────┘ │
│                                                                      │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐ │
│  │  SageMaker  │          │   Bedrock   │          │    S3       │ │
│  │ (ML Models) │          │  (Claude,   │          │  (Storage)  │ │
│  │             │          │   Titan)    │          │             │ │
│  └─────────────┘          └─────────────┘          └─────────────┘ │
│                                                                      │
│  ┌─────────────┐          ┌─────────────┐                          │
│  │    Step     │          │ EventBridge │                          │
│  │  Functions  │◀─────────│ (Schedules) │                          │
│  │ (Workflows) │          │             │                          │
│  └─────────────┘          └─────────────┘                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

**END OF DEPLOYMENT GUIDE**

Document maintained by: Codename37 Development Team
