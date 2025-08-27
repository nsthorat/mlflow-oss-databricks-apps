# Product Requirements Document

## Overview

**MLflow Open Source Server on Databricks Apps** - A template application that deploys the complete open source MLflow server on Databricks Apps platform with native Databricks integration.

This application replaces the standard FastAPI template with the MLflow server (`mlflow server` command), providing the full MLflow tracking server, model registry, and web UI while leveraging Databricks as the backend storage and compute platform.

## Target Users

- **Data Scientists** - Track experiments, log metrics, and manage model artifacts
- **ML Engineers** - Deploy and version models through MLflow Model Registry  
- **ML Platform Teams** - Template for deploying MLflow infrastructure on Databricks
- **Organizations** - Standardized MLflow deployment pattern for Databricks environments

## Core Features

### MLflow Server Deployment
- **Complete MLflow Server**: Full `mlflow server` deployment with web UI and REST API
- **Native Databricks Integration**: Direct connection to Databricks services via environment configuration
- **Service Principal Authentication**: Automatic authentication using app service principal (no OBO required)

### MLflow Functionality
- **Experiment Tracking**: Log parameters, metrics, artifacts, and models
- **Model Registry**: Version and stage models with Databricks Unity Catalog backend  
- **Web UI**: Full MLflow web interface for experiment visualization and model management
- **REST API**: Complete MLflow REST API for programmatic access

### Databricks Integration
- **Tracking Backend**: `MLFLOW_TRACKING_URI=databricks` for experiment storage in Databricks
- **Registry Backend**: `MLFLOW_REGISTRY_URI=databricks-uc` for Unity Catalog model registry
- **Authentication**: Leverages Databricks Apps service principal for seamless access

## User Stories

1. **As a Data Scientist**, I want to access the MLflow web UI to visualize my experiments and compare model performance across runs
2. **As an ML Engineer**, I want to use the MLflow API to programmatically register and deploy models from my training pipelines  
3. **As a Platform Engineer**, I want a template to deploy MLflow server that integrates natively with our Databricks workspace
4. **As a Team Lead**, I want a centralized MLflow server that my team can use without managing infrastructure

## Success Metrics

- **Deployment Success**: MLflow server starts successfully with Databricks integration
- **UI Accessibility**: MLflow web interface loads and displays experiments/models from Databricks
- **API Functionality**: MLflow REST API endpoints respond correctly for tracking and registry operations
- **Template Reusability**: Other teams can easily deploy their own MLflow instances using this template

## Implementation Priority

### Phase 1: Core MLflow Server (MVP)
- Replace FastAPI server with MLflow server entry point
- Configure Databricks environment variables in app.yaml
- Ensure MLflow dependencies are properly installed
- Verify basic MLflow UI loads and connects to Databricks

### Phase 2: Databricks Integration Validation  
- Test experiment logging through MLflow API
- Verify model registration with Unity Catalog
- Validate authentication flow with service principal
- Ensure UI properly displays Databricks-stored experiments

### Phase 3: Template Documentation
- Document deployment process and configuration
- Add troubleshooting guide for common issues
- Provide example usage patterns for teams
- Create migration guide from other MLflow deployments

## Technical Requirements

### Environment Configuration
```yaml
# app.yaml environment variables
MLFLOW_TRACKING_URI: "databricks"
MLFLOW_REGISTRY_URI: "databricks-uc"  
DATABRICKS_HOST: ${DATABRICKS_HOST}
DATABRICKS_TOKEN: ${DATABRICKS_TOKEN}
```

### Application Entry Point
- Replace `uvicorn server.app:app` with `mlflow server` command
- Maintain Databricks Apps compatibility and lifecycle management

### Dependencies
- MLflow open source package (not mlflow-skinny)
- All MLflow server dependencies for full functionality
- Maintain compatibility with Databricks Apps runtime