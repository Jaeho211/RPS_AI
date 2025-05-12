from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# 환경 변수에서 데이터베이스 URL을 가져오거나, 없으면 SQLite를 사용
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rps_game.db")
print(f"DATABASE_URL loaded: {DATABASE_URL}")

# Render의 PostgreSQL URL 형식 수정
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 