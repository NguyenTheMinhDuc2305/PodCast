import pymongo
from typing import Dict, Any, Optional
from src.db.database import Database
def get_teacher_name(db: Optional[Database], params: Dict[str, Any]):

    sql_params = {
        "student_id": params["lms_student_id"],
        # "month_of_report": params["month_of_report"],
    }

    where_clause = "WHERE student_id = :student_id"

    query = f"""
        SELECT 
            concat_ws(' ', b.firstname, b.middlename, b.lastname) AS care_specialist_fullname
        FROM raw_tutor.tutor_student_info a
        LEFT JOIN raw_tutor.mdl_user b ON a.care_specialist_id = b.id::text
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
