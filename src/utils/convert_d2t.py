import json
import os

def convert_d2t(data: dict):
    return json.dumps(data, ensure_ascii=False)