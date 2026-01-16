#!/bin/bash
#
# Brandpoint AI Platform - Post-Deploy Smoke Test
#
# Run AFTER deploy.sh completes to verify deployment
#
# Usage:
#   ./smoke-test.sh dev us-east-1
#   ./smoke-test.sh prod us-east-1 --profile production
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENVIRONMENT="${1:-dev}"
REGION="${2:-us-east-1}"
PROJECT="brandpoint-ai"
STACK_NAME="${PROJECT}-${ENVIRONMENT}"
PROFILE=""

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

PASSED=0
FAILED=0
WARNINGS=0

echo "========================================"
echo "Brandpoint AI Platform - Smoke Test"
echo "========================================"
echo ""
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo ""

# Check if stack exists
echo -n "Checking stack exists... "
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
    --region $REGION $AWS_ARGS \
    --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$STACK_STATUS" == "NOT_FOUND" ]; then
    echo -e "${RED}FAILED${NC}"
    echo "Stack $STACK_NAME does not exist"
    exit 1
elif [[ "$STACK_STATUS" == *"COMPLETE"* ]] && [[ "$STACK_STATUS" != *"ROLLBACK"* ]]; then
    echo -e "${GREEN}PASS${NC} ($STACK_STATUS)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAILED${NC} ($STACK_STATUS)"
    FAILED=$((FAILED + 1))
fi

# Get stack outputs
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text $AWS_ARGS)
API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
    --region $REGION $AWS_ARGS \
    --query "Stacks[0].Outputs[?OutputKey=='APIEndpoint'].OutputValue" --output text 2>/dev/null || echo "")

echo ""
echo "API Endpoint: ${API_ENDPOINT:-NOT_FOUND}"
echo ""

# 1. Health check endpoint
echo -n "Testing /health endpoint... "
if [ -n "$API_ENDPOINT" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_ENDPOINT}/health" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" == "200" ]; then
        echo -e "${GREEN}PASS${NC} (HTTP 200)"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}FAILED${NC} (HTTP $HTTP_CODE)"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${YELLOW}SKIP${NC} (no API endpoint)"
    WARNINGS=$((WARNINGS + 1))
fi

# 2. Check Lambda functions
echo -n "Checking Lambda functions... "
LAMBDA_COUNT=$(aws lambda list-functions --region $REGION $AWS_ARGS \
    --query "Functions[?starts_with(FunctionName, '${PROJECT}-${ENVIRONMENT}')].FunctionName" \
    --output text 2>/dev/null | wc -w)
if [ "$LAMBDA_COUNT" -ge 15 ]; then
    echo -e "${GREEN}PASS${NC} ($LAMBDA_COUNT functions)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAILED${NC} (only $LAMBDA_COUNT functions, expected 15+)"
    FAILED=$((FAILED + 1))
fi

# 3. Check Step Functions state machine
echo -n "Checking Step Functions... "
SM_ARN="arn:aws:states:${REGION}:${ACCOUNT_ID}:stateMachine:${PROJECT}-${ENVIRONMENT}-persona-agent"
SM_STATUS=$(aws stepfunctions describe-state-machine \
    --state-machine-arn "$SM_ARN" \
    --region $REGION $AWS_ARGS \
    --query "status" --output text 2>/dev/null || echo "NOT_FOUND")
if [ "$SM_STATUS" == "ACTIVE" ]; then
    echo -e "${GREEN}PASS${NC} (ACTIVE)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAILED${NC} ($SM_STATUS)"
    FAILED=$((FAILED + 1))
fi

# 4. Check OpenSearch domain
echo -n "Checking OpenSearch... "
OS_PROCESSING=$(aws opensearch describe-domain \
    --domain-name "${PROJECT}-${ENVIRONMENT}-vectors" \
    --region $REGION $AWS_ARGS \
    --query "DomainStatus.Processing" --output text 2>/dev/null || echo "NOT_FOUND")
if [ "$OS_PROCESSING" == "False" ]; then
    echo -e "${GREEN}PASS${NC} (Ready)"
    PASSED=$((PASSED + 1))
elif [ "$OS_PROCESSING" == "True" ]; then
    echo -e "${YELLOW}WARN${NC} (Still processing)"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${RED}FAILED${NC} ($OS_PROCESSING)"
    FAILED=$((FAILED + 1))
fi

# 5. Check Neptune cluster
echo -n "Checking Neptune... "
NEPTUNE_STATUS=$(aws neptune describe-db-clusters \
    --db-cluster-identifier "${PROJECT}-${ENVIRONMENT}-knowledge-graph" \
    --region $REGION $AWS_ARGS \
    --query "DBClusters[0].Status" --output text 2>/dev/null || echo "NOT_FOUND")
