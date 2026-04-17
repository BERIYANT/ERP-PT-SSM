#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script untuk membuat tabel petty_cash dan populate dengan sample data
Jalankan: python seed_petty_cash.py
"""

import sys
from datetime import datetime
from app import create_app
from models import db, PettyCash

def seed_petty_cash():
    app = create_app('development')
    
    with app.app_context():
        try:
            # ─── Create all tables ───────────────────────────────────────
            print("📦 Creating database tables...")
            db.create_all()
            print("✅ Tables created successfully")
            
            # ─── Check if data already exists ────────────────────────────
            existing_count = PettyCash.query.count()
            if existing_count > 0:
                print(f"⚠️  Database sudah memiliki {existing_count} records petty cash")
                response = input("Apakah Anda ingin menghapus data lama? (y/n): ")
                if response.lower() == 'y':
                    PettyCash.query.delete()
                    db.session.commit()
                    print("✅ Data lama dihapus")
                else:
                    print("❌ Aborting...")
                    return
            
            # ─── Sample Data ────────────────────────────────────────────
            sample_data = [
                PettyCash(
                    tanggal=datetime(2026, 3, 2).date(),
                    kategori='Transport',
                    deskripsi='BBM Kendaraan Survey',
                    jumlah=200000,
                    keterangan='Pengisian BBM di SPBU',
                    created_by=None
                ),
                PettyCash(
                    tanggal=datetime(2026, 3, 2).date(),
                    kategori='Makan',
                    deskripsi='Makan Siang Tim',
                    jumlah=150000,
                    keterangan='Makan bersama di kantin',
                    created_by=None
                ),
                PettyCash(
                    tanggal=datetime(2026, 3, 1).date(),
                    kategori='Office',
                    deskripsi='Pembelian Alat Tulis',
                    jumlah=75000,
                    keterangan='Spidol dan kertas HVS',
                    created_by=None
                ),
                PettyCash(
                    tanggal=datetime(2026, 3, 1).date(),
                    kategori='Transport',
                    deskripsi='Ongkos Taksi',
                    jumlah=120000,
                    keterangan='Antar jemput ke lokasi project',
                    created_by=None
                ),
                PettyCash(
                    tanggal=datetime(2026, 2, 28).date(),
                    kategori='Makan',
                    deskripsi='Snack Rapat',
                    jumlah=85000,
                    keterangan='Kopi dan snack untuk rapat',
                    created_by=None
                ),
                PettyCash(
                    tanggal=datetime(2026, 2, 28).date(),
                    kategori='Lainnya',
                    deskripsi='Maintenance Printer',
                    jumlah=250000,
                    keterangan='Service printer kantor',
                    created_by=None
                ),
                PettyCash(
                    tanggal=datetime(2026, 2, 27).date(),
                    kategori='Office',
                    deskripsi='Fotocopy Dokumen',
                    jumlah=50000,
                    keterangan='Fotocopy RAB project',
                    created_by=None
                ),
                PettyCash(
                    tanggal=datetime(2026, 2, 27).date(),
                    kategori='Transport',
                    deskripsi='BBM Kendaraan',
                    jumlah=200000,
                    keterangan='Pengisian BBM',
                    created_by=None
                ),
            ]
            
            # ─── Insert data ────────────────────────────────────────────
            print("\n📝 Seeding sample data...")
            for data in sample_data:
                db.session.add(data)
            
            db.session.commit()
            print(f"✅ {len(sample_data)} petty cash records berhasil ditambahkan")
            
            # ─── Verify ─────────────────────────────────────────────────
            total_count = PettyCash.query.count()
            total_amount = db.session.query(db.func.sum(PettyCash.jumlah)).scalar() or 0
            
            print("\n" + "="*50)
            print(f"📊 Total Records: {total_count}")
            print(f"💰 Total Amount: Rp {float(total_amount):,.0f}")
            print("="*50)
            print("\n✅ Seeding completed successfully!")
            print("📍 Akses halaman: http://localhost:5000/petty-cash")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            db.session.rollback()
            return False
    
    return True


if __name__ == '__main__':
    success = seed_petty_cash()
    sys.exit(0 if success else 1)
