from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ...core import AppSettings

engine = create_engine(AppSettings.DB.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True,pool_size=32, max_overflow=64,connect_args={"application_name":"dev_auth_api"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine,expire_on_commit=False)

class SessionManager:
    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()