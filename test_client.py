from dotenv import load_dotenv
load_dotenv()
from app import create_app
from models import db
app = create_app()

with app.test_client() as client:
    # First we might need a fake login if @login_required blocks
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'admin'
        sess['role'] = 'superadmin'

    response = client.post('/api/projects/1/timeline', json={
        "number": 1,
        "task_name": "Test",
        "tanggal": "2026-05-15",
        "status": "planned",
        "notes": ""
    })
    print("Status:", response.status_code)
    print("Data:", response.data.decode('utf-8'))
