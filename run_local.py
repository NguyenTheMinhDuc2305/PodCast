from src.core import make_podcast, check_add_music
from dotenv import load_dotenv
import os
import pandas as pd
from tqdm import tqdm
load_dotenv()

if __name__ == "__main__":
    PATH = "DS 50 hs podcast - DS 50 HS.csv"
    df = pd.read_csv(PATH)
    month = 202602
    for index, row in tqdm(df.iterrows(), total=len(df)):
        student_id = row["STUDENT_ID"]
        make_podcast(student_id, month)
        break

# if __name__ == "__main__":
#     video_path = "E:/WORK/PodCast/outputs/videos/1092392_202602.mp4"
#     music_path = "E:/WORK/PodCast/inputs/music/background.mp3"
#     output_path = "test.mp4"
#     check_add_music(video_path, music_path, output_path)