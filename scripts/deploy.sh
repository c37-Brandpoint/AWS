#!/bin/bash
#
# Brandpoint AI Platform - Deployment Script
#
# Usage:
#   ./deploy.sh --environment dev --region us-east-1
#   ./deploy.sh --environment prod --region us-east-1 --profile production
#

set -e

# Default values
ENVIRONMENT="dev"
REGION="us-east-1"
PROJECT_NAME="brandpoint-ai"
PROFILE=""
SKIP_LAMBDA_BUILD=false

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
        --skip-lambda-build)
            SKIP_LAMBDA_BUILD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -e, --environment    Environment (dev, staging, prod) [default: dev]"
            echo "  -r, --region         AWS region [default: us-east-1]"
            echo "  -p, --profile        AWS CLI profile to use"
            echo "  --skip-lambda-build  Skip Lambda package build"
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
TEMPLATES_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-templates-${ACCOUNT_ID}"
LAMBDA_CODE_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-lambda-code-${ACCOUNT_ID}"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Brandpoint AI Platform Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Environment:     ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "Region:          ${YELLOW}${REGION}${NC}"
echo -e "Account ID:      ${YELLOW}${ACCOUNT_ID}${NC}"
echo -e "Stack Name:      ${YELLOW}${STACK_NAME}${NC}"
echo ""

# Step 1: Create S3 buckets for deployment artifacts
echo -e "${GREEN}[1/5] Creating deployment buckets...${NC}"

aws s3 mb s3://${TEMPLATES_BUCKET} --region ${REGION} $AWS_ARGS 2>/dev/null || true
aws s3 mb s3://${LAMBDA_CODE_BUCKET} --region ${REGION} $AWS_ARGS 2>/dev/null || true

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket ${TEMPLATES_BUCKET} \
    --versioning-configuration Status=Enabled \
    --region ${REGION} $AWS_ARGS

aws s3api put-bucket-versioning \
    --bucket ${LAMBDA_CODE_BUCKET} \
    --versioning-configuration Status=Enabled \
    --region ${REGION} $AWS_ARGS

# Block public access (security hardening)
echo "  Applying security settings..."
aws s3api put-public-access-block \
    --bucket ${TEMPLATES_BUCKET} \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
    --region ${REGION} $AWS_ARGS

aws s3api put-public-access-block \
    --bucket ${LAMBDA_CODE_BUCKET} \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
    --region ${REGION} $AWS_ARGS

# Enable server-side encryption
aws s3api put-bucket-encryption \
    --bucket ${TEMPLATES_BUCKET} \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
    --region ${REGION} $AWS_ARGS

aws s3api put-bucket-encryption \
    --bucket ${LAMBDA_CODE_BUCKET} \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
    --region ${REGION} $AWS_ARGS

echo -e "${GREEN}✓ Buckets created and secured${NC}"

# Step 2: Upload CloudFormation templates
echo -e "${GREEN}[2/5] Uploading CloudFormation templates...${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/../infrastructure"

aws s3 sync ${INFRA_DIR}/cloudformation/ s3://${TEMPLATES_BUCKET}/cloudformation/ \
    --region ${REGION} $AWS_ARGS \
    --delete

echo -e "${GREEN}✓ Templates uploaded${NC}"

# Step 3: Build and upload Lambda packages (if not skipped)
if [ "$SKIP_LAMBDA_BUILD" = false ]; then
    echo -e "${GREEN}[3/5] Building Lambda packages...${NC}"

    LAMBDA_DIR="${INFRA_DIR}/lambda"

    if [ -d "$LAMBDA_DIR" ]; then
        for func_dir in ${LAMBDA_DIR}/*/; do
            if [ -d "$func_dir" ]; then
                func_name=$(basename "$func_dir")
                echo "  Building ${func_name}..."

                # Create zip package
                cd "$func_dir"
                if [ -f "requirements.txt" ]; then
                    pip install -r requirements.txt -t ./package --quiet
                    cd package
                    zip -r9 ../${func_name}.zip . --quiet
                    cd ..
                    zip -g ${func_name}.zip *.py --quiet 2>/dev/null || true
                    rm -rf package
                else
                    zip -r9 ${func_name}.zip . --quiet
                fi

                # Upload to S3
                aws s3 cp ${func_name}.zip s3://${LAMBDA_CODE_BUCKET}/functions/${func_name}.zip \
                    --region ${REGION} $AWS_ARGS

                rm -f ${func_name}.zip
                cd - > /dev/null
            fi
        done
        echo -e "${GREEN}✓ Lambda packages uploaded${NC}"
    else
        echo -e "${YELLOW}⚠ No Lambda source directory found. Skipping Lambda build.${NC}"
    fi
else
    echo -e "${YELLOW}[3/5] Skipping Lambda build (--skip-lambda-build)${NC}"
fi

# Step 4: Deploy CloudFormation stack
echo -e "${GREEN}[4/5] Deploying CloudFormation stack...${NC}"

aws cloudformation deploy \
    --template-file ${INFRA_DIR}/cloudformation/main.yaml \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    --parameter-overrides \
        Environment=${ENVIRONMENT} \
        ProjectName=${PROJECT_NAME} \
        TemplatesBucket=${TEMPLATES_BUCKET} \
        LambdaCodeBucket=${LAMBDA_CODE_BUCKET} \
    $AWS_ARGS \
    --no-fail-on-empty-changeset

echo -e "${GREEN}✓ Stack deployed${NC}"

# Step 5: Get stack outputs
echo -e "${GREEN}[5/5] Retrieving stack outputs...${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table \
    $AWS_ARGS

echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update secrets in Secrets Manager with actual API keys:"
echo "   aws secretsmanager put-secret-value --secret-id ${PROJECT_NAME}-${ENVIRONMENT}-openai-api-key --secret-string '{\"apiKey\":\"your-key\"}'"
echo ""
echo "2. Upload ML model to S3:"
echo "   aws s3 cp model.tar.gz s3://${PROJECT_NAME}-${ENVIRONMENT}-model-artifacts-${ACCOUNT_ID}/models/visibility-predictor/"
echo ""
echo "3. Create initial personas in DynamoDB"
echo ""
echo "4. Test the API endpoint"
echo ""
