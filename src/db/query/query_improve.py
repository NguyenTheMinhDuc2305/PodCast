import pymongo
from typing import Dict, Any, Optional
from src.db.database import Database


def get_student_improve(db: Optional[Database], params: Dict[str, Any]):
    sql_params = {
        "lms_student_id": params["lms_student_id"],
        "month_of_report": params["month_of_report"],
    }

    where_clause = "WHERE lms_student_id = :lms_student_id AND month_of_report = :month_of_report"

    query = f"""
        SELECT improvement
        FROM raw_tutor.student_monthly_highlight
        {where_clause}
    """
    should_close = False

    if db is None:
        db = Database()
        should_close = True

    try:
        results = db.execute_query(query, sql_params)
        if not results:
            return None
        return results
    except Exception as e:
        print(f"Lỗi khi thực thi query: {e}")
        raise
    finally:
        if should_close:
            db.close()