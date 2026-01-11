"""Download ML models from GitHub releases for deployment."""

import logging
import os
import sys
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Model files to download
REQUIRED_MODELS = [
    "final_no_age_model.pkl",
    "final_no_age_scaler.pkl",
    "final_no_age_imputer.pkl",
    "improved_pattern_cnn_model_retrained.h5",
    "blood_type_triplet_embedding.h5",
    "blood_support_embeddings.npz",
]


def download_file(url: str, destination: Path, timeout: int = 120) -> bool:
    """Download a file from URL to destination path."""
    try:
        logger.info(f"Downloading {destination.name}...")
        response = requests.get(url, stream=True, timeout=timeout)
        
        if response.status_code == 404:
            logger.error(f"File not found (404): {url}")
            return False
        
        response.raise_for_status()
        
        # Get file size if available
        total_size = int(response.headers.get('content-length', 0))
        size_mb = total_size / (1024 * 1024) if total_size else 0
        
        if size_mb > 0:
            logger.info(f"  Size: {size_mb:.2f} MB")
        
        # Create parent directory if needed
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Download with progress
        downloaded = 0
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        
        logger.info(f"  ✓ Downloaded successfully ({downloaded / (1024 * 1024):.2f} MB)")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"  ✗ Download failed: {e}")
        return False


def download_models_from_github():
    """Download all required models from GitHub releases."""
    # Get GitHub info from environment or use defaults
    github_repo = os.getenv("GITHUB_REPO", "miahangelo/thesis-project-be")
    github_tag = os.getenv("MODELS_RELEASE_TAG", "models-v1.0")
    
    # Base directory (same as in ml_service.py)
    base_dir = Path(__file__).parent.parent / "shared-models"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading models from GitHub: {github_repo} @ {github_tag}")
    logger.info(f"Target directory: {base_dir}")
    
    success_count = 0
    failed_models = []
    
    for model_file in REQUIRED_MODELS:
        destination = base_dir / model_file
        
        # Skip if already exists and has content
        if destination.exists() and destination.stat().st_size > 0:
            logger.info(f"✓ {model_file} already exists (skipping)")
            success_count += 1
            continue
        
        # Construct GitHub release download URL
        url = f"https://github.com/{github_repo}/releases/download/{github_tag}/{model_file}"
        
        if download_file(url, destination):
            success_count += 1
        else:
            failed_models.append(model_file)
    
    logger.info(f"\nDownload Summary: {success_count}/{len(REQUIRED_MODELS)} successful")
    
    if failed_models:
        logger.error(f"Failed to download: {', '.join(failed_models)}")
        logger.error("\nPlease ensure:")
        logger.error(f"1. GitHub repository '{github_repo}' is accessible")
        logger.error(f"2. Release tag '{github_tag}' exists")
        logger.error(f"3. All model files are uploaded to the release")
        return False
    
    logger.info("✓ All models downloaded successfully!")
    return True


if __name__ == "__main__":
    success = download_models_from_github()
    sys.exit(0 if success else 1)
