import os
from lib.yaml_config import load_config


config = {}

if os.getenv('APP_CONFIG'):
    config = load_config(os.getenv('APP_CONFIG'))
else:
    print('APP_CONFIG not set...')
    exit(1)
