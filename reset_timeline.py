"""
Script untuk reset dan re-seed timeline data dengan tanggal dinamis
Timeline akan otomatis menyesuaikan status berdasarkan tanggal sistem
"""

from datetime import datetime, timedelta
from app import create_app, db
from models import ProjectTimeline, Project

app = create_app('development')

def get_status_by_date(tanggal, start_date, index):
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

def reset_and_seed_timeline():
    with app.app_context():
        # Get all projects
        projects = Project.query.all()
        
        if not projects:
            print("⚠️  Tidak ada project. Skipping...")
            return
        
        # Delete existing timeline
        ProjectTimeline.query.delete()
        db.session.commit()
        print("🗑️  Timeline lama dihapus")
        
        total_added = 0
        today = datetime.now().date()
        
        # Create 7-day timeline starting from 3 days ago
        start_date = today - timedelta(days=3)
        
        for project in projects:
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
                status = get_status_by_date(tanggal, start_date, i)
                
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
            print(f"✅ Timeline untuk project '{project.project_name}' berhasil ditambahkan kembali (7 items)")
        
        print(f"\n✅ Total {total_added} timeline items berhasil di-reset dan di-seed!")
        print(f"\n📅 Timeline Configuration:")
        print(f"   Mulai dari: {start_date.strftime('%d %b %Y')}")
        print(f"   Hari ini: {today.strftime('%d %b %Y')}")
        print(f"   Sampai: {(start_date + timedelta(days=6)).strftime('%d %b %Y')}")
        print(f"\n📊 Status Distribution (berdasarkan tanggal hari ini):")
        
        # Count status
        non_proj = Project.query.first()
        if non_proj:
            tls = ProjectTimeline.query.filter_by(project_id=non_proj.id).all()
            completed = len([t for t in tls if t.status == 'completed'])
            in_prog = len([t for t in tls if t.status == 'in_progress'])
            planned = len([t for t in tls if t.status == 'planned'])
            print(f"   - {completed} items: COMPLETED (hijau)")
            print(f"   - {in_prog} item: IN_PROGRESS (biru)")
            print(f"   - {planned} items: PLANNED (putih)")

if __name__ == '__main__':
    print("Resetting dan re-seeding timeline dengan tanggal dinamis...\n")
    reset_and_seed_timeline()