if [ "$NEPTUNE_STATUS" == "available" ]; then
    echo -e "${GREEN}PASS${NC} (available)"
    PASSED=$((PASSED + 1))
elif [ "$NEPTUNE_STATUS" == "creating" ]; then
    echo -e "${YELLOW}WARN${NC} (creating - may take 10-15 min)"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${RED}FAILED${NC} ($NEPTUNE_STATUS)"
    FAILED=$((FAILED + 1))
fi

# 6. Check SageMaker endpoint
echo -n "Checking SageMaker endpoint... "
SM_ENDPOINT_STATUS=$(aws sagemaker describe-endpoint \
    --endpoint-name "${PROJECT}-${ENVIRONMENT}-visibility-predictor" \
    --region $REGION $AWS_ARGS \
    --query "EndpointStatus" --output text 2>/dev/null || echo "NOT_FOUND")
if [ "$SM_ENDPOINT_STATUS" == "InService" ]; then
    echo -e "${GREEN}PASS${NC} (InService)"
    PASSED=$((PASSED + 1))
elif [ "$SM_ENDPOINT_STATUS" == "Creating" ]; then
    echo -e "${YELLOW}WARN${NC} (Creating - may take 5-10 min)"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${RED}FAILED${NC} ($SM_ENDPOINT_STATUS)"
    FAILED=$((FAILED + 1))
fi

# 7. Check DynamoDB tables
echo -n "Checking DynamoDB tables... "
TABLES_FOUND=0
for table in "personas" "query-results" "predictions"; do
    TABLE_STATUS=$(aws dynamodb describe-table \
        --table-name "${PROJECT}-${ENVIRONMENT}-${table}" \
        --region $REGION $AWS_ARGS \
        --query "Table.TableStatus" --output text 2>/dev/null || echo "NOT_FOUND")
    if [ "$TABLE_STATUS" == "ACTIVE" ]; then
        TABLES_FOUND=$((TABLES_FOUND + 1))
    fi
done
if [ "$TABLES_FOUND" -eq 3 ]; then
    echo -e "${GREEN}PASS${NC} (3 tables active)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAILED${NC} (only $TABLES_FOUND/3 tables active)"
    FAILED=$((FAILED + 1))
fi

# 8. Check S3 buckets
echo -n "Checking S3 buckets... "
BUCKETS_FOUND=0
for bucket_suffix in "model-artifacts" "results-archive" "data-lake"; do
    BUCKET_NAME="${PROJECT}-${ENVIRONMENT}-${bucket_suffix}-${ACCOUNT_ID}"
    if aws s3 ls "s3://${BUCKET_NAME}" --region $REGION $AWS_ARGS > /dev/null 2>&1; then
        BUCKETS_FOUND=$((BUCKETS_FOUND + 1))
    fi
done
if [ "$BUCKETS_FOUND" -eq 3 ]; then
    echo -e "${GREEN}PASS${NC} (3 buckets)"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}WARN${NC} ($BUCKETS_FOUND/3 buckets found)"
    WARNINGS=$((WARNINGS + 1))
fi

# 9. Check secrets exist
echo -n "Checking Secrets Manager... "
SECRETS_FOUND=0
for secret in "openai-api-key" "perplexity-api-key" "gemini-api-key" "hub-service-account-key"; do
    if aws secretsmanager describe-secret \
        --secret-id "${PROJECT}-${ENVIRONMENT}-${secret}" \
        --region $REGION $AWS_ARGS > /dev/null 2>&1; then
        SECRETS_FOUND=$((SECRETS_FOUND + 1))
    fi
done
if [ "$SECRETS_FOUND" -ge 4 ]; then
    echo -e "${GREEN}PASS${NC} ($SECRETS_FOUND secrets)"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}WARN${NC} ($SECRETS_FOUND/4 secrets found)"
    WARNINGS=$((WARNINGS + 1))
fi

# Summary
echo ""
echo "========================================"
TOTAL=$((PASSED + FAILED))
echo "Results: $PASSED/$TOTAL passed"
if [ $WARNINGS -gt 0 ]; then
    echo "Warnings: $WARNINGS (may still be provisioning)"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}SMOKE TEST PASSED WITH WARNINGS${NC}"
        echo "Some resources may still be provisioning."
        echo "Re-run in a few minutes if needed."
    else
        echo -e "${GREEN}SMOKE TEST PASSED${NC}"
        echo "Deployment verified successfully!"
    fi
    exit 0
else
    echo -e "${RED}SMOKE TEST FAILED${NC}"
    echo "$FAILED check(s) failed. Review stack and CloudWatch logs."
    exit 1
fi
