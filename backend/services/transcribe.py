## services/transcribe.py

import os
from typing import Tuple
from faster_whisper import WhisperModel

# Choose a Whisper size. 'medium' is strong on Finnish; use 'small' for CPU-only.
MODEL_SIZE = os.getenv('WHISPER_MODEL_SIZE', 'medium')
DEVICE = os.getenv('WHISPER_DEVICE', 'auto')  # 'cuda' | 'cpu' | 'auto'

_model = None

def _get_model():
    global _model
    if _model is None:
        compute_type = 'float16' if DEVICE in ('cuda', 'auto') else 'int8'
        _model = WhisperModel(MODEL_SIZE, device=DEVICE if DEVICE != 'auto' else 'cuda' if os.getenv('CUDA_VISIBLE_DEVICES') else 'cpu', compute_type=compute_type)
    return _model


def transcribe_audio(file_path: str, language_hint: str = None) -> Tuple[str, float]:
    """Return (text, avg_prob)."""
    model = _get_model()
    segments, info = model.transcribe(file_path, language=language_hint, vad_filter=True)
    text = " ".join([seg.text.strip() for seg in segments])
    return text.strip(), getattr(info, 'language_probability', 0.0)
