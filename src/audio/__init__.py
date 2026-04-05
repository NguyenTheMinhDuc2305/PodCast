from .elevenlab.model import ElevenLabsModel

def load_audio_model(model_name: str):
    if model_name == "elevenlabs":
        return ElevenLabsModel()
    else:
        raise ValueError(f"Unsupported audio model: {model_name}")