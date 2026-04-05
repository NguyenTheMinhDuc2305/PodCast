from typing import Any, Dict, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

class Database:
    def __init__(self, overrides: Optional[Dict[str, Any]] = None):
        self.engine: Optional[Engine] = None
        self.overrides = overrides
        self.schema = self.overrides.get("schema")
        self.connect()

    def _build_connection_params(self) -> Dict[str, Any]:
        """Tạo dict tham số kết nối từ ENV và overrides."""
        required_keys = {
            "host": "DB_HOST",
            "port": "DB_PORT",
            "database": "DB_NAME",
            "user": "DB_USER",
            "password": "DB_PASSWORD",
        }
        params: Dict[str, Any] = {}
        missing = []

        for key, env_name in required_keys.items():
            value = self.overrides.get(key)
            if value:
                params[key] = value
            else:
                missing.append(env_name)

        if missing:
            raise ValueError(
                "Thiếu thông tin cấu hình DB trong biến môi trường: "
                + ", ".join(missing)
            )

        return params

    def _build_connection_url(self) -> str:
        """Tạo connection string PostgreSQL cho SQLAlchemy."""
        params = self._build_connection_params()
        return (
            "postgresql+psycopg2://"
            f"{params['user']}:{params['password']}"
            f"@{params['host']}:{params['port']}/{params['database']}"
        )

    def connect(self) -> None:
        """Thiết lập SQLAlchemy engine."""
        try:
            url = self._build_connection_url()
            connect_args = {}
            if self.schema:
                connect_args["options"] = f"-c search_path={self.schema}"

            self.engine = create_engine(
                url, pool_pre_ping=True, future=True, connect_args=connect_args
            )
            print("Kết nối database thành công!")
        except SQLAlchemyError as exc:
            print(f"Lỗi kết nối database: {exc}")
            raise

    def execute_query(
        self, query: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> list[Dict[str, Any]]:
        """
        Thực thi query và trả về kết quả.

        Args:
            query: Câu lệnh SQL
            params: Tham số cho query (nếu có)

        Returns:
            List các dict chứa kết quả
        """
        if not self.engine:
            raise RuntimeError("SQLAlchemy engine chưa được khởi tạo.")

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as exc:
            print(f"Lỗi thực thi query: {exc}")
            raise

    def get_all_tables(self):
        """
        Lấy danh sách tất cả các bảng trong database.

        Returns:
            List tên các bảng
        """
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """
        results = self.execute_query(query)
        return [row["table_name"] for row in results]

    def get_table_data(self, table_name: str, limit: int = None):
        """
        Lấy dữ liệu từ một bảng.

        Args:
            table_name: Tên bảng
            limit: Giới hạn số dòng (nếu có)

        Returns:
            List các dict chứa dữ liệu
        """
        query = f"SELECT * FROM {table_name}"
        params = None
        if limit:
            query += " LIMIT :limit"
            params = {"limit": limit}
        return self.execute_query(query, params)

    def close(self):
        """Đóng kết nối database."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            print("Đã đóng kết nối database.")