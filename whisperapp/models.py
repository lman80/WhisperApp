"""
Model registry and management for WhisperApp.
Supports multiple STT models with download tracking.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Callable
from dataclasses import dataclass

log = logging.getLogger(__name__)

# Model cache directory (uses HuggingFace cache)
CACHE_DIR = Path.home() / ".cache" / "huggingface" / "hub"


@dataclass
class ModelInfo:
    """Information about an available model."""
    key: str
    name: str
    model_id: str
    model_type: str  # "parakeet" or "whisper"
    size: str
    speed: str
    description: str


# Available models registry
AVAILABLE_MODELS: Dict[str, ModelInfo] = {
    "parakeet": ModelInfo(
        key="parakeet",
        name="Parakeet TDT 0.6B",
        model_id="mlx-community/parakeet-tdt-0.6b-v2",
        model_type="parakeet",
        size="~2.5GB",
        speed="Fastest",
        description="NVIDIA's fast dictation model"
    ),
    "whisper-large": ModelInfo(
        key="whisper-large",
        name="Whisper Large v3",
        model_id="mlx-community/whisper-large-v3-mlx",
        model_type="whisper",
        size="~3GB",
        speed="Slow",
        description="Best accuracy, slower"
    ),
    "whisper-small": ModelInfo(
        key="whisper-small",
        name="Whisper Small",
        model_id="mlx-community/whisper-small-mlx",
        model_type="whisper",
        size="~500MB",
        speed="Fast",
        description="Light and fast"
    ),
    "distil-whisper": ModelInfo(
        key="distil-whisper",
        name="Distil-Whisper Large",
        model_id="mlx-community/distil-whisper-large-v3",
        model_type="whisper",
        size="~1.5GB",
        speed="Fast",
        description="Fast with great accuracy"
    ),
}

# Default model
DEFAULT_MODEL = "parakeet"


def get_model_info(model_key: str) -> Optional[ModelInfo]:
    """Get info for a specific model."""
    return AVAILABLE_MODELS.get(model_key)


def list_models() -> list[ModelInfo]:
    """List all available models."""
    return list(AVAILABLE_MODELS.values())


def is_model_downloaded(model_key: str) -> bool:
    """Check if a model is already downloaded."""
    model = AVAILABLE_MODELS.get(model_key)
    if not model:
        return False
    
    # Convert model_id to cache directory name
    # HuggingFace uses format: models--org--name
    cache_name = "models--" + model.model_id.replace("/", "--")
    model_path = CACHE_DIR / cache_name
    
    # Check if snapshots exist (indicates download)
    snapshots_path = model_path / "snapshots"
    if snapshots_path.exists():
        # Check if any snapshot has actual files
        for snapshot in snapshots_path.iterdir():
            if any(snapshot.iterdir()):
                return True
    
    return False


def download_model(model_key: str, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
    """
    Download a model if not already present.
    
    Args:
        model_key: Key of the model to download
        progress_callback: Optional callback for progress updates
        
    Returns:
        True if successful, False otherwise
    """
    model = AVAILABLE_MODELS.get(model_key)
    if not model:
        log.error(f"Unknown model: {model_key}")
        return False
    
    if is_model_downloaded(model_key):
        log.info(f"Model already downloaded: {model.name}")
        return True
    
    try:
        if progress_callback:
            progress_callback(f"Downloading {model.name} ({model.size})...")
        
        log.info(f"Downloading model: {model.name} ({model.model_id})")
        
        if model.model_type == "parakeet":
            from parakeet_mlx import from_pretrained
            from_pretrained(model.model_id)
        else:  # whisper
            import mlx_whisper
            # Just load the model to trigger download
            mlx_whisper.transcribe("", path_or_hf_repo=model.model_id)
        
        log.info(f"✓ Model downloaded: {model.name}")
        return True
        
    except Exception as e:
        log.error(f"Failed to download {model.name}: {e}")
        return False


def get_downloaded_models() -> list[str]:
    """Get list of model keys that are downloaded."""
    return [key for key in AVAILABLE_MODELS if is_model_downloaded(key)]
