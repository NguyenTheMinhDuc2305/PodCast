from .gemini.model import GeminiModel

def load_text_model(name):
    if name == "gemini":
        return GeminiModel()
    else:        
        raise ValueError(f"Unsupported model name: {name}")