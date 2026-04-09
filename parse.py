import os
FOLDER = "save_8_4_2026/script/"
import json
import pandas as pd
df = pd.DataFrame(columns = [
    "id_hs",
    "intro",
    "highlight",
    "improve",
    "solution",
    "conclusion"
])
for file in os.listdir(FOLDER):
    id_hs = file.split("_")[0]
    with open(os.path.join(FOLDER, file), "r", encoding="utf-8") as f:
        data = json.load(f)["result"]
    df.loc[len(df)] = {
        "id_hs": id_hs,
        "intro": data["intro"],
        "highlight": data["highlight"],
        "improve": data["improve"],
        "solution": data["solution"],
        "conclusion": data["conclusion"],
    }
df.to_csv("result_8_4_2026.csv", index=False, encoding="utf-8-sig")