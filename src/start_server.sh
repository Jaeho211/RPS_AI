#!/bin/bash

# 테이블 생성
python3 -c "from database.models import Base; from database.database import engine; Base.metadata.create_all(bind=engine)"

# 서버 시작
uvicorn main:app --reload 