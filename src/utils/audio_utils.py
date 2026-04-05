import librosa
import soundfile as sf
import os

def increase_speed(input_path, output_path, speed=1.5):
    y, sr = librosa.load(input_path, sr=None)
    y_fast = librosa.effects.time_stretch(y, rate=speed)

    # force wav output
    output_path = os.path.splitext(output_path)[0] + ".wav"

    sf.write(output_path, y_fast, sr)
    return output_path