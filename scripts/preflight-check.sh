#!/bin/bash
#
# Brandpoint AI Platform - Preflight Check
#
# Run BEFORE deploy.sh to validate environment is ready
#
# Usage:
#   ./preflight-check.sh
#   ./preflight-check.sh --profile myprofile
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROFILE=""
ERRORS=0
WARNINGS=0

# Parse arguments
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "Brandpoint AI Platform - Preflight Check"
echo "========================================"
echo ""

# 1. Check AWS CLI
echo -n "Checking AWS CLI... "
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version 2>&1 | head -n1)
    echo -e "${GREEN}OK${NC} ($AWS_VERSION)"
else
    echo -e "${RED}MISSING${NC}"
    echo "  Install AWS CLI: https://aws.amazon.com/cli/"
    ERRORS=$((ERRORS + 1))
fi

# 2. Check AWS credentials
echo -n "Checking AWS credentials... "
if aws sts get-caller-identity $AWS_ARGS > /dev/null 2>&1; then
    ACCOUNT=$(aws sts get-caller-identity --query Account --output text $AWS_ARGS)
    IDENTITY=$(aws sts get-caller-identity --query Arn --output text $AWS_ARGS)
    echo -e "${GREEN}OK${NC}"
    echo "  Account: $ACCOUNT"
    echo "  Identity: $IDENTITY"
else
    echo -e "${RED}FAILED${NC}"
    echo "  Run 'aws configure' or set AWS_PROFILE"
    ERRORS=$((ERRORS + 1))
fi

# 3. Check required tools
for tool in zip pip python3; do
    echo -n "Checking $tool... "
    if command -v $tool &> /dev/null; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}MISSING${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

# 4. Check Bedrock model access
echo -n "Checking Bedrock model access... "
if aws bedrock list-foundation-models --query "modelSummaries[?modelId=='anthropic.claude-3-5-sonnet-20241022-v2:0']" --output text $AWS_ARGS 2>/dev/null | grep -q "anthropic"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "  May need to request Bedrock model access in AWS Console"
    WARNINGS=$((WARNINGS + 1))
fi

# 5. Check Lambda source directories
echo -n "Checking Lambda source code... "
LAMBDA_DIR="$PROJECT_ROOT/infrastructure/lambda"
MISSING=0
EXPECTED_FUNCTIONS=(
    "load-persona"
    "generate-queries"
    "execute-query"
    "analyze-visibility"
    "store-results"
    "feature-extraction"
    "content-ingestion"
    "graph-update"
    "similarity-search"
    "graph-query"
    "insights-generator"
    "prediction-api"
    "persona-api"
    "intelligence-api"
    "health-check"
)

for func in "${EXPECTED_FUNCTIONS[@]}"; do
    if [ ! -f "$LAMBDA_DIR/$func/index.py" ]; then
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}OK${NC} (${#EXPECTED_FUNCTIONS[@]} functions found)"
else
    echo -e "${RED}FAILED${NC} ($MISSING functions missing)"
    ERRORS=$((ERRORS + 1))
fi

# 6. Check CloudFormation templates
echo -n "Checking CloudFormation templates... "
CF_DIR="$PROJECT_ROOT/infrastructure/cloudformation"
REQUIRED_TEMPLATES=(
    "main.yaml"
    "00-foundation.yaml"
    "01-storage.yaml"
    "02-databases.yaml"
    "03-compute.yaml"
    "04-orchestration.yaml"
    "05-api.yaml"
    "06-monitoring.yaml"
    "07-secrets.yaml"
)
MISSING_CF=0
MISSING_LIST=""

for tpl in "${REQUIRED_TEMPLATES[@]}"; do
    if [ ! -f "$CF_DIR/$tpl" ]; then
        MISSING_CF=$((MISSING_CF + 1))
        MISSING_LIST="$MISSING_LIST $tpl"
    fi
done

if [ $MISSING_CF -eq 0 ]; then
    echo -e "${GREEN}OK${NC} (${#REQUIRED_TEMPLATES[@]} templates)"
else
    echo -e "${RED}FAILED${NC}"
    echo "  Missing:$MISSING_LIST"
    ERRORS=$((ERRORS + 1))
fi

# 7. Validate main template syntax
echo -n "Validating CloudFormation syntax... "
if aws cloudformation validate-template --template-body "file://$CF_DIR/main.yaml" $AWS_ARGS > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    echo "  Template has syntax errors"
    ERRORS=$((ERRORS + 1))
fi

# 8. Check for circular dependency fix
echo -n "Checking circular dependency fix... "
if grep -q "STEP_FUNCTION_NAME" "$CF_DIR/03-compute.yaml" 2>/dev/null; then
    echo -e "${GREEN}OK${NC} (fixed)"
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "  Circular dependency may exist - check 03-compute.yaml"
    WARNINGS=$((WARNINGS + 1))
fi

# 9. Check deploy script exists and is executable
echo -n "Checking deploy.sh... "
if [ -x "$SCRIPT_DIR/deploy.sh" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "  Run: chmod +x scripts/deploy.sh"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "========================================"
if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}PREFLIGHT PASSED WITH WARNINGS${NC}"
        echo "$WARNINGS warning(s) - review before deploying"
    else
        echo -e "${GREEN}PREFLIGHT PASSED${NC}"
        echo "Ready to deploy!"
    fi
    echo ""
    echo "Run: ./scripts/deploy.sh --environment dev --region us-east-1"
    exit 0
else
    echo -e "${RED}PREFLIGHT FAILED${NC}"
    echo "$ERRORS error(s) must be resolved before deploying"
    exit 1
fi
