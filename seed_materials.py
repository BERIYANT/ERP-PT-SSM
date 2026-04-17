"""
Script untuk menambahkan sample data Material ke database
Jalankan ini sekali untuk populate database dengan data awal
"""

from app import create_app
from models import db, Material

app = create_app('development')

with app.app_context():
    # Pastikan table sudah dibuat
    db.create_all()
    
    # Check apakah sudah ada data
    existing = Material.query.first()
    if existing:
        print("⚠️  Database sudah berisi data Material. Skipping...")
    else:
        # Sample data
        sample_materials = [
            # Gudang
            Material(name='Kabel A', price=1000000, source='gudang', used=False),
            Material(name='Kabel B', price=1000000, source='gudang', used=False),
            Material(name='Kabel C', price=1000000, source='gudang', used=False),
            Material(name='Kabel D', price=1000000, source='gudang', used=False),
            Material(name='Kabel E', price=1000000, source='gudang', used=False),
            # Lapangan
            Material(name='Kabel F', price=1000000, source='lapangan', used=True),
            Material(name='Kabel G', price=1000000, source='lapangan', used=True),
            Material(name='Kabel H', price=1000000, source='lapangan', used=True),
            Material(name='Kabel I', price=1000000, source='lapangan', used=True),
            Material(name='Kabel J', price=1000000, source='lapangan', used=True),
        ]
        
        for material in sample_materials:
            db.session.add(material)
        
        db.session.commit()
        print("✅ Sample Material berhasil ditambahkan ke database!")
        print(f"   Total: {len(sample_materials)} material")
        print("   - 5 material di Gudang")
        print("   - 5 material di Lapangan")
