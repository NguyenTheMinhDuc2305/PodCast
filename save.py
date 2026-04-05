from src.utils.query import get_highlight, get_content, get_improve, get_name, get_teacher
from dotenv import load_dotenv
import os
from src.utils.convert_d2t import convert_d2t
from src.db.database import Database
load_dotenv()
from src.text.gemini__model import GeminiModel
from config import load_config
import pandas as pd
from tqdm import tqdm
PATH = "DS 50 hs podcast - DS 50 HS.csv"
PATH_RESULT = "DS 50 hs podcast - DS 50 HS - RESULT.csv"
date = 202601
if __name__ == "__main__":
    df = pd.read_csv(PATH)
    config = load_config("config.yaml")
    gemini_model = GeminiModel(config)
    for index, row in tqdm(df.iterrows(), total=len(df)):
        student_id = row["STUDENT_ID"]
        highlight = convert_d2t(get_highlight(student_id, date))
        content = convert_d2t(get_content(student_id, date))
        improve = convert_d2t(get_improve(student_id, date))
        name = get_name(student_id, date)[0]["full_name"]
        teacher = get_teacher(student_id)[0]["care_specialist_fullname"]
        month = date
        result = gemini_model.generate_text({
            "highlight": highlight,
            "others": content,
            "improve": improve,
            "month": month,
            "name": name,
            "teacher": teacher,
        })
        # Cập nhật trực tiếp vào df (row từ iterrows() là bản sao, không cập nhật df)
        df.at[index, "intro"] = result["intro"]
        df.at[index, "highlight"] = result["highlight"]
        df.at[index, "improve"] = result["improve"]
        df.at[index, "solution"] = result["solution"]
        df.at[index, "conclusion"] = result["conclusion"]

    df.to_csv(PATH_RESULT, index=False, encoding="utf-8-sig")
    print(f"Đã lưu kết quả vào {PATH_RESULT}")