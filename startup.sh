#!/bin/bash
cd /home/site/wwwroot
export PYTHONPATH=/home/site/wwwroot:$PYTHONPATH
cd api
python main.py
