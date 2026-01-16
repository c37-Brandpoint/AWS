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
echo -e "${GREEN}[1/7] Creating deployment buckets...${NC}"

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
echo -e "${GREEN}[2/7] Uploading CloudFormation templates...${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/../infrastructure"

aws s3 sync ${INFRA_DIR}/cloudformation/ s3://${TEMPLATES_BUCKET}/cloudformation/ \
    --region ${REGION} $AWS_ARGS \
    --delete

echo -e "${GREEN}✓ Templates uploaded${NC}"

# Step 3: Build and upload Lambda packages (if not skipped)
if [ "$SKIP_LAMBDA_BUILD" = false ]; then
    echo -e "${GREEN}[3/7] Building Lambda packages...${NC}"

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
    echo -e "${YELLOW}[3/7] Skipping Lambda build (--skip-lambda-build)${NC}"
fi

# Step 4: Preflight validation
echo -e "${GREEN}[4/7] Running preflight validation...${NC}"

# Define expected Lambda functions
EXPECTED_FUNCTIONS=(
    "analyze-visibility"
    "content-ingestion"
    "execute-query"
    "feature-extraction"
    "generate-queries"
    "graph-query"
    "graph-update"
    "health-check"
    "insights-generator"
    "intelligence-api"
    "load-persona"
    "persona-api"
    "prediction-api"
    "similarity-search"
    "store-results"
)

# Check all Lambda zips exist in S3
echo "  Checking Lambda packages in S3..."
MISSING_FUNCTIONS=()
for func in "${EXPECTED_FUNCTIONS[@]}"; do
    if ! aws s3 ls s3://${LAMBDA_CODE_BUCKET}/functions/${func}.zip --region ${REGION} $AWS_ARGS > /dev/null 2>&1; then
        MISSING_FUNCTIONS+=("$func")
    fi
done

if [ ${#MISSING_FUNCTIONS[@]} -gt 0 ]; then
    echo -e "${RED}ERROR: Missing Lambda packages in S3:${NC}"
    for func in "${MISSING_FUNCTIONS[@]}"; do
        echo -e "${RED}  - functions/${func}.zip${NC}"
    done
    echo ""
    echo "Run without --skip-lambda-build to package and upload Lambda functions."
    exit 1
fi
echo -e "  ${GREEN}✓ All 15 Lambda packages found in S3${NC}"

# Validate CloudFormation template
echo "  Validating CloudFormation template..."
if ! aws cloudformation validate-template \
    --template-url https://${TEMPLATES_BUCKET}.s3.${REGION}.amazonaws.com/cloudformation/main.yaml \
    --region ${REGION} $AWS_ARGS > /dev/null 2>&1; then
    echo -e "${RED}ERROR: CloudFormation template validation failed${NC}"
    echo "Check the template syntax in infrastructure/cloudformation/main.yaml"
    exit 1
fi
echo -e "  ${GREEN}✓ CloudFormation template valid${NC}"

echo -e "${GREEN}✓ Preflight validation passed${NC}"

# Step 5: Create model artifacts bucket and placeholder
echo -e "${GREEN}[5/7] Preparing model artifacts...${NC}"

MODEL_ARTIFACTS_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-model-artifacts-${ACCOUNT_ID}"
MODEL_KEY="models/visibility-predictor/model.tar.gz"

# Create model artifacts bucket if it doesn't exist
aws s3 mb s3://${MODEL_ARTIFACTS_BUCKET} --region ${REGION} $AWS_ARGS 2>/dev/null || true

aws s3api put-bucket-versioning \
    --bucket ${MODEL_ARTIFACTS_BUCKET} \
    --versioning-configuration Status=Enabled \
    --region ${REGION} $AWS_ARGS 2>/dev/null || true

aws s3api put-public-access-block \
    --bucket ${MODEL_ARTIFACTS_BUCKET} \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
    --region ${REGION} $AWS_ARGS 2>/dev/null || true

aws s3api put-bucket-encryption \
    --bucket ${MODEL_ARTIFACTS_BUCKET} \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
    --region ${REGION} $AWS_ARGS 2>/dev/null || true

# Check if model exists, create placeholder if not
if ! aws s3 ls "s3://${MODEL_ARTIFACTS_BUCKET}/${MODEL_KEY}" --region ${REGION} $AWS_ARGS > /dev/null 2>&1; then
    echo -e "  ${YELLOW}ML model not found. Creating placeholder...${NC}"
    echo -e "  ${YELLOW}NOTE: Upload real model.tar.gz before using prediction endpoints${NC}"

    # Create minimal placeholder model that returns a clear error
    TEMP_MODEL_DIR=$(mktemp -d)
    mkdir -p "${TEMP_MODEL_DIR}/code"

    cat > "${TEMP_MODEL_DIR}/code/inference.py" << 'INFERENCE_EOF'
"""
Placeholder model for SageMaker endpoint.
Replace this with your actual trained model.
"""
import json

def model_fn(model_dir):
    return {"placeholder": True}

def input_fn(request_body, request_content_type):
    return json.loads(request_body)

def predict_fn(input_data, model):
    return {
        "error": "PLACEHOLDER_MODEL",
        "message": "This is a placeholder model. Upload your trained model.tar.gz to replace this.",
        "score": 0.0,
        "confidence": 0.0
    }

def output_fn(prediction, accept):
    return json.dumps(prediction)
INFERENCE_EOF

    # Create model.tar.gz
    cd "${TEMP_MODEL_DIR}"
    tar -czvf model.tar.gz code/ > /dev/null 2>&1

    # Upload to S3
    aws s3 cp model.tar.gz "s3://${MODEL_ARTIFACTS_BUCKET}/${MODEL_KEY}" \
        --region ${REGION} $AWS_ARGS > /dev/null

    # Cleanup
    rm -rf "${TEMP_MODEL_DIR}"

    echo -e "  ${GREEN}✓ Placeholder model uploaded${NC}"
else
    echo -e "  ${GREEN}✓ Model artifact found in S3${NC}"
fi

# Step 6: Deploy CloudFormation stack
echo -e "${GREEN}[6/7] Deploying CloudFormation stack...${NC}"

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

# Step 7: Get stack outputs
echo -e "${GREEN}[7/7] Retrieving stack outputs...${NC}"

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
echo "   aws secretsmanager put-secret-value --secret-id ${PROJECT_NAME}-${ENVIRONMENT}-perplexity-api-key --secret-string '{\"apiKey\":\"your-key\"}'"
echo "   aws secretsmanager put-secret-value --secret-id ${PROJECT_NAME}-${ENVIRONMENT}-gemini-api-key --secret-string '{\"apiKey\":\"your-key\"}'"
echo ""
echo "2. Replace placeholder ML model in S3 with trained model:"
echo "   aws s3 cp model.tar.gz s3://${MODEL_ARTIFACTS_BUCKET}/${MODEL_KEY}"
echo "   (A placeholder model was deployed - predictions will return errors until replaced)"
echo ""
echo "3. Run smoke tests to verify deployment:"
echo "   ./scripts/smoke-test.sh ${ENVIRONMENT} ${REGION}"
echo ""
echo "4. Create initial personas in DynamoDB"
echo ""
echo "5. Test the API endpoint"
echo ""
