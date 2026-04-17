"""
Setup koneksi MySQL untuk SSM Portal.

Fungsi:
1. Membuat tabel berdasarkan SQLAlchemy model
2. Sinkronkan ENUM users.role agar mendukung mandor/supervisi
3. Seed akun default jika belum ada

Jalankan:
    .venv\\Scripts\\python.exe setup_mysql.py
"""

from sqlalchemy import text
from app import create_app
from models import db, User


DEFAULT_USERS = [
    {
        "username": "admin",
        "password": "admin123",
        "nama": "Super Admin",
        "email": "admin@ssm.co.id",
        "role": "admin",
        "jabatan": "Administrator",
    },
    {
        "username": "mandor1",
        "password": "mandor123",
        "nama": "Mandor Default",
        "email": "mandor1@ssm.co.id",
        "role": "mandor",
        "jabatan": "Mandor",
    },
    {
        "username": "supervisi1",
        "password": "supervisi123",
        "nama": "Supervisi Default",
        "email": "supervisi1@ssm.co.id",
        "role": "supervisi",
        "jabatan": "Supervisi",
    },
]


def ensure_role_enum():
    # Paksa skema role agar match dengan model terbaru.
    sql = text(
        """
        ALTER TABLE users
        MODIFY COLUMN role ENUM('admin','user','mandor','supervisi')
        NOT NULL DEFAULT 'user'
        """
    )
    db.session.execute(sql)
    db.session.commit()


def seed_default_users():
    created = []
    for item in DEFAULT_USERS:
        existing = User.query.filter_by(username=item["username"]).first()
        if existing:
            continue

        user = User(
            username=item["username"],
            nama=item["nama"],
            email=item["email"],
            role=item["role"],
            jabatan=item["jabatan"],
            is_active=True,
        )
        user.set_password(item["password"])
        db.session.add(user)
        created.append(item["username"])

    if created:
        db.session.commit()

    return created


def main():
    app = create_app("development")
    with app.app_context():
        db.create_all()
        ensure_role_enum()
        created = seed_default_users()

        print("=" * 58)
        print("SETUP MYSQL SSM PORTAL")
        print("=" * 58)
        print("Database dan tabel berhasil disiapkan.")
        if created:
            print("Akun default dibuat:", ", ".join(created))
        else:
            print("Akun default sudah ada, tidak ada user baru.")
        print("Akun login yang bisa dipakai:")
        print("- admin / admin123")
        print("- mandor1 / mandor123")
        print("- supervisi1 / supervisi123")
        print("=" * 58)


if __name__ == "__main__":
    main()
