#!/bin/bash

# Use default port 8000 if PORT environment variable is not set
PORT=${PORT:-8000}

# Change directory to src
cd src

# 테이블 생성
python3 -c "from database.models import Base; from database.database import engine; Base.metadata.create_all(bind=engine)"

# 서버 시작
uvicorn main:app --host 0.0.0.0 --port $PORT