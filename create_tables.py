"""
Script untuk membuat tabel database
"""
from app import create_app
from models import db, ProjectOverheadOpname, ProjectOverheadKasbonMandor, ProjectJasaSlip

app = create_app('development')

with app.app_context():
    # Create all tables
    db.create_all()
    print('✅ Database tables created successfully!')
    print('✅ Tabel project_overhead_opname siap digunakan')
    print('✅ Tabel project_overhead_kasbon_mandor siap digunakan')
    print('✅ Tabel project_jasa_slip siap digunakan')
