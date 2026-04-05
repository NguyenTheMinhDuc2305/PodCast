from json import load
import os
from config import load_config
from src.db.database import Database
from src.db.query.query_highlight import get_student_highlight
from src.db.query.query_content import get_student_content
from src.db.query.query_improve import get_student_improve
from src.db.query.query_name import get_student_name
from src.db.query.query_teacher import get_teacher_name
from dotenv import load_dotenv
from src.db.query.query_class import get_student_class
load_dotenv(".env")
# cfg = load_config("")
db = Database(overrides={
    "host": os.getenv("CDP_HOST"),
    "port": os.getenv("CDP_PORT"),
    "database": os.getenv("CDP_NAME"),
    "user": os.getenv("CDP_USER"),
    "password": os.getenv("CDP_PASSWORD"),
    "schema": os.getenv("CDP_SCHEMA")
    
})

def get_highlight(lms_student_id: int, month_of_report: int):
    return get_student_highlight(db, {
        "lms_student_id": lms_student_id,
        "month_of_report": month_of_report
    })

def get_content(lms_student_id: int, month_of_report: int):
    return get_student_content(db, {
        "lms_student_id": lms_student_id,
        "month_of_report": month_of_report
    })

def get_improve(lms_student_id: int, month_of_report: int):
    return get_student_improve(db, {
        "lms_student_id": lms_student_id,
        "month_of_report": month_of_report
    })


def get_name(lms_student_id: int, month_of_report: int):
    return get_student_name(db, {
        "lms_student_id": lms_student_id,
        "month_of_report": month_of_report
    })

def get_teacher(lms_student_id: int):
    return get_teacher_name(db, {
        "lms_student_id": lms_student_id,
        # "month_of_report": month_of_report
    })

def get_class(lms_student_id: int, month_of_report: int):
    # from src.db.query.query_class import get_student_class
    return get_student_class(db, {
        "lms_student_id": lms_student_id,
    })