#!/bin/bash

set -e

echo "=== MLflow UI Assets Builder ==="
START_TIME=$(date +%s)

# Store the original directory where script was called from
ORIGINAL_DIR="$(pwd)"

# Function to parse pyproject.toml for MLflow dependency
get_mlflow_dependency() {
    python3 -c "
import sys
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        # Fallback to manual parsing
        with open('pyproject.toml', 'r') as f:
            content = f.read()
            for line in content.split('\\n'):
                if 'mlflow' in line and 'git+' in line:
                    # Extract the git URL
                    start = line.find('git+')
                    end = line.find('\"', start)
                    if start != -1 and end != -1:
                        print(line[start:end])
                        sys.exit(0)
        sys.exit(1)

with open('pyproject.toml', 'rb') as f:
    import tomllib
    data = tomllib.load(f)
    deps = data.get('project', {}).get('dependencies', [])
    for dep in deps:
        if dep.startswith('mlflow') and 'git+' in dep:
            # Extract git URL from dependency
            start = dep.find('git+')
            print(dep[start:])
            sys.exit(0)
    sys.exit(1)
"
}

# Check if MLflow dependency is from git
echo "Checking MLflow dependency in pyproject.toml..."
MLFLOW_DEP=$(get_mlflow_dependency 2>/dev/null || echo "")

if [ -z "$MLFLOW_DEP" ]; then
    echo "MLflow is installed from PyPI, not from a git repository."
    echo "Downloading pre-built UI assets from PyPI wheel..."
    
    # Download and extract UI assets from PyPI (same as deploy.sh does)
    TEMP_ASSETS_DIR="/tmp/mlflow-pypi-assets-$(date +%s)"
    mkdir -p "$TEMP_ASSETS_DIR"
    
    echo "Fetching latest MLflow version from PyPI..."
    MLFLOW_VERSION=$(curl -s https://pypi.org/pypi/mlflow/json | python3 -c "import json,sys;print(json.load(sys.stdin)['info']['version'])")
    echo "MLflow version: $MLFLOW_VERSION"
    
    echo "Downloading MLflow wheel from PyPI..."
    curl -sL "https://files.pythonhosted.org/packages/py3/m/mlflow/mlflow-${MLFLOW_VERSION}-py3-none-any.whl" -o "$TEMP_ASSETS_DIR/mlflow.whl"
    
    echo "Extracting UI assets from wheel..."
    cd "$TEMP_ASSETS_DIR"
    unzip -q mlflow.whl 'mlflow/server/js/build/*'
    
    # Return to original directory
    cd "$ORIGINAL_DIR"
    
    # Create mlflow-ui-assets directory if it doesn't exist
    mkdir -p mlflow-ui-assets
    
    # Copy UI assets
    echo "Copying UI assets to mlflow-ui-assets..."
    cp -r "$TEMP_ASSETS_DIR/mlflow/server/js/build/"* mlflow-ui-assets/
    
    # Clean up temp directory
    rm -rf "$TEMP_ASSETS_DIR"
    
    # Remove source map files to avoid deployment size limits (>10MB files not allowed)
    echo "Removing source map files (too large for deployment)..."
    find mlflow-ui-assets -name "*.map" -type f -delete
    
    echo "✅ MLflow UI assets downloaded successfully from PyPI!"
    echo "Assets are in: mlflow-ui-assets/"
    
    # List what was created
    echo ""
    echo "Created files:"
    ls -la mlflow-ui-assets/ | head -10
    exit 0
fi

echo "Found git dependency: $MLFLOW_DEP"
echo "Will build UI assets from source..."

# Parse git URL and branch
if [[ "$MLFLOW_DEP" =~ git\+([^@]+)@(.+) ]]; then
    GIT_URL="${BASH_REMATCH[1]}"
    GIT_BRANCH="${BASH_REMATCH[2]}"
elif [[ "$MLFLOW_DEP" =~ git\+(.+) ]]; then
    GIT_URL="${BASH_REMATCH[1]}"
    GIT_BRANCH="main"
else
    echo "Could not parse git URL from: $MLFLOW_DEP"
    exit 1
fi

echo "Git URL: $GIT_URL"
echo "Branch: $GIT_BRANCH"

# Create temp directory for cloning
TEMP_DIR="/tmp/mlflow-ui-build-$(date +%s)"
echo "Creating temporary directory: $TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Clean up function
cleanup() {
    echo "Cleaning up temporary directory..."
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Clone only the JS directory using partial clone with tree filter
echo "Cloning MLflow repository (partial clone of mlflow/server/js only)..."
CLONE_START=$(date +%s)
cd "$TEMP_DIR"

# Use partial clone with tree:0 filter - only download trees on demand
git clone --filter=tree:0 --depth=1 --branch "$GIT_BRANCH" --single-branch --no-checkout "$GIT_URL" mlflow
cd mlflow
git sparse-checkout init --cone
git sparse-checkout set mlflow/server/js
git checkout "$GIT_BRANCH"
cd ..
CLONE_END=$(date +%s)
echo "Clone took $((CLONE_END - CLONE_START)) seconds"

# Navigate to js directory
cd mlflow/mlflow/server/js

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "Error: package.json not found in mlflow/server/js"
    exit 1
fi

# Build UI assets
echo "Installing dependencies and building MLflow UI assets..."
BUILD_START=$(date +%s)
yarn install && yarn build
BUILD_END=$(date +%s)
echo "Total build time: $((BUILD_END - BUILD_START)) seconds"

# Check if build was successful
if [ ! -d "build" ]; then
    echo "Error: Build directory not created"
    exit 1
fi

# Return to original directory
cd "$ORIGINAL_DIR"

# Create mlflow-ui-assets directory if it doesn't exist
echo "Creating mlflow-ui-assets directory..."
mkdir -p mlflow-ui-assets

# Copy built assets
echo "Copying built assets to mlflow-ui-assets..."
cp -r "$TEMP_DIR/mlflow/mlflow/server/js/build/"* mlflow-ui-assets/

# Remove source map files to avoid deployment size limits (>10MB files not allowed)
echo "Removing source map files (too large for deployment)..."
find mlflow-ui-assets -name "*.map" -type f -delete

echo "✅ MLflow UI assets built successfully from source!"
echo "Assets are in: mlflow-ui-assets/"

# List what was created
echo ""
echo "Created files:"
ls -la mlflow-ui-assets/ | head -10

END_TIME=$(date +%s)
echo ""
echo "Total time: $((END_TIME - START_TIME)) seconds"