from dotenv import load_dotenv
load_dotenv()
from app import create_app
from models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        from models import ProjectTimeline
        t = ProjectTimeline.query.first()
        print("Success query timeline")
    except Exception as e:
        print(f"Error querying timeline: {e}")
