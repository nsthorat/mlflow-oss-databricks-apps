#!/bin/bash

echo "=== MLflow Server Startup Script ==="
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Find where MLflow is installed
MLFLOW_PATH=$(python -c 'import mlflow.server; import os; print(os.path.dirname(mlflow.server.__file__))')
echo "MLflow server module path: $MLFLOW_PATH"

# Check if js/build exists in MLflow installation
echo "Checking for existing js/build directory..."
if [ -d "$MLFLOW_PATH/js/build" ]; then
    echo "Found existing js/build at $MLFLOW_PATH/js/build"
    ls -la "$MLFLOW_PATH/js/build" | head -5
else
    echo "js/build directory not found in MLflow installation"
fi

# Check if our UI assets exist
echo "Checking for mlflow-ui-assets in current directory..."
if [ -d "mlflow-ui-assets" ]; then
    echo "Found mlflow-ui-assets directory"
    ls -la mlflow-ui-assets | head -5
    
    # Create js/build directory if it doesn't exist
    echo "Creating js/build directory in MLflow installation..."
    mkdir -p "$MLFLOW_PATH/js/build"
    
    # Copy UI assets to MLflow's expected location
    echo "Copying UI assets to $MLFLOW_PATH/js/build..."
    cp -r mlflow-ui-assets/* "$MLFLOW_PATH/js/build/"
    
    echo "UI assets copied successfully"
    echo "Checking copied files..."
    ls -la "$MLFLOW_PATH/js/build" | head -5
else
    echo "ERROR: mlflow-ui-assets directory not found!"
fi

echo "Environment variables:"
echo "MLFLOW_TRACKING_URI: $MLFLOW_TRACKING_URI"
echo "MLFLOW_REGISTRY_URI: $MLFLOW_REGISTRY_URI"
echo "MLFLOW_DEFAULT_ARTIFACT_ROOT: $MLFLOW_DEFAULT_ARTIFACT_ROOT"
echo "DATABRICKS_HOST: $DATABRICKS_HOST"
echo "DATABRICKS_TOKEN: [REDACTED]"

echo "Starting MLflow server with configured backends..."
echo "Backend Store URI: $MLFLOW_TRACKING_URI"
echo "Registry Store URI: $MLFLOW_REGISTRY_URI"
echo "Default Artifact Root: $MLFLOW_DEFAULT_ARTIFACT_ROOT"

exec mlflow server \
    --host 0.0.0.0 \
    --port 8000 \
    --backend-store-uri "$MLFLOW_TRACKING_URI" \
    --registry-store-uri "$MLFLOW_REGISTRY_URI" \
    --default-artifact-root "$MLFLOW_DEFAULT_ARTIFACT_ROOT"