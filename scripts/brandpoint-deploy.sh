#!/bin/bash
#
# Brandpoint AI Platform - One-Command Deployment
#
# This is the ONLY script Brandpoint IT needs to run.
# It orchestrates preflight checks, deployment, smoke tests, and ignition.
#
# Usage:
#   ./brandpoint-deploy.sh                                    # Dev environment, auto-select CIDR
#   ./brandpoint-deploy.sh --env prod                         # Prod environment
#   ./brandpoint-deploy.sh --env dev --cidr 10.102.0.0/16    # Custom CIDR
#   ./brandpoint-deploy.sh --env dev --resume                 # Resume from last step
#
# For help: ./brandpoint-deploy.sh --help
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Defaults
ENVIRONMENT="dev"
REGION="us-east-1"
VPC_CIDR=""
PROFILE=""
RESUME=false
SKIP_CONFIRM=false

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
STATE_FILE="$PROJECT_ROOT/.deploy-state"

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
        -c|--cidr)
            VPC_CIDR="$2"
            shift 2
            ;;
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        --resume)
            RESUME=true
            shift
            ;;
        -y|--yes)
            SKIP_CONFIRM=true
            shift
            ;;
        -h|--help)
            echo ""
            echo -e "${BOLD}Brandpoint AI Platform - One-Command Deployment${NC}"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -e, --env          Environment: dev, staging, prod [default: dev]"
            echo "  -r, --region       AWS region [default: us-east-1]"
            echo "  -c, --cidr         VPC CIDR block [default: auto-select safe CIDR]"
            echo "  -p, --profile      AWS CLI profile to use"
            echo "  --resume           Resume from last completed step"
            echo "  -y, --yes          Skip confirmation prompts"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                              # Deploy dev with auto-selected CIDR"
            echo "  $0 --env prod                   # Deploy prod with auto-selected CIDR"
            echo "  $0 --cidr 10.102.0.0/16        # Deploy dev with specific CIDR"
            echo "  $0 --resume                     # Resume interrupted deployment"
            echo ""
            echo "This script will:"
            echo "  1. Run preflight checks (credentials, quotas, CIDR conflicts)"
            echo "  2. Auto-select a safe VPC CIDR if not specified"
            echo "  3. Deploy all AWS infrastructure"
            echo "  4. Run smoke tests to verify deployment"
            echo "  5. Guide you through secrets configuration"
            echo "  6. Enable scheduled jobs (Ignition) when ready"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set AWS profile
if [ -n "$PROFILE" ]; then
    export AWS_PROFILE="$PROFILE"
    AWS_ARGS="--profile $PROFILE"
else
    AWS_ARGS=""
fi

# State management functions
save_state() {
    echo "$1" > "$STATE_FILE"
}

get_state() {
    if [ -f "$STATE_FILE" ]; then
        cat "$STATE_FILE"
    else
        echo "0"
    fi
}

clear_state() {
    rm -f "$STATE_FILE"
}

