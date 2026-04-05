import pymongo
from typing import Dict, Any, Optional
from src.db.database import Database
def get_student_name(db: Optional[Database], params: Dict[str, Any]):

    sql_params = {
        "student_id": params["lms_student_id"],
        # "month_of_report": params["month_of_report"],
    }

    where_clause = "WHERE student_id = :student_id"

    query = f"""
        SELECT FULL_NAME
        FROM raw_tutor.TUTOR_STUDENT_INFO
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
