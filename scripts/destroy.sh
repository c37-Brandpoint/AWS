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
CYAN='\033[0;36m'
NC='\033[0m'

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
MODEL_ARTIFACTS_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-model-artifacts-${ACCOUNT_ID}"

# Function to empty versioned bucket
empty_versioned_bucket() {
    local bucket=$1
    echo "  Emptying $bucket (including versions)..."

    # Check if bucket exists
    if ! aws s3api head-bucket --bucket "$bucket" --region "$REGION" $AWS_ARGS 2>/dev/null; then
        echo "    (bucket does not exist, skipping)"
        return 0
    fi

    # Delete all objects
    aws s3 rm "s3://${bucket}" --recursive --region "$REGION" $AWS_ARGS 2>/dev/null || true

    # Delete all versions (for versioned buckets)
    echo "    Deleting object versions..."
    aws s3api list-object-versions --bucket "$bucket" --region "$REGION" $AWS_ARGS \
        --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' \
        --output json 2>/dev/null | \
    aws s3api delete-objects --bucket "$bucket" --delete file:///dev/stdin \
        --region "$REGION" $AWS_ARGS 2>/dev/null || true

    # Delete all delete markers
    echo "    Deleting delete markers..."
    aws s3api list-object-versions --bucket "$bucket" --region "$REGION" $AWS_ARGS \
        --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' \
        --output json 2>/dev/null | \
    aws s3api delete-objects --bucket "$bucket" --delete file:///dev/stdin \
        --region "$REGION" $AWS_ARGS 2>/dev/null || true

    echo "    Done"
}

# Function to print error help
print_deletion_help() {
    local error_type=$1
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  STACK DELETION FAILED${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}WHAT TO CHECK:${NC}"
    echo ""
    echo "1. Check the CloudFormation Console for the specific error:"
    echo "   https://console.aws.amazon.com/cloudformation/home?region=${REGION}#/stacks"
    echo ""
    echo "2. View deletion events:"
    echo "   aws cloudformation describe-stack-events --stack-name $STACK_NAME --region $REGION $AWS_ARGS | head -50"
    echo ""
    echo -e "${YELLOW}COMMON ISSUES AND FIXES:${NC}"
    echo ""
    echo "A) S3 Bucket Not Empty:"
    echo "   aws s3 rm s3://BUCKET_NAME --recursive --region $REGION $AWS_ARGS"
    echo ""
    echo "B) ENI Still Attached (Lambda in VPC):"
    echo "   - Wait 10-15 minutes for Lambda ENIs to auto-detach"
    echo "   - Or manually detach in EC2 Console > Network Interfaces"
    echo ""
    echo "C) Security Group In Use:"
    echo "   - Check what's using it:"
    echo "     aws ec2 describe-network-interfaces --filters Name=group-id,Values=SG_ID --region $REGION $AWS_ARGS"
    echo ""
    echo "D) NAT Gateway Stuck:"
    echo "   aws ec2 describe-nat-gateways --filter Name=state,Values=deleting --region $REGION $AWS_ARGS"
    echo "   - If stuck, wait or contact AWS Support"
    echo ""
    echo "E) Resource Still In Use by Another Stack:"
    echo "   - Check for dependent stacks:"
    echo "     aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --region $REGION $AWS_ARGS"
    echo ""
    echo -e "${CYAN}FORCE DELETE (if stuck):${NC}"
    echo "   aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION $AWS_ARGS"
    echo "   aws cloudformation delete-stack --stack-name $STACK_NAME --retain-resources RESOURCE_ID --region $REGION $AWS_ARGS"
    echo ""
}

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

# Check if stack exists
echo ""
echo -n "Checking if stack exists... "
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
    --region "$REGION" $AWS_ARGS \
    --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$STACK_STATUS" = "NOT_FOUND" ]; then
    echo -e "${YELLOW}Stack not found${NC}"
    echo "Proceeding to clean up any orphaned resources..."
else
    echo -e "${GREEN}Found ($STACK_STATUS)${NC}"
fi

# Step 1: Empty S3 buckets
echo ""
echo -e "${YELLOW}[1/5] Emptying S3 buckets...${NC}"

# Get all bucket names from the stack (if it exists)
if [ "$STACK_STATUS" != "NOT_FOUND" ]; then
    BUCKETS=$(aws cloudformation list-stack-resources \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query "StackResourceSummaries[?ResourceType=='AWS::S3::Bucket'].PhysicalResourceId" \
        --output text \
        $AWS_ARGS 2>/dev/null || echo "")

    for bucket in $BUCKETS; do
        empty_versioned_bucket "$bucket"
    done
fi

# Also empty deployment buckets
empty_versioned_bucket "$TEMPLATES_BUCKET"
empty_versioned_bucket "$LAMBDA_CODE_BUCKET"
empty_versioned_bucket "$MODEL_ARTIFACTS_BUCKET"

echo -e "${GREEN}✓ Buckets emptied${NC}"

# Step 2: Disable EventBridge rules (prevent new executions during deletion)
echo ""
echo -e "${YELLOW}[2/5] Disabling EventBridge rules...${NC}"

