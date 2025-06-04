#!/bin/bash

# Use default port 8000 if PORT environment variable is not set
PORT=${PORT:-8000}

cd src && gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
