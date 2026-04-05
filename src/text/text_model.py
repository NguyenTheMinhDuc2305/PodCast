from abc import ABC, abstractmethod

class TextModel(ABC):
    @abstractmethod
    def generate_script(self, params: dict):
        pass
    