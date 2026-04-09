import os
import pandas as pd
import json

FOLDER = r"E:\WORK\PodCast\save\script"
CSV_PATH = "run_7_4.csv"
MONTH_SUFFIX = "202603"

df = pd.read_csv(CSV_PATH)

required_columns = {
    "id_hs",
    "intro",
    "highlight",
    "improve",
    "Solution",
    "conclusion",
}
missing_columns = required_columns - set(df.columns)
if missing_columns:
    raise ValueError(f"Thiếu cột trong CSV: {sorted(missing_columns)}")

os.makedirs(FOLDER, exist_ok=True)

updated = 0
skipped = 0

for row in df.to_dict(orient="records"):
    student_id = row["id_hs"]
    json_path = os.path.join(FOLDER, f"{student_id}_{MONTH_SUFFIX}.json")

    if not os.path.exists(json_path):
        skipped += 1
        continue

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["result"] = {
        "intro": row["intro"],
        "highlight": row["highlight"],
        "improve": row["improve"],
        "solution": row["Solution"],
        "conclusion": row["conclusion"],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    updated += 1

print(f"Đã cập nhật: {updated} file. Bỏ qua (không thấy json): {skipped} file.")