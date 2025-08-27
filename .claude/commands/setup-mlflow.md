---
description: "Setup and deploy MLflow OSS on Databricks Apps"
---

# MLflow OSS Setup for Databricks Apps

I'm helping you set up and deploy MLflow OSS on Databricks Apps.

---

## 🚨 CRITICAL: Databricks CLI Execution Rule 🚨

**VERY IMPORTANT: For environment-specific authentication, prefix with environment setup:**

```bash
# ✅ CORRECT - Use environment setup when needed
source .env.local && export DATABRICKS_HOST && export DATABRICKS_TOKEN && databricks current-user me
source .env.local && export DATABRICKS_HOST && export DATABRICKS_TOKEN && databricks apps list
source .env.local && export DATABRICKS_HOST && export DATABRICKS_TOKEN && databricks workspace list /

# ✅ ALSO CORRECT - Use databricks CLI directly with profiles
databricks current-user me --profile myprofile
databricks apps list --profile myprofile
databricks workspace list / --profile myprofile
```

**Why this is required:**
- Ensures environment variables are loaded from .env.local
- Exports authentication variables to environment
- Prevents authentication failures and missing configuration

---

**Let me check your current setup:**

## 🔍 Progress Detection

**I'll first check if your MLflow app is already set up:**

- Run `./app_status.sh` to see if .env.local is configured and app exists
- Check if `mlflow-ui-assets/` directory exists
- Verify deployment status

**Based on this detection, I'll either:**
- **Help you deploy** if the app is set up but not deployed
- **Help you complete setup** if configuration is incomplete
- **Ask if you want to change configuration** if everything is already set up

**If your app is already configured, I'll ask:**

"Your MLflow app is configured and ready. Do you want to change any of the following?

1. **MLflow installation source** 
   - Currently: [mlflow==3.3.1 from PyPI / mlflow from git branch]
   - Change to: Different PyPI version or Git branch
   
2. **MLflow tracking server**
   - Currently: [Databricks / SQLite at path]
   - Change to: Switch between Databricks workspace or SQLite database
   
3. **Databricks app configuration**
   - Currently: App name, resource limits, environment variables
   - Change to: Modify app.yaml settings
   
4. **Deploy as-is** - Keep current configuration and deploy

Enter your choice (1-4):"

After making any changes, I'll ask: "Would you like to change anything else before deploying?"

**Let's get started:**

## Progress Overview

⏺ **Step 1: Environment Setup**
   - a) Configure MLflow Source
   - b) Configure Tracking Server
   - c) Interactive Setup
   - d) Verify Configuration

⏺ **Step 2: Deploy MLflow OSS**
   - a) Deploy to Databricks Apps
   - b) Verify Deployment

---

## Configuration Change Mode

**If you selected to change a specific configuration:**

**For MLflow source change:**
- I'll jump directly to **Step 1a: Configure MLflow Source**
- After completing, I'll ask if you want to change anything else

**For Tracking server change:**
- I'll jump directly to **Step 1b: Configure Tracking Server**
- After completing, I'll ask if you want to change anything else

**For App configuration change:**
- I'll help you update app.yaml settings directly
- Common changes include environment variables, resource limits, etc.
- After completing, I'll ask if you want to change anything else

**After any change:**
I'll ask: "Would you like to (1) Change something else, or (2) Deploy now?"
- If you choose to change something else, I'll show the options again
- If you choose to deploy, I'll proceed to Step 2: Deploy MLflow OSS

---

## Step 1: Environment Setup

**a) Configure MLflow Source**

Before we begin setup, I need to know which version of MLflow you want to use:

**Option 1: MLflow from PyPI (stable release)**
- Uses the latest stable MLflow release from PyPI
- Pre-built UI assets included
- Faster installation

If you choose Option 1, I'll show you available versions by running:

```bash
uv run python list_mlflow_versions.py
```

Then I'll ask: "Which version would you like to install? (Press Enter for latest, or specify version like '3.3.1')"

**Note:** If you ask to "show me all versions", I'll run `uv run python list_mlflow_versions.py --json` to display the complete list of all 151+ versions.

**Option 2: MLflow from a Git branch (development)**
- Uses a specific branch from GitHub
- Requires building UI assets from source
- Allows testing of custom MLflow features

**I'll ask you:**
- "Do you want to use MLflow from PyPI or from a Git branch?"
- If Git branch: "Please provide the branch in format `username/branch-name` (e.g., `nsthorat/nik-databricks-tracking`)"

**Based on your choice, I'll:**
1. Update `pyproject.toml` with the appropriate MLflow dependency:
   - **PyPI with specific version**: 
     - If "latest" or Enter pressed: Use `uv add mlflow` to add the latest version
     - If specific version (e.g., "3.3.0"): Use `uv add mlflow==3.3.0`
   - **Git branch**: Parse the format and add dependency:
     - For `username/branch-name`: `mlflow @ git+https://github.com/username/mlflow.git@branch-name`
     - For `nsthorat/nik-databricks-tracking`: `mlflow @ git+https://github.com/nsthorat/mlflow.git@nik-databricks-tracking`
2. Run `uv sync` to validate and install the dependency
3. Verify the installation was successful before proceeding

**b) Configure Tracking Server**

Now I need to configure where MLflow will store experiments and artifacts:

**Option 1: Databricks Tracking Server (recommended)**
- Uses Databricks workspace for experiment tracking
- Uses Unity Catalog for model registry
- Integrated with Databricks features
- Default artifact location: `/Volumes/main/default/mlflow-artifacts`

