#!/bin/bash
#
# Brandpoint AI Platform - Teardown Script
#
# WARNING: This will delete all resources and data!
#
# Usage:
#   ./destroy.sh --environment dev --region us-east-1
#   ./destroy.sh --environment dev --region us-east-1 --confirm
#

set -e

# Default values
ENVIRONMENT="dev"
REGION="us-east-1"
PROJECT_NAME="brandpoint-ai"
PROFILE=""
CONFIRM=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        --confirm)
            CONFIRM=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -e, --environment    Environment (dev, staging, prod) [default: dev]"
            echo "  -r, --region         AWS region [default: us-east-1]"
            echo "  -p, --profile        AWS CLI profile to use"
            echo "  --confirm            Skip confirmation prompt"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set AWS profile if provided
if [ -n "$PROFILE" ]; then
    export AWS_PROFILE="$PROFILE"
    AWS_ARGS="--profile $PROFILE"
else
    AWS_ARGS=""
fi

# Derived values
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text $AWS_ARGS)
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
TEMPLATES_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-templates-${ACCOUNT_ID}"
LAMBDA_CODE_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-lambda-code-${ACCOUNT_ID}"

echo -e "${RED}========================================${NC}"
echo -e "${RED}Brandpoint AI Platform DESTRUCTION${NC}"
echo -e "${RED}========================================${NC}"
echo ""
echo -e "Environment:     ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "Region:          ${YELLOW}${REGION}${NC}"
echo -e "Account ID:      ${YELLOW}${ACCOUNT_ID}${NC}"
echo -e "Stack Name:      ${YELLOW}${STACK_NAME}${NC}"
echo ""
echo -e "${RED}WARNING: This will DELETE all resources and data!${NC}"
echo ""

if [ "$CONFIRM" = false ]; then
    read -p "Are you sure you want to proceed? Type 'DELETE' to confirm: " confirmation
    if [ "$confirmation" != "DELETE" ]; then
        echo "Aborted."
        exit 1
    fi
fi

# Step 1: Empty S3 buckets
echo -e "${YELLOW}[1/4] Emptying S3 buckets...${NC}"

# Get all bucket names from the stack
BUCKETS=$(aws cloudformation list-stack-resources \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query "StackResourceSummaries[?ResourceType=='AWS::S3::Bucket'].PhysicalResourceId" \
    --output text \
    $AWS_ARGS 2>/dev/null || echo "")

for bucket in $BUCKETS; do
    echo "  Emptying $bucket..."
    aws s3 rm s3://${bucket} --recursive --region ${REGION} $AWS_ARGS 2>/dev/null || true
done

# Also empty deployment buckets
echo "  Emptying deployment buckets..."
aws s3 rm s3://${TEMPLATES_BUCKET} --recursive --region ${REGION} $AWS_ARGS 2>/dev/null || true
aws s3 rm s3://${LAMBDA_CODE_BUCKET} --recursive --region ${REGION} $AWS_ARGS 2>/dev/null || true

echo -e "${GREEN}✓ Buckets emptied${NC}"

# Step 2: Delete CloudFormation stack
echo -e "${YELLOW}[2/4] Deleting CloudFormation stack...${NC}"

aws cloudformation delete-stack \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    $AWS_ARGS

echo "  Waiting for stack deletion..."
aws cloudformation wait stack-delete-complete \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    $AWS_ARGS

echo -e "${GREEN}✓ Stack deleted${NC}"

# Step 3: Delete deployment buckets
echo -e "${YELLOW}[3/4] Deleting deployment buckets...${NC}"

aws s3 rb s3://${TEMPLATES_BUCKET} --region ${REGION} $AWS_ARGS 2>/dev/null || true
aws s3 rb s3://${LAMBDA_CODE_BUCKET} --region ${REGION} $AWS_ARGS 2>/dev/null || true

echo -e "${GREEN}✓ Deployment buckets deleted${NC}"

# Step 4: Clean up CloudWatch log groups
echo -e "${YELLOW}[4/4] Cleaning up log groups...${NC}"

LOG_GROUPS=$(aws logs describe-log-groups \
    --log-group-name-prefix "/aws/lambda/${PROJECT_NAME}-${ENVIRONMENT}" \
    --region ${REGION} \
    --query "logGroups[*].logGroupName" \
    --output text \
    $AWS_ARGS 2>/dev/null || echo "")

for log_group in $LOG_GROUPS; do
    echo "  Deleting $log_group..."
    aws logs delete-log-group --log-group-name "$log_group" --region ${REGION} $AWS_ARGS 2>/dev/null || true
done

echo -e "${GREEN}✓ Log groups cleaned up${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Teardown Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "All ${ENVIRONMENT} resources have been deleted."
