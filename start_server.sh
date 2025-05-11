#!/bin/bash

# Use default port 8000 if PORT environment variable is not set
PORT=${PORT:-8000}

# Change directory to src
cd src

# 서버 시작
uvicorn main:app --host 0.0.0.0 --port $PORT