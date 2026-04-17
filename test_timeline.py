from app import create_app
from models import db, ProjectTimeline
from datetime import datetime

app = create_app()
with app.app_context():
    try:
        t = ProjectTimeline(project_id=1, number=1, task_name='Test', tanggal=datetime.now().date(), status='planned')
        db.session.add(t)
        db.session.commit()
        print("Success inserting")
        db.session.delete(t)
        db.session.commit()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