# Print step header
print_step() {
    local step=$1
    local total=$2
    local title=$3
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  STEP ${step}/${total}: ${title}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print error and exit
fail_with_help() {
    local error_msg=$1
    local fix_msg=$2
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  DEPLOYMENT FAILED${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${RED}WHAT FAILED:${NC}"
    echo "  $error_msg"
    echo ""
    echo -e "${YELLOW}HOW TO FIX:${NC}"
    echo "  $fix_msg"
    echo ""
    echo -e "${CYAN}After fixing, resume with:${NC}"
    echo "  $0 --env $ENVIRONMENT --region $REGION --resume"
    echo ""
    exit 1
}

# Banner
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                          ║${NC}"
echo -e "${GREEN}║            ${BOLD}BRANDPOINT AI PLATFORM - DEPLOYMENT${NC}${GREEN}                          ║${NC}"
echo -e "${GREEN}║                                                                          ║${NC}"
echo -e "${GREEN}║  One command. Safe defaults. Guided deployment.                          ║${NC}"
echo -e "${GREEN}║                                                                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Environment:  ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "  Region:       ${YELLOW}${REGION}${NC}"
echo -e "  VPC CIDR:     ${YELLOW}${VPC_CIDR:-auto-select}${NC}"
echo ""

# Check for resume
LAST_STEP=$(get_state)
if [ "$RESUME" = true ] && [ "$LAST_STEP" != "0" ]; then
    echo -e "${CYAN}Resuming from step $((LAST_STEP + 1))...${NC}"
    START_STEP=$((LAST_STEP + 1))
else
    START_STEP=1
    clear_state
fi

#=============================================================================
# STEP 1: Preflight Checks
#=============================================================================
if [ $START_STEP -le 1 ]; then
    print_step 1 6 "PREFLIGHT CHECKS"

    # Check AWS CLI
    echo -n "Checking AWS CLI... "
    if ! command -v aws &> /dev/null; then
        fail_with_help "AWS CLI is not installed" "Install from https://aws.amazon.com/cli/"
    fi
    print_success "Installed"

    # Check AWS credentials
    echo -n "Checking AWS credentials... "
    if ! aws sts get-caller-identity $AWS_ARGS > /dev/null 2>&1; then
        fail_with_help "AWS credentials not configured" "Run 'aws configure' or set AWS_PROFILE"
    fi
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text $AWS_ARGS)
    IDENTITY=$(aws sts get-caller-identity --query Arn --output text $AWS_ARGS)
    print_success "Authenticated"
    echo "    Account: $ACCOUNT_ID"
    echo "    Identity: $IDENTITY"

    # Check required tools
    for tool in python3 zip; do
        echo -n "Checking $tool... "
        if ! command -v $tool &> /dev/null; then
            fail_with_help "$tool is not installed" "Install $tool before continuing"
        fi
        print_success "Installed"
    done

    # Check Linux for Lambda builds
    echo -n "Checking build environment... "
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        fail_with_help "Lambda builds require Linux (current: $OSTYPE)" \
            "Use WSL on Windows, or run from a Linux machine/EC2 instance"
    fi
    print_success "Linux detected"

    # Check EIP quota
    echo -n "Checking Elastic IP quota... "
    EIP_LIMIT=$(aws service-quotas get-service-quota \
        --service-code ec2 --quota-code L-0263D0A3 \
        --query "Quota.Value" --output text $AWS_ARGS 2>/dev/null || echo "5")
    EIP_USED=$(aws ec2 describe-addresses --query "length(Addresses)" --output text $AWS_ARGS 2>/dev/null || echo "0")
    [ "$EIP_LIMIT" = "None" ] && EIP_LIMIT=5
    [ "$EIP_USED" = "None" ] && EIP_USED=0
    EIP_AVAILABLE=$((EIP_LIMIT - EIP_USED))
    if [ "$EIP_AVAILABLE" -lt 1 ]; then
        fail_with_help "No Elastic IPs available ($EIP_USED/$EIP_LIMIT used)" \
            "Release unused Elastic IPs or request a quota increase in AWS Console"
    fi
    print_success "$EIP_AVAILABLE available"

    # Check VPC quota
    echo -n "Checking VPC quota... "
    VPC_LIMIT=$(aws service-quotas get-service-quota \
        --service-code vpc --quota-code L-F678F1CE \
        --query "Quota.Value" --output text $AWS_ARGS 2>/dev/null || echo "5")
    VPC_COUNT=$(aws ec2 describe-vpcs --query "length(Vpcs)" --output text $AWS_ARGS 2>/dev/null || echo "0")
    [ "$VPC_LIMIT" = "None" ] && VPC_LIMIT=5
    [ "$VPC_COUNT" = "None" ] && VPC_COUNT=0
    VPC_AVAILABLE=$((VPC_LIMIT - VPC_COUNT))
    if [ "$VPC_AVAILABLE" -lt 1 ]; then
        fail_with_help "No VPC capacity ($VPC_COUNT/$VPC_LIMIT used)" \
            "Delete unused VPCs or request a quota increase in AWS Console"
    fi
    print_success "$VPC_AVAILABLE available"

    save_state 1
    print_success "Preflight checks passed"
fi

#=============================================================================
# STEP 2: CIDR Selection (Auto or Manual)
#=============================================================================
if [ $START_STEP -le 2 ]; then
    print_step 2 6 "NETWORK CONFIGURATION"

    # Get all existing VPC CIDRs
    echo "Scanning existing VPCs for CIDR conflicts..."
    EXISTING_CIDRS=$(aws ec2 describe-vpcs --query "Vpcs[].CidrBlock" --output text $AWS_ARGS 2>/dev/null || echo "")

    if [ -n "$EXISTING_CIDRS" ]; then
        echo "  Found existing VPCs:"
        for cidr in $EXISTING_CIDRS; do
            echo "    - $cidr"
        done
    else
        echo "  No existing VPCs found"
    fi
    echo ""

    # Auto-select CIDR if not provided
    if [ -z "$VPC_CIDR" ]; then
        echo "Auto-selecting safe CIDR..."

        # Candidate CIDRs (less commonly used ranges)
        CANDIDATES=(
            "10.200.0.0/16"
            "10.201.0.0/16"
            "10.202.0.0/16"
            "172.20.0.0/16"
            "172.21.0.0/16"
            "10.100.0.0/16"
        )

        # Check each candidate for overlap using Python
        for candidate in "${CANDIDATES[@]}"; do
            OVERLAP=false

            if [ -n "$EXISTING_CIDRS" ]; then
                # Use Python to check for CIDR overlap (not just equality)
                OVERLAP=$(python3 << EOF
import ipaddress
candidate = ipaddress.ip_network('$candidate')
existing = '''$EXISTING_CIDRS'''.split()
for cidr in existing:
    if cidr:
        try:
            existing_net = ipaddress.ip_network(cidr)
            if candidate.overlaps(existing_net):
                print('true')
                exit(0)
        except:
            pass
print('false')
EOF
)
            fi

            if [ "$OVERLAP" = "false" ]; then
                VPC_CIDR="$candidate"
                echo -e "  ${GREEN}Selected: $VPC_CIDR (no conflicts)${NC}"
                break
            else
                echo "  Skipping $candidate (overlaps with existing VPC)"
            fi
        done

        if [ -z "$VPC_CIDR" ]; then
            fail_with_help "Could not find a non-overlapping CIDR" \
                "Manually specify a CIDR with: --cidr <your-cidr>"
        fi
    else
        # Validate user-provided CIDR
        echo "Validating provided CIDR: $VPC_CIDR"

        if [ -n "$EXISTING_CIDRS" ]; then
            OVERLAP=$(python3 << EOF
import ipaddress
candidate = ipaddress.ip_network('$VPC_CIDR')
existing = '''$EXISTING_CIDRS'''.split()
for cidr in existing:
    if cidr:
        try:
            existing_net = ipaddress.ip_network(cidr)
            if candidate.overlaps(existing_net):
                print('true')
                exit(0)
        except:
            pass
print('false')
EOF
)
            if [ "$OVERLAP" = "true" ]; then
                fail_with_help "CIDR $VPC_CIDR overlaps with an existing VPC" \
                    "Choose a different CIDR. Suggestions: 10.200.0.0/16, 10.201.0.0/16, 172.20.0.0/16"
            fi
        fi
        print_success "CIDR $VPC_CIDR is valid (no overlaps)"
    fi

    echo ""
    echo -e "  ${BOLD}VPC CIDR for this deployment: ${YELLOW}$VPC_CIDR${NC}"
    echo ""

    if [ "$SKIP_CONFIRM" = false ]; then
        read -p "Continue with this CIDR? (Y/n): " CONFIRM
        if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
            echo "Cancelled. Specify a different CIDR with --cidr"
            exit 1
        fi
    fi

    save_state 2
fi

#=============================================================================
# STEP 3: Deploy Infrastructure
#=============================================================================
if [ $START_STEP -le 3 ]; then
    print_step 3 6 "DEPLOYING INFRASTRUCTURE"

    echo "This will create all AWS resources. This typically takes 30-45 minutes."
    echo "(OpenSearch and Neptune clusters take time to provision)"
    echo ""

    if [ "$SKIP_CONFIRM" = false ]; then
        read -p "Start deployment? (Y/n): " CONFIRM
        if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
            echo "Cancelled."
            exit 1
        fi
    fi

    echo ""
    echo "Running deploy.sh..."
    echo ""

    # Run deploy.sh with all parameters
    if ! "$SCRIPT_DIR/deploy.sh" \
        --environment "$ENVIRONMENT" \
        --region "$REGION" \
        --cidr "$VPC_CIDR" \
        --yes \
        ${PROFILE:+--profile "$PROFILE"}; then
        fail_with_help "CloudFormation deployment failed" \
            "Check the AWS CloudFormation console for detailed error messages"
    fi

    save_state 3
    print_success "Infrastructure deployed successfully"
fi

#=============================================================================
# STEP 4: Smoke Tests
#=============================================================================
if [ $START_STEP -le 4 ]; then
    print_step 4 6 "VERIFYING DEPLOYMENT"

    echo "Running smoke tests to verify all resources..."
    echo ""

    if ! "$SCRIPT_DIR/smoke-test.sh" "$ENVIRONMENT" "$REGION" ${PROFILE:+--profile "$PROFILE"}; then
        echo ""
        echo -e "${YELLOW}Some resources may still be provisioning.${NC}"
        echo "This is normal for OpenSearch and Neptune (can take 15-20 minutes)."
        echo ""
        read -p "Re-run smoke tests? (Y/n): " RERUN
        if [[ ! "$RERUN" =~ ^[Nn]$ ]]; then
            "$SCRIPT_DIR/smoke-test.sh" "$ENVIRONMENT" "$REGION" ${PROFILE:+--profile "$PROFILE"} || true
        fi
    fi

    save_state 4
    print_success "Deployment verified"
fi

#=============================================================================
# STEP 5: Secrets Configuration
#=============================================================================
if [ $START_STEP -le 5 ]; then
    print_step 5 6 "SECRETS CONFIGURATION"

    PROJECT_NAME="brandpoint-ai"

    echo -e "${YELLOW}IMPORTANT: You must configure API keys before enabling scheduled jobs.${NC}"
    echo ""
    echo "Copy and run these commands with your actual API keys:"
    echo ""
    echo -e "${CYAN}# OpenAI API Key (for ChatGPT queries)${NC}"
    echo "aws secretsmanager put-secret-value \\"
    echo "  --secret-id ${PROJECT_NAME}-${ENVIRONMENT}-openai-api-key \\"
    echo "  --secret-string '{\"apiKey\":\"sk-YOUR-OPENAI-KEY\"}' \\"
    echo "  --region $REGION $AWS_ARGS"
    echo ""
    echo -e "${CYAN}# Perplexity API Key${NC}"
    echo "aws secretsmanager put-secret-value \\"
    echo "  --secret-id ${PROJECT_NAME}-${ENVIRONMENT}-perplexity-api-key \\"
    echo "  --secret-string '{\"apiKey\":\"pplx-YOUR-PERPLEXITY-KEY\"}' \\"
    echo "  --region $REGION $AWS_ARGS"
    echo ""
    echo -e "${CYAN}# Google Gemini API Key${NC}"
    echo "aws secretsmanager put-secret-value \\"
    echo "  --secret-id ${PROJECT_NAME}-${ENVIRONMENT}-gemini-api-key \\"
    echo "  --secret-string '{\"apiKey\":\"YOUR-GEMINI-KEY\"}' \\"
    echo "  --region $REGION $AWS_ARGS"
    echo ""
    echo -e "${CYAN}# Hub Service Account Key (for Brandpoint Hub integration)${NC}"
    echo "aws secretsmanager put-secret-value \\"
    echo "  --secret-id ${PROJECT_NAME}-${ENVIRONMENT}-hub-service-account-key \\"
    echo "  --secret-string '{\"apiKey\":\"YOUR-HUB-KEY\"}' \\"
    echo "  --region $REGION $AWS_ARGS"
    echo ""
    echo -e "${BOLD}After running the commands above, press Enter to continue...${NC}"
    read -p ""

    save_state 5
    print_success "Secrets configuration step complete"
fi

#=============================================================================
# STEP 6: Ignition (Enable Schedules)
#=============================================================================
if [ $START_STEP -le 6 ]; then
    print_step 6 6 "IGNITION - ENABLE SCHEDULED JOBS"

    echo "The EventBridge schedule is currently DISABLED for safety."
    echo "This prevents errors from placeholder secrets."
    echo ""
    echo -e "${YELLOW}Only enable if you have configured ALL secrets in Step 5.${NC}"
    echo ""

    if [ "$SKIP_CONFIRM" = false ]; then
        read -p "Enable scheduled jobs now? (y/N): " CONFIRM
        if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
            echo ""
            echo "Skipping ignition. To enable later, run:"
            echo "  ./scripts/ignite.sh --env $ENVIRONMENT --region $REGION"
            echo ""
            save_state 6
        else
            echo ""
            echo "Running ignition..."
            if "$SCRIPT_DIR/ignite.sh" --env "$ENVIRONMENT" --region "$REGION" ${PROFILE:+--profile "$PROFILE"}; then
                save_state 6
                print_success "Scheduled jobs enabled"
            else
                echo ""
                echo -e "${YELLOW}Ignition skipped. Configure secrets first, then run:${NC}"
                echo "  ./scripts/ignite.sh --env $ENVIRONMENT --region $REGION"
            fi
        fi
    else
        echo "Skipping ignition (auto mode). Run manually when ready:"
        echo "  ./scripts/ignite.sh --env $ENVIRONMENT --region $REGION"
        save_state 6
    fi
fi

#=============================================================================
# COMPLETE
#=============================================================================
clear_state

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                          ║${NC}"
echo -e "${GREEN}║                    ${BOLD}DEPLOYMENT COMPLETE!${NC}${GREEN}                                   ║${NC}"
echo -e "${GREEN}║                                                                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Environment:${NC}  $ENVIRONMENT"
echo -e "  ${BOLD}Region:${NC}       $REGION"
echo -e "  ${BOLD}VPC CIDR:${NC}     $VPC_CIDR"
echo ""
echo -e "  ${BOLD}Next Steps:${NC}"
echo "  1. Verify secrets are configured (if not done in Step 5)"
echo "  2. Enable scheduled jobs: ./scripts/ignite.sh --env $ENVIRONMENT"
echo "  3. Test the API endpoints"
echo "  4. Set up VPC Peering for RDS access (see DEPLOYMENT_GUIDE.md)"
echo ""
echo -e "  ${BOLD}Useful Commands:${NC}"
echo "  - View stack outputs: aws cloudformation describe-stacks --stack-name brandpoint-ai-$ENVIRONMENT"
echo "  - Run smoke tests:    ./scripts/smoke-test.sh $ENVIRONMENT $REGION"
echo "  - Rollback:           ./scripts/rollback.sh $ENVIRONMENT $REGION"
echo ""
echo -e "  ${BOLD}Documentation:${NC}"
echo "  - Quick reference:    docs/BRANDPOINT_RUNBOOK.md"
echo "  - Full guide:         docs/DEPLOYMENT_GUIDE.md"
echo ""
