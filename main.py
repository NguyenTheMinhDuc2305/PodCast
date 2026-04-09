from src.core import make_podcast
from dotenv import load_dotenv
import os
from src.core import generate_script
import json
import pandas as pd
from tqdm import tqdm
FOLDER = "save_8_4_2026/script/"
os.makedirs(FOLDER, exist_ok=True)
load_dotenv()
df = pd.read_csv("AI team - Podcast - Gen_kich_ban_8_4.csv")
id_hs = list(df["ID học sinh"])
month = 202603
for student_id in tqdm(id_hs, total=len(id_hs)):
    result, highlight, improve_list = generate_script(student_id, month)
    raw = {
        "result": result,
        "highlight": highlight,
        "improve_list": improve_list
        }
    with open(os.path.join(FOLDER, f"{student_id}_{month}.json"), "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=4)