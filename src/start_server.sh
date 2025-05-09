#!/bin/bash

# 데이터베이스 초기화
rm -f rps_game.db

# 테이블 생성
python3 -c "from database.models import Base; from database.database import engine; Base.metadata.create_all(bind=engine)"

# 팀 멤버 데이터 초기화
python3 -c "from database.init_data import init_team_members; init_team_members()"

# 서버 시작
uvicorn main:app --reload 