"""
Script untuk membuat tabel project_jasa_slip di database yang sudah ada.
Jalankan script ini jika tabel slip gaji jasa belum ada.
"""

import sys
from app import create_app, db

app = create_app('development')


def create_jasa_slip_table():
    """Membuat tabel project_jasa_slip."""
    with app.app_context():
        try:
            db.create_all()

            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            if 'project_jasa_slip' not in tables:
                print('❌ Tabel project_jasa_slip tidak ditemukan')
                return False

            print('✅ Tabel project_jasa_slip berhasil dibuat atau sudah ada!')
            columns = inspector.get_columns('project_jasa_slip')
            print(f'   Jumlah kolom: {len(columns)}')
            for col in columns:
                print(f"   - {col['name']} ({col['type']})")

        except Exception as e:
            print(f'❌ Error: {e}')
            import traceback
            traceback.print_exc()
            return False

    return True


if __name__ == '__main__':
    print('Creating jasa slip table...')
    success = create_jasa_slip_table()
    if success:
        print('\n✅ Jasa slip table ready!')
    sys.exit(0 if success else 1)
