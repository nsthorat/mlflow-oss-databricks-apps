# Technical Design Document

## High-Level Design

The MLflow OSS Server on Databricks Apps replaces the default FastAPI template with a full MLflow tracking server that integrates natively with Databricks services.

### Architecture Overview
```
[Databricks Apps Platform]
    ↓
[MLflow Server Process]
    ├── Web UI (Port 80)
    ├── REST API (Port 80)
    └── Backend Connections
        ├── Tracking Store → Databricks
        ├── Model Registry → Unity Catalog
        └── Artifact Store → UC Volumes
```

### Technology Stack
- **Application Server**: MLflow server (replaces uvicorn/FastAPI)
- **Runtime**: Python 3.11+ with MLflow dependencies
- **Backend Storage**: Databricks for experiments, Unity Catalog for models
- **Authentication**: Databricks Apps service principal

### Libraries and Frameworks
```python
# Core Dependencies
mlflow>=2.10.0  # Full MLflow package (not mlflow-skinny)
databricks-sdk  # For Databricks integration
gunicorn  # MLflow server uses gunicorn internally
```

### Data Architecture
- **Experiment Tracking**: Stored in Databricks workspace via `MLFLOW_TRACKING_URI=databricks`
- **Model Registry**: Unity Catalog via `MLFLOW_REGISTRY_URI=databricks-uc`
- **Artifacts**: Stored in Unity Catalog Volumes at `/Volumes/main/default/mlflow-artifacts`
- **Metrics/Parameters**: Databricks tracking store

### Integration Points
- **Databricks Workspace**: Direct connection via service principal
- **Unity Catalog**: Model registry backend
- **Databricks Apps Platform**: Lifecycle management and deployment

## Implementation Plan

### Phase 1: Core MLflow Server Setup
1. **Replace FastAPI with MLflow Server**
   - Remove `server/` directory (FastAPI code)
   - Remove `client/` directory (React frontend)
   - Update `app.yaml` to use `mlflow server` command
   - Configure MLflow dependencies in `pyproject.toml`

2. **Configure Databricks Integration**
   - Set environment variables in `app.yaml`:
     - `MLFLOW_TRACKING_URI=databricks`
     - `MLFLOW_REGISTRY_URI=databricks-uc`
     - `MLFLOW_DEFAULT_ARTIFACT_ROOT=/Volumes/main/default/mlflow-artifacts`
   - Databricks Apps automatically provides `DATABRICKS_HOST` and `DATABRICKS_TOKEN`

3. **Update Entry Point**
   ```yaml
   # app.yaml command section
   command: ["mlflow", "server", "--host", "0.0.0.0", "--port", "80"]
   ```

### Phase 2: Deployment Configuration
1. **Dependencies Management**
   - Update `pyproject.toml` with MLflow and required dependencies
   - Ensure all MLflow server dependencies are included
   - Remove unnecessary frontend build tools

2. **Environment Configuration**
   ```yaml
   # app.yaml environment section
   env:
     - name: MLFLOW_TRACKING_URI
       value: databricks
     - name: MLFLOW_REGISTRY_URI  
       value: databricks-uc
     - name: MLFLOW_DEFAULT_ARTIFACT_ROOT
       value: /Volumes/main/default/mlflow-artifacts
   # Note: DATABRICKS_HOST and DATABRICKS_TOKEN are automatically provided by Databricks Apps
   ```

3. **Deployment Scripts**
   - Update `deploy.sh` to skip frontend build
   - Ensure proper requirements generation
   - Validate MLflow server startup

### Phase 3: Testing & Validation
1. **Local Testing**
   - Test MLflow server locally with Databricks connection
   - Verify UI loads and connects to Databricks
   - Test basic experiment creation and model logging

2. **Deployment Testing**
   - Deploy to Databricks Apps
   - Verify MLflow UI accessibility
   - Test API endpoints
   - Validate Unity Catalog integration

## Development Workflow

### File Structure Changes
```
mlflow-oss-databricks-apps/
├── app.yaml              # Updated with MLflow server command
├── pyproject.toml        # MLflow dependencies
├── requirements.txt      # Generated from pyproject.toml
├── deploy.sh            # Modified for MLflow deployment
├── docs/
│   ├── product.md      # Product requirements
│   └── design.md       # This document
└── README.md           # Usage instructions
```

### Removed Components
- `server/` directory (FastAPI application)
- `client/` directory (React frontend)
- `scripts/make_fastapi_client.py` (no longer needed)
- Frontend-related configuration files

### Key Configuration Files

**app.yaml**:
```yaml
command: ["mlflow", "server", "--host", "0.0.0.0", "--port", "80"]
env:
  - name: MLFLOW_TRACKING_URI
    value: databricks
  - name: MLFLOW_REGISTRY_URI
    value: databricks-uc
  - name: MLFLOW_DEFAULT_ARTIFACT_ROOT
    value: /Volumes/main/default/mlflow-artifacts
# DATABRICKS_HOST and DATABRICKS_TOKEN are automatically provided by Databricks Apps
```

**pyproject.toml**:
```toml
[project]
dependencies = [
    "mlflow>=2.10.0",
    "databricks-sdk",
    "gunicorn",
]
```

### Deployment Process
1. Clean existing template code
2. Configure MLflow dependencies
3. Update app.yaml with MLflow server command
4. Set environment variables for Databricks integration
5. Deploy to Databricks Apps
6. Verify MLflow server is accessible and functional