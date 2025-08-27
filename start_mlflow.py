#!/usr/bin/env python3
"""
Simple MLflow startup script with embedded volume sync functionality.
"""

import os
import sys
import time
import subprocess
import signal
import threading
import logging
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Try to import databricks SDK
try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.files import DirectoryEntry
    DATABRICKS_SDK_AVAILABLE = True
except ImportError:
    logger.warning("⚠️  Databricks SDK not available - sync daemon disabled")
    DATABRICKS_SDK_AVAILABLE = False


class SimpleVolumeSyncDaemon:
    """Simplified volume sync daemon embedded in the startup script."""
    
    def __init__(self, local_path: str, volume_path: str):
        self.local_path = Path(local_path)
        self.volume_path = volume_path
        self.workspace_client = WorkspaceClient() if DATABRICKS_SDK_AVAILABLE else None
        self.running = False
        self.sync_thread = None
        
        # Ensure local directory exists
        self.local_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Sync daemon initialized: {local_path} ↔️ {volume_path}")
    
    def sync_from_volume(self):
        """Initial sync from volume to local."""
        if not DATABRICKS_SDK_AVAILABLE:
            logger.warning("⚠️  SDK not available, skipping volume sync")
            return
        
        try:
            # Ensure volume directory exists
            self.workspace_client.files.create_directory(self.volume_path)
            logger.info("✅ Volume directory confirmed/created")
            
            # List and download files from volume
            self._sync_directory(self.volume_path, self.local_path)
            logger.info("✅ Initial sync from volume completed")
        except Exception as e:
            logger.warning(f"⚠️  Volume sync error: {e}")
    
    def _sync_directory(self, volume_dir: str, local_dir: Path):
        """Recursively sync a directory from volume to local."""
        try:
            contents = self.workspace_client.files.list_directory_contents(volume_dir)
            for item in contents:
                volume_item_path = f"{volume_dir}/{item.name}"
                local_item_path = local_dir / item.name
                
                if item.file_type == DirectoryEntry.FileType.DIRECTORY:
                    local_item_path.mkdir(parents=True, exist_ok=True)
                    self._sync_directory(volume_item_path, local_item_path)
                elif item.file_type == DirectoryEntry.FileType.FILE:
                    self._download_file(volume_item_path, local_item_path)
        except Exception as e:
            logger.debug(f"Directory sync error for {volume_dir}: {e}")
    
    def _download_file(self, volume_path: str, local_path: Path):
        """Download a single file from volume."""
        try:
            content = self.workspace_client.files.download(volume_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(content)
            logger.info(f"⬇️  Downloaded {volume_path}")
        except Exception as e:
            logger.debug(f"Download error for {volume_path}: {e}")
    
    def _upload_file(self, local_path: Path, volume_path: str):
        """Upload a single file to volume."""
        try:
            with open(local_path, 'rb') as f:
                content = f.read()
            self.workspace_client.files.upload(volume_path, content)
            logger.info(f"⬆️  Uploaded {local_path} → {volume_path}")
        except Exception as e:
            logger.debug(f"Upload error for {local_path}: {e}")
    
    def sync_loop(self):
        """Background sync loop."""
        while self.running:
            try:
                if DATABRICKS_SDK_AVAILABLE:
                    # Simple sync: upload any local files
                    for file_path in self.local_path.rglob('*'):
                        if file_path.is_file():
                            relative = file_path.relative_to(self.local_path)
                            volume_file = f"{self.volume_path}/{relative}"
                            # Only upload if file exists and is not too large
                            if file_path.stat().st_size < 10 * 1024 * 1024:  # 10MB limit
                                self._upload_file(file_path, volume_file)
                
                time.sleep(5)  # Sync every 5 seconds
            except Exception as e:
                logger.debug(f"Sync loop error: {e}")
                time.sleep(10)
    
    def start(self):
        """Start the background sync."""
        if self.running:
            return
        
        self.running = True
        self.sync_thread = threading.Thread(target=self.sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info("✅ Sync daemon started")
    
    def stop(self):
        """Stop the background sync."""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=2)


def copy_ui_assets():
    """Copy MLflow UI assets to the expected location."""
    logger.info("🎨 Copying MLflow UI assets...")
    
    try:
        import mlflow
        mlflow_path = Path(mlflow.__file__).parent
        build_path = mlflow_path / 'server' / 'js' / 'build'
        build_path.mkdir(parents=True, exist_ok=True)
        
        ui_assets_path = Path('mlflow-ui-assets')
        if ui_assets_path.exists():
            import shutil
            for item in ui_assets_path.glob('*'):
                dest = build_path / item.name
                if item.is_file():
                    shutil.copy2(item, dest)
                else:
                    shutil.copytree(item, dest, dirs_exist_ok=True)
            logger.info("✅ UI assets copied")
        else:
            logger.warning("⚠️  UI assets not found")
    except Exception as e:
        logger.warning(f"⚠️  UI asset copy failed: {e}")


def main():
    """Main entry point."""
    logger.info("=" * 50)
    logger.info("🚀 MLflow OSS with Volume Sync")
    logger.info("=" * 50)
    
    # Log environment
    logger.info(f"📍 Working directory: {os.getcwd()}")
    logger.info(f"🌐 DATABRICKS_HOST: {os.getenv('DATABRICKS_HOST', 'Not set')}")
    
    # Get paths from environment
    volume_tracking_uri = os.getenv('MLFLOW_TRACKING_URI', '')
    if volume_tracking_uri.startswith('sqlite:///'):
        volume_path = os.path.dirname(volume_tracking_uri.replace('sqlite:///', ''))
    else:
        volume_path = '/Volumes/rag/nst/mlflow-oss'
    
    local_path = '/tmp/mlflow-sync-data'
    
    logger.info(f"📂 Volume path: {volume_path}")
    logger.info(f"📂 Local path: {local_path}")
    
    # Initialize sync daemon if SDK is available
    sync_daemon = None
    if DATABRICKS_SDK_AVAILABLE:
        sync_daemon = SimpleVolumeSyncDaemon(local_path, volume_path)
        sync_daemon.sync_from_volume()  # Initial sync
        sync_daemon.start()  # Start background sync
    
    # Copy UI assets
    copy_ui_assets()
    
    # Configure MLflow paths
    Path(local_path).mkdir(parents=True, exist_ok=True)
    tracking_uri = f"sqlite:///{local_path}/mlflow-tracking.db"
    registry_uri = f"sqlite:///{local_path}/mlflow-registry.db"
    artifact_root = f"{local_path}/mlflow-artifacts"
    Path(artifact_root).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"📊 MLflow Configuration:")
    logger.info(f"   Tracking: {tracking_uri}")
    logger.info(f"   Registry: {registry_uri}")
    logger.info(f"   Artifacts: {artifact_root}")
    
    # Start MLflow server
    logger.info("🚀 Starting MLflow server...")
    cmd = [
        'mlflow', 'server',
        '--backend-store-uri', tracking_uri,
        '--registry-store-uri', registry_uri,
        '--default-artifact-root', artifact_root,
        '--host', '0.0.0.0',
        '--port', '8000'
    ]
    
    # Handle shutdown gracefully
    def handle_shutdown(signum, frame):
        logger.info("🛑 Shutting down...")
        if sync_daemon:
            sync_daemon.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    # Run MLflow server
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        handle_shutdown(None, None)
    except Exception as e:
        logger.error(f"❌ MLflow server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()