from pydantic import BaseModel

class OutputStructure(BaseModel):
    intro: str
    highlight: str
    improve: str
    solution: str
    conclusion: str