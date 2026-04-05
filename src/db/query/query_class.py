import pymongo
from typing import Dict, Any, Optional
from src.db.database import Database


def get_student_class(db: Optional[Database], params: Dict[str, Any]):
    sql_params = {
        "student_id": params["lms_student_id"],
    }

    where_clause = "WHERE student_id = :student_id"

    query = f"""
        SELECT grade, level
        FROM raw_tutor.tutor_student_info
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
        results[0]["grade"] = results[0]["grade"].split("_")[1]
        return results
    except Exception as e:
        print(f"Lỗi khi thực thi query: {e}")
        raise
    finally:
        if should_close:
            db.close()