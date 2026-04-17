#!/usr/bin/env python3
"""
SSM Portal - Skrip jalankan aplikasi Flask
Gunakan: python run.py
"""
import os
import sys
from pathlib import Path


def _use_project_venv_python():
    project_root = Path(__file__).resolve().parent
    current_python = Path(sys.executable).absolute()

    if os.name == 'nt':
        candidates = [
            project_root / '.venv_local' / 'Scripts' / 'python.exe',
            project_root / '.venv' / 'Scripts' / 'python.exe',
        ]
    else:
        candidates = [
            project_root / '.venv_local' / 'bin' / 'python3',
            project_root / '.venv_local' / 'bin' / 'python',
            project_root / '.venv' / 'bin' / 'python3',
            project_root / '.venv' / 'bin' / 'python',
        ]

    for python_path in candidates:
        if not python_path.exists():
            continue
        if current_python == python_path.absolute():
            return
        os.execv(str(python_path), [str(python_path), str(Path(__file__).resolve()), *sys.argv[1:]])


_use_project_venv_python()

from app import create_app, init_db

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'development'
    port = int(os.environ.get('PORT', 5000))

    if mode == 'init-db':
        # python run.py init-db  → buat tabel dan seed admin default
        app = create_app('development')
        init_db(app)
    else:
        app = create_app(mode)
        print('=' * 50)
        print('  SSM PORTAL - PT. Satria Sakti Mandiri')
        print('=' * 50)
        print(f'  Mode    : {mode}')
        print(f'  URL     : http://localhost:{port}')
        print(f'  API     : http://localhost:{port}/api/')
        print('=' * 50)
        app.run(host='0.0.0.0', port=port, debug=(mode == 'development'))
