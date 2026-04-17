"""
Script untuk menambahkan sample data Timeline ke database
Timeline akan otomatis menyesuaikan status berdasarkan tanggal sistem
"""

from datetime import datetime, timedelta
from app import create_app
from models import db, Project, ProjectTimeline

app = create_app('development')

def get_status_by_date(tanggal):
    """
    Menentukan status berdasarkan perbandingan tanggal
    - Jika tanggal < hari ini: completed
    - Jika tanggal == hari ini: in_progress
    - Jika tanggal > hari ini: planned
    """
    today = datetime.now().date()
    
    if tanggal < today:
        return 'completed'
    elif tanggal == today:
        return 'in_progress'
    else:
        return 'planned'

def seed_timeline_for_projects():
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        # Get all projects
        projects = Project.query.all()
        
        if not projects:
            print("⚠️  Tidak ada project. Skipping timeline seeding...")
            return
        
        total_added = 0
        today = datetime.now().date()
        
        # Create 7-day timeline starting from 3 days ago
        start_date = today - timedelta(days=3)
        
        for project in projects:
            # Check if already has timeline
            existing_timeline = ProjectTimeline.query.filter_by(
                project_id=project.id
            ).first()
            
            if existing_timeline:
                print(f"⏭️  Project '{project.project_name}' sudah memiliki timeline. Skip...")
                continue
            
            # Nama-nama task untuk timeline
            task_names = [
                'Kickoff Meeting',
                'Survey Lokasi',
                'Pengadaan Material',
                'Mobilisasi Tim',
                'Pelaksanaan',
                'Quality Check',
                'Serah Terima'
            ]
            
            timeline_items = []
            for i, task_name in enumerate(task_names):
                tanggal = start_date + timedelta(days=i)
                status = get_status_by_date(tanggal)
                
                timeline_items.append({
                    'number': i + 1,
                    'task_name': task_name,
                    'tanggal': tanggal,
                    'status': status
                })
            
            # Add timeline items
            for item in timeline_items:
                timeline = ProjectTimeline(
                    project_id=project.id,
                    number=item['number'],
                    task_name=item['task_name'],
                    tanggal=item['tanggal'],
                    status=item['status'],
                    notes=None
                )
                db.session.add(timeline)
                total_added += 1
            
            db.session.commit()
            print(f"✅ Timeline untuk project '{project.project_name}' berhasil ditambahkan (7 items)")
        
        print(f"\n✅ Total {total_added} timeline items berhasil ditambahkan!")
        print(f"\n📅 Timeline Configuration:")
        print(f"   Mulai dari: {start_date.strftime('%d %b %Y')}")
        print(f"   Hari ini: {today.strftime('%d %b %Y')}")
        print(f"   Sampai: {(start_date + timedelta(days=6)).strftime('%d %b %Y')}")
        print(f"\n📊 Status otomatis berdasarkan tanggal sistem:")
        print(f"   - Tanggal lalu: COMPLETED (hijau)")
        print(f"   - Hari ini: IN_PROGRESS (biru)")
        print(f"   - Tanggal mendatang: PLANNED (putih)")

if __name__ == '__main__':
    seed_timeline_for_projects()

if __name__ == '__main__':
    seed_timeline_for_projects()
