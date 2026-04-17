#!/usr/bin/env python
"""Script untuk menambahkan test data ke Project 1 agar diagram muncul"""

from app import create_app
from models import db, Project, ProjectRAB, Material, PettyCash
from datetime import datetime, date

app = create_app('development')
with app.app_context():
    project = Project.query.get(1)
    
    if not project:
        print("❌ Project 1 tidak ditemukan")
        exit(1)
    
    print(f"=== Menambahkan Test Data ke {project.project_name} ===\n")
    
    # 1. Add RAB Items
    print("1️⃣ Menambahkan RAB Items...")
    rab_items = [
        {
            'kategori': 'jasa',
            'deskripsi': 'Jasa Engineering',
            'satuan': 'ls',
            'volume': 1,
            'harga_satuan': 100000000,
            'total': 100000000
        },
        {
            'kategori': 'material',
            'deskripsi': 'Kabel & Perlengkapan',
            'satuan': 'ls',
            'volume': 1,
            'harga_satuan': 200000000,
            'total': 200000000
        },
        {
            'kategori': 'overhead',
            'deskripsi': 'Biaya Overhead Proyek',
            'satuan': 'ls',
            'volume': 1,
            'harga_satuan': 350000000,
            'total': 350000000
        },
        {
            'kategori': 'patty_cash',
            'deskripsi': 'Petty Cash',
            'satuan': 'ls',
            'volume': 1,
            'harga_satuan': 50000000,
            'total': 50000000
        },
    ]
    
    for item in rab_items:
        rab = ProjectRAB(
            project_id=project.id,
            kategori=item['kategori'],
            deskripsi=item['deskripsi'],
            satuan=item['satuan'],
            volume=item['volume'],
            harga_satuan=item['harga_satuan'],
            total=item['total']
        )
        db.session.add(rab)
        print(f"   ✓ {item['kategori']}: Rp {item['total']:,}")
    
    db.session.commit()
    print("   ✅ RAB items ditambahkan\n")
    
    # 2. Add Materials
    print("2️⃣ Menambahkan Materials...")
    materials = [
        {'name': 'Kabel A (untuk Project 1)', 'price': 50000000},
        {'name': 'Kabel B (untuk Project 1)', 'price': 75000000},
        {'name': 'Hardware (untuk Project 1)', 'price': 75000000},
    ]
    
    for mat in materials:
        material = Material(
            project_id=project.id,
            name=mat['name'],
            price=mat['price'],
            source='gudang',
            used=False
        )
        db.session.add(material)
        print(f"   ✓ {mat['name']}: Rp {mat['price']:,}")
    
    db.session.commit()
    print("   ✅ Materials ditambahkan\n")
    
    # 3. Add Petty Cash
    print("3️⃣ Menambahkan Petty Cash Items...")
    petty_items = [
        {'kategori': 'Transport', 'deskripsi': 'Biaya transportasi', 'jumlah': 5000000},
        {'kategori': 'Makan', 'deskripsi': 'Biaya makan tim', 'jumlah': 3000000},
        {'kategori': 'Office', 'deskripsi': 'Biaya kantor', 'jumlah': 2000000},
    ]
    
    for item in petty_items:
        petty = PettyCash(
            project_id=project.id,
            tanggal=date.today(),
            kategori=item['kategori'],
            deskripsi=item['deskripsi'],
            jumlah=item['jumlah']
        )
        db.session.add(petty)
        print(f"   ✓ {item['kategori']}: Rp {item['jumlah']:,}")
    
    db.session.commit()
    print("   ✅ Petty Cash items ditambahkan\n")
    
    # Summary
    print("=" * 50)
    print("📊 RINGKASAN DATA YANG DITAMBAHKAN:")
    print("=" * 50)
    print(f"Project: {project.project_name}")
    print(f"Budget Awal: Rp {project.amount:,}\n")
    
    rab_total = sum(r.total for r in ProjectRAB.query.filter_by(project_id=project.id).all())
    print(f"Total RAB: Rp {rab_total:,}")
    
    mat_total = sum(m.price for m in Material.query.filter_by(project_id=project.id).all())
    print(f"Total Materials: Rp {mat_total:,}")
    
    petty_total = sum(p.jumlah for p in PettyCash.query.filter_by(project_id=project.id).all())
    print(f"Total Petty Cash: Rp {petty_total:,}")
    
    print("\n✅ Data berhasil ditambahkan! Sekarang diagram akan muncul di dashboard.")
    print("🔄 Silakan refresh browser untuk melihat perubahannya.")
