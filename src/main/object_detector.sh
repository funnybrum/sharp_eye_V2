# !/bin/bash
cd /sharp_eye
APP_CONFIG=./resources/object_detector.yaml YOLO_CONFIG_DIR=/tmp/Ultralytics python3 object_detector.py
