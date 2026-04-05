from elevenlabs import ElevenLabs
import os
from src.audio.audio_model import AudioModel
class ElevenLabsModel(AudioModel):
    def __init__(self):
        self.client = ElevenLabs(api_key = os.getenv("ELEVEN_LABS_API_KEY"))
    
    def generate_audio(self, script, output_path):
        # print(os.getenv("ELEVEN_LABS_VOICE_ID"))
        audio = self.client.text_to_speech.convert(
                                            text = script, 
                                            voice_id=os.getenv("ELEVEN_LABS_VOICE_ID"),
                                            model_id="eleven_v3",
                                            output_format="mp3_44100_128",
                                           )
        with open(output_path, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)