aws events disable-rule \
    --name "${PROJECT_NAME}-${ENVIRONMENT}-persona-agent-schedule" \
    --region "$REGION" $AWS_ARGS 2>/dev/null || echo "  (rule not found, skipping)"

aws events disable-rule \
    --name "${PROJECT_NAME}-${ENVIRONMENT}-content-published" \
    --region "$REGION" $AWS_ARGS 2>/dev/null || echo "  (rule not found, skipping)"

echo -e "${GREEN}✓ Rules disabled${NC}"

# Step 3: Delete CloudFormation stack
echo ""
echo -e "${YELLOW}[3/5] Deleting CloudFormation stack...${NC}"

if [ "$STACK_STATUS" != "NOT_FOUND" ]; then
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        $AWS_ARGS

    echo "  Waiting for stack deletion (this may take 15-30 minutes)..."
    echo "  Monitor progress: https://console.aws.amazon.com/cloudformation/home?region=${REGION}#/stacks"
    echo ""

    # Wait with timeout handling
    if ! aws cloudformation wait stack-delete-complete \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        $AWS_ARGS 2>/dev/null; then

        # Check what state the stack is in
        FINAL_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
            --region "$REGION" $AWS_ARGS \
            --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo "DELETED")

        if [ "$FINAL_STATUS" = "DELETE_FAILED" ]; then
            print_deletion_help "DELETE_FAILED"
            exit 1
        fi
    fi

    echo -e "${GREEN}✓ Stack deleted${NC}"
else
    echo "  Stack does not exist, skipping"
fi

# Step 4: Delete deployment buckets
echo ""
echo -e "${YELLOW}[4/5] Deleting deployment buckets...${NC}"

for bucket in "$TEMPLATES_BUCKET" "$LAMBDA_CODE_BUCKET" "$MODEL_ARTIFACTS_BUCKET"; do
    echo -n "  Deleting $bucket... "
    if aws s3 rb "s3://${bucket}" --region "$REGION" $AWS_ARGS 2>/dev/null; then
        echo -e "${GREEN}done${NC}"
    else
        echo -e "${YELLOW}skipped (may not exist)${NC}"
    fi
done

echo -e "${GREEN}✓ Deployment buckets deleted${NC}"

# Step 5: Clean up CloudWatch log groups
echo ""
echo -e "${YELLOW}[5/5] Cleaning up log groups...${NC}"

LOG_GROUPS=$(aws logs describe-log-groups \
    --log-group-name-prefix "/aws/lambda/${PROJECT_NAME}-${ENVIRONMENT}" \
    --region "$REGION" \
    --query "logGroups[*].logGroupName" \
    --output text \
    $AWS_ARGS 2>/dev/null || echo "")

if [ -n "$LOG_GROUPS" ] && [ "$LOG_GROUPS" != "None" ]; then
    for log_group in $LOG_GROUPS; do
        echo -n "  Deleting $log_group... "
        if aws logs delete-log-group --log-group-name "$log_group" --region "$REGION" $AWS_ARGS 2>/dev/null; then
            echo -e "${GREEN}done${NC}"
        else
            echo -e "${YELLOW}failed (may require manual deletion)${NC}"
        fi
    done
else
    echo "  No log groups found"
fi

# Also check for Step Functions log groups
SF_LOG_GROUPS=$(aws logs describe-log-groups \
    --log-group-name-prefix "/aws/vendedlogs/states/${PROJECT_NAME}-${ENVIRONMENT}" \
    --region "$REGION" \
    --query "logGroups[*].logGroupName" \
    --output text \
    $AWS_ARGS 2>/dev/null || echo "")

if [ -n "$SF_LOG_GROUPS" ] && [ "$SF_LOG_GROUPS" != "None" ]; then
    for log_group in $SF_LOG_GROUPS; do
        echo -n "  Deleting $log_group... "
        if aws logs delete-log-group --log-group-name "$log_group" --region "$REGION" $AWS_ARGS 2>/dev/null; then
            echo -e "${GREEN}done${NC}"
        else
            echo -e "${YELLOW}failed${NC}"
        fi
    done
fi

echo -e "${GREEN}✓ Log groups cleaned up${NC}"

# Check for orphaned resources
echo ""
echo "Checking for orphaned resources..."

# Check for orphaned Elastic IPs
ORPHAN_EIPS=$(aws ec2 describe-addresses \
    --query "Addresses[?AssociationId==null].AllocationId" \
    --output text \
    --region "$REGION" $AWS_ARGS 2>/dev/null || echo "")

if [ -n "$ORPHAN_EIPS" ] && [ "$ORPHAN_EIPS" != "None" ]; then
    EIP_COUNT=$(echo "$ORPHAN_EIPS" | wc -w)
    echo -e "${YELLOW}NOTE: Found $EIP_COUNT unattached Elastic IP(s) in account${NC}"
    echo "  These may incur charges. To release:"
    echo "  aws ec2 release-address --allocation-id <ID> --region $REGION $AWS_ARGS"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Teardown Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "All ${ENVIRONMENT} resources have been deleted."
echo ""
echo "To redeploy, run:"
echo "  ./scripts/brandpoint-deploy.sh --env $ENVIRONMENT --region $REGION"
echo ""
