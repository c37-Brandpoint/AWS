#!/bin/bash
#
# Brandpoint AI Platform - Emergency Rollback
#
# Deletes the CloudFormation stack and associated resources
#
# Usage:
#   ./rollback.sh dev us-east-1
#   ./rollback.sh prod us-east-1 --profile production
#
# WARNING: This will delete all stack resources. Data in DynamoDB tables,
# S3 buckets, Neptune, and OpenSearch will be deleted unless deletion
# protection is enabled.
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENVIRONMENT="${1:-}"
REGION="${2:-us-east-1}"
PROJECT="brandpoint-ai"
PROFILE=""

if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <environment> [region] [--profile <profile>]"
    echo "  environment: dev, staging, prod"
    echo "  region: AWS region (default: us-east-1)"
    exit 1
fi

STACK_NAME="${PROJECT}-${ENVIRONMENT}"

# Parse additional arguments
shift 2 2>/dev/null || true
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [ -n "$PROFILE" ]; then
    export AWS_PROFILE="$PROFILE"
    AWS_ARGS="--profile $PROFILE"
else
    AWS_ARGS=""
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text $AWS_ARGS)

echo "========================================"
echo -e "${RED}ROLLBACK: $STACK_NAME${NC}"
echo "========================================"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo ""
echo -e "${YELLOW}WARNING: This will delete:${NC}"
echo "  - All Lambda functions"
echo "  - API Gateway"
echo "  - Step Functions state machines"
echo "  - OpenSearch domain (and all indexed data)"
echo "  - Neptune cluster (and all graph data)"
echo "  - SageMaker endpoint"
echo "  - DynamoDB tables (and all data)"
echo "  - S3 buckets created by the stack"
echo "  - IAM roles and policies"
echo "  - CloudWatch dashboards and alarms"
echo ""
echo -e "${YELLOW}This action CANNOT be undone.${NC}"
echo ""
read -p "Type 'ROLLBACK' to confirm: " CONFIRM

if [ "$CONFIRM" != "ROLLBACK" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Starting rollback..."
echo ""

# Step 1: Disable EventBridge rules (stop new executions)
echo "Disabling EventBridge rules..."
aws events disable-rule \
    --name "${PROJECT}-${ENVIRONMENT}-persona-agent-schedule" \
    --region $REGION $AWS_ARGS 2>/dev/null || echo "  (rule not found, skipping)"

aws events disable-rule \
    --name "${PROJECT}-${ENVIRONMENT}-content-published" \
    --region $REGION $AWS_ARGS 2>/dev/null || echo "  (rule not found, skipping)"

# Step 2: Stop running Step Function executions
echo "Stopping running Step Function executions..."
SM_ARN="arn:aws:states:${REGION}:${ACCOUNT_ID}:stateMachine:${PROJECT}-${ENVIRONMENT}-persona-agent"
RUNNING=$(aws stepfunctions list-executions \
    --state-machine-arn "$SM_ARN" \
    --status-filter RUNNING \
    --query "executions[].executionArn" \
    --output text \
    --region $REGION $AWS_ARGS 2>/dev/null || echo "")

if [ -n "$RUNNING" ]; then
    for exec in $RUNNING; do
        aws stepfunctions stop-execution \
            --execution-arn "$exec" \
            --cause "Rollback initiated" \
            --region $REGION $AWS_ARGS 2>/dev/null || true
        echo "  Stopped: $exec"
    done
else
    echo "  No running executions found"
fi

# Step 3: Empty S3 buckets (required before stack deletion)
echo "Emptying S3 buckets..."
for bucket_suffix in "templates" "lambda-code" "model-artifacts" "results-archive" "data-lake"; do
    BUCKET_NAME="${PROJECT}-${ENVIRONMENT}-${bucket_suffix}-${ACCOUNT_ID}"
    if aws s3 ls "s3://${BUCKET_NAME}" --region $REGION $AWS_ARGS > /dev/null 2>&1; then
        echo "  Emptying: $BUCKET_NAME"
        aws s3 rm "s3://${BUCKET_NAME}" --recursive --region $REGION $AWS_ARGS 2>/dev/null || true
        # Also delete versions for versioned buckets
        aws s3api list-object-versions \
            --bucket "$BUCKET_NAME" \
            --region $REGION $AWS_ARGS \
            --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' \
            --output json 2>/dev/null | \
        aws s3api delete-objects \
            --bucket "$BUCKET_NAME" \
            --delete file:///dev/stdin \
            --region $REGION $AWS_ARGS 2>/dev/null || true
    fi
done

# Step 4: Delete the CloudFormation stack
echo ""
echo "Deleting CloudFormation stack..."
aws cloudformation delete-stack \
    --stack-name $STACK_NAME \
    --region $REGION $AWS_ARGS

echo "Waiting for stack deletion (this may take 15-30 minutes)..."
aws cloudformation wait stack-delete-complete \
    --stack-name $STACK_NAME \
    --region $REGION $AWS_ARGS

# Step 5: Clean up deployment buckets (not part of stack)
echo ""
echo "Cleaning up deployment buckets..."
for bucket_suffix in "templates" "lambda-code"; do
    BUCKET_NAME="${PROJECT}-${ENVIRONMENT}-${bucket_suffix}-${ACCOUNT_ID}"
    if aws s3 ls "s3://${BUCKET_NAME}" --region $REGION $AWS_ARGS > /dev/null 2>&1; then
        echo "  Deleting: $BUCKET_NAME"
        aws s3 rb "s3://${BUCKET_NAME}" --force --region $REGION $AWS_ARGS 2>/dev/null || true
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Rollback Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Stack $STACK_NAME has been deleted."
echo ""
echo "To redeploy, run:"
echo "  ./scripts/deploy.sh --environment $ENVIRONMENT --region $REGION"
echo ""
