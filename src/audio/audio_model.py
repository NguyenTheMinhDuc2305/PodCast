from abc import ABC, abstractmethod

class AudioModel(ABC):
    @abstractmethod
    def generate_audio(self, script: str, output_path: str):
        pass