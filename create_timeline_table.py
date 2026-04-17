"""
Script untuk membuat tabel project_timeline di database yang sudah ada
Jalankan script ini jika timeline table belum ada
"""

import sys
from app import create_app, db
from sqlalchemy import text

app = create_app('development')

def create_timeline_table():
    """Membuat tabel project_timeline"""
    with app.app_context():
        try:
            # Ini akan create table jika belum ada
            db.create_all()
            print("✅ Tabel project_timeline berhasil dibuat atau sudah ada!")
            
            # Verify table exists menggunakan text()
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'project_timeline' in tables:
                print("✅ Tabel project_timeline confirmed ada di database!")
                columns = inspector.get_columns('project_timeline')
                print(f"   Jumlah kolom: {len(columns)}")
                for col in columns:
                    print(f"   - {col['name']} ({col['type']})")
            else:
                print("❌ Tabel project_timeline tidak ditemukan")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    print("Creating timeline table...")
    success = create_timeline_table()
    if success:
        print("\n✅ Timeline table ready! Sekarang jalankan: python seed_timeline.py")
    sys.exit(0 if success else 1)
