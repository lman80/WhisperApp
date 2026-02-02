"""Audio recording module for capturing microphone input."""

import tempfile
import threading
from typing import Optional, Callable

import numpy as np


class AudioRecorder:
    """
    Records audio from the microphone.
    
    Usage:
        recorder = AudioRecorder()
        recorder.start()
        # ... user speaks ...
        wav_path = recorder.stop()  # Returns path to WAV file
    """
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        """
        Initialize the audio recorder.
        
        Args:
            sample_rate: Audio sample rate in Hz (16000 recommended for Whisper/Parakeet)
            channels: Number of audio channels (1 for mono)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.frames: list = []
        self.stream = None
        self.recording = False
        self._lock = threading.Lock()
        self._start_time: Optional[float] = None
        self.level_callback: Optional[callable] = None  # Callback for audio level
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream - stores audio frames."""
        if status:
            print(f"Audio status: {status}")
        
        with self._lock:
            if self.recording:
                self.frames.append(indata.copy())
                
                # Calculate and emit audio level for visualizer
                if self.level_callback:
                    import numpy as np
                    rms = np.sqrt(np.mean(indata**2))
                    self.level_callback(rms)
    
    def start(self) -> None:
        """Start recording audio from the microphone."""
        import sounddevice as sd
        import time
        
        with self._lock:
            self.frames = []
            self.recording = True
            self._start_time = time.time()
        
        # Find a real microphone (avoid virtual devices like BlackHole)
        device = self._find_real_microphone()
        
        self.stream = sd.InputStream(
            device=device,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='float32',
            callback=self._audio_callback
        )
        self.stream.start()
    
    def _find_real_microphone(self):
        """Find a real microphone device, avoiding virtual audio devices."""
        import sounddevice as sd
        
        # Virtual audio devices to avoid
        virtual_devices = ['blackhole', 'soundflower', 'loopback', 'virtual']
        
        devices = sd.query_devices()
        candidates = []
        
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                name_lower = d['name'].lower()
                is_virtual = any(v in name_lower for v in virtual_devices)
                if not is_virtual:
                    candidates.append((i, d['name']))
        
        if candidates:
            # Prefer MacBook built-in mic for reliability
            for idx, name in candidates:
                if 'macbook' in name.lower():
                    return idx
            # Fall back to first real mic
            return candidates[0][0]
        
        # No real mic found, use default
        return None
    
    def stop(self) -> str:
        """
        Stop recording and save audio to a WAV file.
        
        Returns:
            Path to the saved WAV file
        """
        import time
        from scipy.io import wavfile
        
        with self._lock:
            self.recording = False
            duration = time.time() - self._start_time if self._start_time else 0
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # Concatenate all recorded frames
        if not self.frames:
            raise RuntimeError("No audio was recorded")
        
        audio_data = np.concatenate(self.frames, axis=0)
        
        # Convert float32 to int16 for WAV file
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Save to temporary WAV file
        wav_path = tempfile.mktemp(suffix=".wav")
        wavfile.write(wav_path, self.sample_rate, audio_int16)
        
        # Store duration for statistics
        self._last_duration = duration
        
        return wav_path
    
    @property
    def last_duration(self) -> float:
        """Duration of the last recording in seconds."""
        return getattr(self, '_last_duration', 0.0)
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self.recording


def list_audio_devices():
    """List available audio input devices."""
    import sounddevice as sd
    
    devices = sd.query_devices()
    input_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append({
                'index': i,
                'name': device['name'],
                'channels': device['max_input_channels'],
                'sample_rate': device['default_samplerate']
            })
    
    return input_devices
