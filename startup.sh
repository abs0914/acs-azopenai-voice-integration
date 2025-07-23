#!/bin/bash
cd /home/site/wwwroot
export PYTHONPATH=/home/site/wwwroot:$PYTHONPATH
cd api
gunicorn --bind 0.0.0.0:8000 --workers 1 --timeout 600 main:app
