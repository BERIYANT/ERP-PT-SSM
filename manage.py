#!/usr/bin/env python3
import os, sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
if load_dotenv:
    load_dotenv(BASE_DIR / '.env')
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','ssm.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
