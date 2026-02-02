"""Transcription module supporting multiple STT models."""

import os
import logging
from typing import Optional

log = logging.getLogger('whisperapp.transcribe')

# Lazy-loaded model instances
_parakeet_model = None
_current_model_key: Optional[str] = None


def _load_parakeet(model_id: str):
    """Load Parakeet model."""
    global _parakeet_model
    
    try:
        from parakeet_mlx import from_pretrained
        log.info(f"Loading Parakeet model: {model_id}")
        _parakeet_model = from_pretrained(model_id)
        log.info("✓ Parakeet model loaded")
        return _parakeet_model
    except ImportError:
        raise ImportError("parakeet-mlx not installed. Run: pip install parakeet-mlx")


def transcribe(audio_path: str, model_key: str = "parakeet") -> str:
    """
    Transcribe audio file using the specified model.
    
    Args:
        audio_path: Path to WAV audio file
        model_key: Which model to use (parakeet, whisper-large, whisper-small, distil-whisper)
        
    Returns:
        Transcribed text string
    """
    global _parakeet_model, _current_model_key
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Get model info
    from .models import AVAILABLE_MODELS, DEFAULT_MODEL
    model_info = AVAILABLE_MODELS.get(model_key, AVAILABLE_MODELS[DEFAULT_MODEL])
    
    log.debug(f"Transcribing with {model_info.name}: {audio_path}")
    
    if model_info.model_type == "parakeet":
        # Use Parakeet
        if _parakeet_model is None or _current_model_key != model_key:
            _parakeet_model = _load_parakeet(model_info.model_id)
            _current_model_key = model_key
        
        result = _parakeet_model.transcribe(audio_path)
        
        # Handle result format
        if hasattr(result, 'text'):
            text = result.text
        elif isinstance(result, str):
            text = result
        elif isinstance(result, dict):
            text = result.get("text", "")
        else:
            text = str(result)
            
    else:
        # Use Whisper (mlx-whisper)
        try:
            import mlx_whisper
        except ImportError:
            raise ImportError("mlx-whisper not installed. Run: pip install mlx-whisper")
        
        log.info(f"Transcribing with Whisper model: {model_info.model_id}")
        
        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=model_info.model_id,
            language="en",  # Force English for speed
            fp16=True,
            verbose=False
        )
        
        text = result.get("text", "") if isinstance(result, dict) else str(result)
    
    log.debug(f"Transcription result: '{text}'")
    return text.strip()


def transcribe_with_timing(audio_path: str, model_key: str = "parakeet") -> dict:
    """
    Transcribe audio and return timing information.
    
    Returns:
        dict with 'text', 'transcription_time', and 'word_count' keys
    """
    import time
    
    start_time = time.time()
    text = transcribe(audio_path, model_key=model_key)
    duration = time.time() - start_time
    
    return {
        "text": text,
        "transcription_time": duration,
        "word_count": len(text.split()) if text else 0
    }