**Option 2: SQLite (Open Source)**
- Uses SQLite database files in Unity Catalog Volumes
- Fully self-contained solution
- Requires configuring paths for:
  - Tracking database (e.g., `/Volumes/main/default/mlflow-tracking.db`)
  - Registry database (e.g., `/Volumes/main/default/mlflow-registry.db`)
  - Artifact storage (e.g., `/Volumes/main/default/mlflow-artifacts`)

**I'll ask you:**
- "Do you want to use Databricks tracking server or SQLite (open source)?"

**For Databricks tracking server:**
- I'll set in `app.yaml`:
  ```yaml
  - name: MLFLOW_TRACKING_URI
    value: databricks
  - name: MLFLOW_REGISTRY_URI
    value: databricks-uc
  ```
- I'll ask: "Do you want to change the default artifact root? (currently: `/Volumes/main/default/mlflow-artifacts`)"
- If yes, I'll update `MLFLOW_DEFAULT_ARTIFACT_ROOT` in app.yaml

**For SQLite (open source):**
- I'll ask for paths (or use defaults):
  - Tracking DB path (default: `/Volumes/main/default/mlflow-tracking.db`)
  - Registry DB path (default: `/Volumes/main/default/mlflow-registry.db`)
  - Artifact root (default: `/Volumes/main/default/mlflow-artifacts`)
- I'll set in `app.yaml`:
  ```yaml
  - name: MLFLOW_TRACKING_URI
    value: sqlite:///Volumes/main/default/mlflow-tracking.db
  - name: MLFLOW_REGISTRY_URI
    value: sqlite:///Volumes/main/default/mlflow-registry.db
  - name: MLFLOW_DEFAULT_ARTIFACT_ROOT
    value: /Volumes/main/default/mlflow-artifacts
  ```

**Note:** Make sure the Unity Catalog volume paths exist and are accessible by the service principal.

**c) Interactive Setup**

After configuring MLflow and the tracking server, I'll run the interactive setup script to configure your app:

1. I'll use `osascript` to open a new terminal window in your project directory (preferring iTerm if available)
2. Run `./setup.sh --auto-close` which will guide you through:
   - Databricks authentication (PAT or profile)
   - Environment variable configuration
   - Python and frontend dependency installation
   - Claude MCP Playwright setup
3. When setup completes, the terminal will close automatically
4. I'll confirm the setup was successful

**Command I'll execute:**
```bash
# Use the open_setup.sh script which handles terminal detection gracefully
./open_setup.sh
```

**Note:** The setup script requires interactive input, so it must run in a separate terminal window that you can interact with.

*I'll wait for the setup to complete before proceeding to the next step.*

**d) Verify Configuration**

After the setup completes, I'll verify your configuration:

1. **Check for existing app:**
   - I'll read the app name from `.env.local` (DATABRICKS_APP_NAME)
   - Run `databricks apps list | grep DATABRICKS_APP_NAME` to check if it exists
   - **I'll use `./app_status.sh` to get comprehensive app status and display it nicely**
   - **I'll always display:**
     - **App Name:** [app name from .env.local]
     - **App URL:** [app url from app_status.sh]
     - **App Management:** [DATABRICKS_HOST from .env.local]/apps/[app name]

2. **Verify environment variables:**
   - Check that DATABRICKS_HOST and DATABRICKS_TOKEN are set correctly
   - Verify MLflow dependencies are installed in pyproject.toml
   
**I'll display:**
   - **App Name:** [app name from .env.local]
   - **App URL:** [if app exists]
   - **Status:** [ready for deployment / needs configuration]

---

## Step 2: Deploy MLflow OSS

**I'll help you deploy MLflow OSS to Databricks Apps:**

**a) Deploy to Databricks Apps**

1. **Create app if needed:**
   - If the app doesn't exist, I'll use `./deploy.sh --create`
   - This creates and deploys the app in one step

2. **Deploy the app:**
   ```bash
   ./deploy.sh
   ```
   - Automatically detects MLflow source type (git vs PyPI)
   - Builds UI assets if needed (from git) or downloads them (from PyPI)
   - Generates requirements.txt
   - Deploys to Databricks workspace
   
3. **Monitor deployment:**
   - Check deployment logs for any issues
   - Verify successful startup

**b) Verify Deployment**

1. **Check app status:**
   ```bash
   databricks apps list | grep mlflow-oss
   ```

2. **Monitor logs for startup:**
   ```bash
   uv run python dba_logz.py <app-url> --duration 60
   ```
   - Look for "Application startup complete" or "Uvicorn running"
   - Check for any Python exceptions or import errors

3. **Test the app:**
   ```bash
   uv run python dba_client.py <app-url> /
   ```
   - Verify MLflow UI is accessible
   - Confirm all endpoints are working

**I'll display:**
   - **App Name:** [from .env.local]
   - **App URL:** [from deployment]
   - **Status:** [deployment status]
   - **Service Principal:** [from app_status.sh]

---

## Important Post-Deployment Notes

**1. Grant Permissions to Other Users:**
To allow other users to access your MLflow app, you need to grant them permissions:
- Go to: `{DATABRICKS_HOST}/apps/{APP_NAME}` (e.g., https://e2-dogfood.staging.cloud.databricks.com/apps/mlflow-oss)
- Click the **"Permissions"** button
- Add users or groups and set their access level

**2. MLflow Authentication:**
The application uses a service principal for MLflow authentication:
- The service principal (displayed above) is automatically used for accessing MLflow experiments
- This ensures secure access to your MLflow tracking data
- No additional authentication setup is required for the app to access experiments

---

**That's it! Your MLflow OSS instance is now running on Databricks Apps.**