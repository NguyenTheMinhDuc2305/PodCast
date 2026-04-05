from google import genai
import os
import json
from google.genai import types
from src.text.text_model import TextModel
from src.text.structure import OutputStructure
from src.text.gemini.prompt import TEXT_PROMPT
from google.protobuf.json_format import MessageToDict

class GeminiModel(TextModel):
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    def generate_script(self, params: dict) -> str:
        prompt = TEXT_PROMPT.format(
                                highlight=params["highlight"], 
                                improve=params["improve"], 
                                others=params["others"], 
                                month=params["month"], 
                                name=params["name"], 
                                teacher=params["teacher"]
        )

        generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema= OutputStructure
        )

        response = self.client.models.generate_content(
            model = os.getenv("GEMINI_MODEL_NAME"),
            contents = prompt,
            config = generation_config
        )
        # print(response.usage_metadata)
        usage_dict = {
                "prompt_token_count": getattr(response.usage_metadata, "prompt_token_count", 0),
                "candidates_token_count": getattr(response.usage_metadata, "candidates_token_count", 0),
                
                # Thêm dòng này để lấy Thinking Tokens an toàn
                "thoughts_token_count": getattr(response.usage_metadata, "thoughts_token_count", 0),
                
                "total_token_count": getattr(response.usage_metadata, "total_token_count", 0)
            }

        # Lưu dữ liệu vào file JSONL
        with open("response_usage.jsonl", "a", encoding="utf-8") as f:
            json.dump(usage_dict, f)
            f.write("\n")
        return json.loads(response.text)
