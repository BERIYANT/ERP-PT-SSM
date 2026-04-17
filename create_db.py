from app import create_app
from models import db

app = create_app('default')
with app.app_context():
    db.create_all()
    print("Database tables updated successfully!")
