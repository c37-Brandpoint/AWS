#!/bin/bash
#
# Brandpoint AI Platform - Ignition Script
#
# Enables EventBridge scheduled jobs AFTER verifying secrets are configured.
# This prevents crash loops from placeholder API keys.
#
# Usage:
#   ./ignite.sh --env dev --region us-east-1
#   ./ignite.sh --env prod --region us-east-1 --profile production
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Defaults
ENVIRONMENT="dev"
REGION="us-east-1"
PROJECT_NAME="brandpoint-ai"
PROFILE=""
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env|--environment)
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
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Enables EventBridge scheduled jobs after verifying secrets are configured."
            echo ""
            echo "Options:"
            echo "  -e, --env        Environment: dev, staging, prod [default: dev]"
            echo "  -r, --region     AWS region [default: us-east-1]"
            echo "  -p, --profile    AWS CLI profile to use"
            echo "  -f, --force      Skip secret validation (not recommended)"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -n "$PROFILE" ]; then
    export AWS_PROFILE="$PROFILE"
    AWS_ARGS="--profile $PROFILE"
else
    AWS_ARGS=""
fi

echo ""
echo "========================================"
echo "Brandpoint AI Platform - Ignition"
echo "========================================"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo ""

# Secrets to check
SECRETS=(
    "${PROJECT_NAME}-${ENVIRONMENT}-openai-api-key"
    "${PROJECT_NAME}-${ENVIRONMENT}-perplexity-api-key"
    "${PROJECT_NAME}-${ENVIRONMENT}-gemini-api-key"
)

# Check each secret for placeholder values
echo "Checking secrets for placeholder values..."
echo ""

SECRETS_OK=true
for secret_id in "${SECRETS[@]}"; do
    echo -n "  Checking $secret_id... "

    # Get secret value
    SECRET_VALUE=$(aws secretsmanager get-secret-value \
        --secret-id "$secret_id" \
        --query "SecretString" \
        --output text \
        --region "$REGION" $AWS_ARGS 2>/dev/null || echo "NOT_FOUND")

    if [ "$SECRET_VALUE" = "NOT_FOUND" ]; then
        echo -e "${RED}NOT FOUND${NC}"
        SECRETS_OK=false
    elif echo "$SECRET_VALUE" | grep -qi "placeholder"; then
        echo -e "${RED}PLACEHOLDER DETECTED${NC}"
        SECRETS_OK=false
    elif echo "$SECRET_VALUE" | grep -qi "your-key\|YOUR-KEY\|your_key\|YOUR_KEY"; then
        echo -e "${RED}TEMPLATE VALUE DETECTED${NC}"
        SECRETS_OK=false
    elif echo "$SECRET_VALUE" | grep -qi "sk-YOUR\|pplx-YOUR"; then
        echo -e "${RED}EXAMPLE VALUE DETECTED${NC}"
        SECRETS_OK=false
    else
        # Check if apiKey field exists and has a reasonable length
        API_KEY=$(echo "$SECRET_VALUE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('apiKey',''))" 2>/dev/null || echo "")
        if [ -z "$API_KEY" ] || [ ${#API_KEY} -lt 10 ]; then
            echo -e "${YELLOW}SUSPICIOUS (key too short or missing)${NC}"
            SECRETS_OK=false
        else
            echo -e "${GREEN}OK${NC}"
        fi
    fi
done

echo ""

if [ "$SECRETS_OK" = false ]; then
    if [ "$FORCE" = true ]; then
        echo -e "${YELLOW}WARNING: Secrets validation failed but --force was specified.${NC}"
        echo ""
    else
        echo -e "${RED}========================================"
        echo -e "IGNITION BLOCKED"
        echo -e "========================================${NC}"
        echo ""
        echo "One or more secrets contain placeholder or invalid values."
        echo "Enabling schedules now would cause immediate Lambda failures."
        echo ""
        echo -e "${YELLOW}To fix:${NC}"
        echo "1. Update secrets with real API keys:"
        echo ""
        echo "   aws secretsmanager put-secret-value \\"
        echo "     --secret-id ${PROJECT_NAME}-${ENVIRONMENT}-openai-api-key \\"
        echo "     --secret-string '{\"apiKey\":\"sk-your-real-key\"}' \\"
        echo "     --region $REGION $AWS_ARGS"
        echo ""
        echo "2. Re-run this script: ./scripts/ignite.sh --env $ENVIRONMENT --region $REGION"
        echo ""
        echo -e "${YELLOW}To skip validation (NOT RECOMMENDED):${NC}"
        echo "   ./scripts/ignite.sh --env $ENVIRONMENT --region $REGION --force"
        echo ""
        exit 1
    fi
fi

# Enable EventBridge rules
echo "Enabling EventBridge scheduled jobs..."
echo ""

RULE_NAME="${PROJECT_NAME}-${ENVIRONMENT}-persona-agent-schedule"

echo -n "  Enabling $RULE_NAME... "
if aws events enable-rule \
    --name "$RULE_NAME" \
    --region "$REGION" $AWS_ARGS 2>/dev/null; then
    echo -e "${GREEN}ENABLED${NC}"
else
    echo -e "${YELLOW}SKIPPED (rule may not exist)${NC}"
fi

echo ""
echo -e "${GREEN}========================================"
echo -e "IGNITION COMPLETE"
echo -e "========================================${NC}"
echo ""
echo "The scheduled jobs are now ENABLED."
echo ""
echo "The Persona Agent will run according to the configured schedule."
echo "Monitor execution in the AWS Step Functions console."
echo ""
echo "To disable schedules:"
echo "  aws events disable-rule --name $RULE_NAME --region $REGION $AWS_ARGS"
echo ""
