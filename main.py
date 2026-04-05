from src.core import make_podcast
from dotenv import load_dotenv
import os
load_dotenv()
if __name__ == "__main__":
    student_id = 1092392
    month = 202601
    make_podcast(student_id, month)