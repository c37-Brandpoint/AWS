#!/bin/bash
#
# Brandpoint AI Platform - Preflight Check
#
# Run BEFORE deploy.sh to validate environment is ready
#
# Usage:
#   ./preflight-check.sh
#   ./preflight-check.sh --cidr 10.101.0.0/16
#   ./preflight-check.sh --profile myprofile --cidr 10.102.0.0/16
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROFILE=""
VPC_CIDR="10.100.0.0/16"
ERRORS=0
WARNINGS=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -c|--cidr)
            VPC_CIDR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -p, --profile    AWS CLI profile to use"
            echo "  -c, --cidr       VPC CIDR to check for conflicts [default: 10.100.0.0/16]"
            echo "  -h, --help       Show this help message"
            exit 0
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
echo "Network Reconnaissance (CIDR: $VPC_CIDR)"
echo "========================================"
echo ""

# 10. Check for VPC CIDR conflicts
echo -n "Checking for CIDR conflicts... "
CONFLICT=$(aws ec2 describe-vpcs \
    --filters Name=cidr,Values=$VPC_CIDR \
    --query "Vpcs[].VpcId" --output text $AWS_ARGS 2>/dev/null || echo "")

if [ -n "$CONFLICT" ] && [ "$CONFLICT" != "None" ]; then
    echo -e "${RED}CONFLICT DETECTED${NC}"
    echo -e "  ${RED}CRITICAL: CIDR $VPC_CIDR is already in use by VPC: $CONFLICT${NC}"
    echo "  You MUST choose a different CIDR. Common alternatives:"
    echo "    - 10.101.0.0/16"
    echo "    - 10.102.0.0/16"
    echo "    - 172.20.0.0/16"
    echo ""
    echo "  Run deployment with: ./scripts/deploy.sh --cidr <new-cidr>"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}OK${NC} (no conflict)"
fi

# 11. Check Elastic IP quota (needed for NAT Gateway)
echo -n "Checking Elastic IP quota... "
EIP_LIMIT=$(aws service-quotas get-service-quota \
    --service-code ec2 \
    --quota-code L-0263D0A3 \
    --query "Quota.Value" --output text $AWS_ARGS 2>/dev/null || echo "5")
EIP_USED=$(aws ec2 describe-addresses --query "length(Addresses)" --output text $AWS_ARGS 2>/dev/null || echo "0")

# Handle potential "None" or empty responses
if [ "$EIP_LIMIT" = "None" ] || [ -z "$EIP_LIMIT" ]; then
    EIP_LIMIT=5
fi
if [ "$EIP_USED" = "None" ] || [ -z "$EIP_USED" ]; then
    EIP_USED=0
fi

EIP_AVAILABLE=$((EIP_LIMIT - EIP_USED))
if [ "$EIP_AVAILABLE" -lt 1 ]; then
    echo -e "${RED}FAIL${NC} ($EIP_USED/$EIP_LIMIT used)"
    echo "  NAT Gateway requires an Elastic IP. Request quota increase or release unused EIPs."
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}OK${NC} ($EIP_USED/$EIP_LIMIT used, $EIP_AVAILABLE available)"
fi

# 12. Check VPC quota
echo -n "Checking VPC quota... "
VPC_LIMIT=$(aws service-quotas get-service-quota \
    --service-code vpc \
    --quota-code L-F678F1CE \
    --query "Quota.Value" --output text $AWS_ARGS 2>/dev/null || echo "5")
VPC_COUNT=$(aws ec2 describe-vpcs --query "length(Vpcs)" --output text $AWS_ARGS 2>/dev/null || echo "0")

# Handle potential "None" or empty responses
if [ "$VPC_LIMIT" = "None" ] || [ -z "$VPC_LIMIT" ]; then
    VPC_LIMIT=5
fi
if [ "$VPC_COUNT" = "None" ] || [ -z "$VPC_COUNT" ]; then
    VPC_COUNT=0
fi

VPC_AVAILABLE=$((VPC_LIMIT - VPC_COUNT))
if [ "$VPC_AVAILABLE" -lt 1 ]; then
    echo -e "${RED}FAIL${NC} ($VPC_COUNT/$VPC_LIMIT used)"
    echo "  No VPC capacity available. Request quota increase or delete unused VPCs."
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}OK${NC} ($VPC_COUNT/$VPC_LIMIT used, $VPC_AVAILABLE available)"
fi

# 13. Check NAT Gateway quota
echo -n "Checking NAT Gateway quota... "
NAT_LIMIT=$(aws service-quotas get-service-quota \
    --service-code vpc \
    --quota-code L-FE5A380F \
    --query "Quota.Value" --output text $AWS_ARGS 2>/dev/null || echo "5")
NAT_COUNT=$(aws ec2 describe-nat-gateways \
    --filter Name=state,Values=available,pending \
    --query "length(NatGateways)" --output text $AWS_ARGS 2>/dev/null || echo "0")

# Handle potential "None" or empty responses
if [ "$NAT_LIMIT" = "None" ] || [ -z "$NAT_LIMIT" ]; then
    NAT_LIMIT=5
fi
if [ "$NAT_COUNT" = "None" ] || [ -z "$NAT_COUNT" ]; then
    NAT_COUNT=0
fi

NAT_AVAILABLE=$((NAT_LIMIT - NAT_COUNT))
if [ "$NAT_AVAILABLE" -lt 1 ]; then
    echo -e "${RED}FAIL${NC} ($NAT_COUNT/$NAT_LIMIT used)"
    echo "  No NAT Gateway capacity. Request quota increase or delete unused NAT Gateways."
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}OK${NC} ($NAT_COUNT/$NAT_LIMIT used, $NAT_AVAILABLE available)"
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
    echo "Run: ./scripts/deploy.sh --environment dev --region us-east-1 --cidr $VPC_CIDR"
    exit 0
else
    echo -e "${RED}PREFLIGHT FAILED${NC}"
    echo "$ERRORS error(s) must be resolved before deploying"
    echo ""
    echo "Fix the issues above before running deploy.sh"
    exit 1
fi
