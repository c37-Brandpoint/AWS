#!/bin/bash
#
# Package Lambda Functions for Deployment
# Creates deployment packages for all Lambda functions
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="$PROJECT_ROOT/infrastructure/lambda"
BUILD_DIR="$PROJECT_ROOT/build/lambda"
S3_BUCKET="${1:-}"

echo "========================================"
echo "Packaging Brandpoint Lambda Functions"
echo "========================================"

# Create build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# List of Lambda functions to package
FUNCTIONS=(
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

# Package common utilities first
echo ""
echo "Packaging common utilities..."
COMMON_DIR="$BUILD_DIR/common"
mkdir -p "$COMMON_DIR"
if [ -d "$LAMBDA_DIR/common" ]; then
    cp -r "$LAMBDA_DIR/common/"* "$COMMON_DIR/"
fi

# Package each function
for func in "${FUNCTIONS[@]}"; do
    FUNC_DIR="$LAMBDA_DIR/$func"

    if [ ! -d "$FUNC_DIR" ]; then
        echo "Warning: Function directory not found: $func"
        continue
    fi

    echo ""
    echo "Packaging: $func"

    PACKAGE_DIR="$BUILD_DIR/$func"
    mkdir -p "$PACKAGE_DIR"

    # Copy function code
    cp "$FUNC_DIR/index.py" "$PACKAGE_DIR/"

    # Copy common utilities
    if [ -d "$COMMON_DIR" ]; then
        mkdir -p "$PACKAGE_DIR/common"
        cp -r "$COMMON_DIR/"* "$PACKAGE_DIR/common/" 2>/dev/null || true
    fi

    # Install dependencies if requirements.txt exists
    if [ -f "$FUNC_DIR/requirements.txt" ]; then
        echo "  Installing dependencies..."
        pip install -r "$FUNC_DIR/requirements.txt" -t "$PACKAGE_DIR" --quiet --upgrade
    fi

    # Create zip package
    echo "  Creating zip package..."
    cd "$PACKAGE_DIR"
    zip -r "$BUILD_DIR/${func}.zip" . -x "*.pyc" -x "__pycache__/*" -q
    cd - > /dev/null

    # Get package size
    SIZE=$(du -h "$BUILD_DIR/${func}.zip" | cut -f1)
    echo "  Package size: $SIZE"
done

echo ""
echo "========================================"
echo "Packaging complete!"
echo "========================================"
echo ""
echo "Packages created in: $BUILD_DIR"
echo ""

# List all packages
ls -lh "$BUILD_DIR"/*.zip

# Upload to S3 if bucket specified
if [ -n "$S3_BUCKET" ]; then
    echo ""
    echo "Uploading to S3: s3://$S3_BUCKET/functions/"

    for func in "${FUNCTIONS[@]}"; do
        if [ -f "$BUILD_DIR/${func}.zip" ]; then
            aws s3 cp "$BUILD_DIR/${func}.zip" "s3://$S3_BUCKET/functions/${func}.zip"
            echo "  Uploaded: ${func}.zip"
        fi
    done

    echo ""
    echo "All packages uploaded to S3"
fi

echo ""
echo "Done!"
