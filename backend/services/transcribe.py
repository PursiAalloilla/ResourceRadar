import os
from faster_whisper import WhisperModel

MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")
DEVICE = os.getenv("WHISPER_DEVICE", "auto")

_model = None

def _get_model():
    global _model
    if _model is not None:
        return _model

    # Determine compute type safely
    if DEVICE == "auto":
        if os.getenv("CUDA_VISIBLE_DEVICES"):
            device = "cuda"
            compute_type = "float16"
        else:
            device = "cpu"
            compute_type = "int8"  # safe fallback for CPU
    else:
        device = DEVICE
        compute_type = "float16" if device == "cuda" else "int8"

    print(f"[transcribe] Loading Whisper model ({MODEL_SIZE}) on {device} [{compute_type}]")

    _model = WhisperModel(
        MODEL_SIZE,
        device=device,
        compute_type=compute_type
    )
    return _model


def transcribe_audio(audio_path: str):
    """Transcribe a WAV or audio file to text."""
    model = _get_model()
    segments, info = model.transcribe(audio_path, beam_size=5)
    text = " ".join([seg.text for seg in segments])
    return text.strip(), info
