"""
Script untuk membuat tabel project_overhead_kasbon_mandor di database yang sudah ada.
Jalankan script ini jika tabel kasbon mandor belum ada.
"""

import sys
from app import create_app, db

app = create_app('development')


def create_kasbon_mandor_table():
    """Membuat tabel project_overhead_kasbon_mandor."""
    with app.app_context():
        try:
            db.create_all()

            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            if 'project_overhead_kasbon_mandor' not in tables:
                print('❌ Tabel project_overhead_kasbon_mandor tidak ditemukan')
                return False

            print('✅ Tabel project_overhead_kasbon_mandor berhasil dibuat atau sudah ada!')
            columns = inspector.get_columns('project_overhead_kasbon_mandor')
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
    print('Creating kasbon mandor table...')
    success = create_kasbon_mandor_table()
    if success:
        print('\n✅ Kasbon mandor table ready!')
    sys.exit(0 if success else 1)
