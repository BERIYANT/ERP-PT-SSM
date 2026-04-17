from datetime import date
from flask import Blueprint, request, jsonify, session
from models import db, Project, ProjectRAB, ProjectTimeline, ProjectJasaSlip, Customer
from routes.auth import login_required, catat_log

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')


# ─── GET /api/projects ───────────────────────────────────────────────────────
@projects_bp.route('/', methods=['GET'])
@login_required
def get_projects():
    project_type = request.args.get('type')        # 'po' | 'non_po'
    status       = request.args.get('status')      # 'active' | 'archived'
    customer_id  = request.args.get('customer_id', type=int)

    q = Project.query
    if project_type:
        q = q.filter_by(project_type=project_type)
    if status:
        q = q.filter_by(status=status)
    if customer_id:
        q = q.filter_by(customer_id=customer_id)

    projects = q.order_by(Project.created_at.desc()).all()
    return jsonify({'success': True, 'data': [p.to_dict() for p in projects]})


# ─── GET /api/projects/<id> ──────────────────────────────────────────────────
@projects_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_project(id):
    p = Project.query.get_or_404(id)
    data = p.to_dict()
    data['rab'] = [r.to_dict() for r in p.rab]
    return jsonify({'success': True, 'data': data})


# ─── POST /api/projects ──────────────────────────────────────────────────────
@projects_bp.route('/', methods=['POST'])
@login_required
def create_project():
    data = request.get_json(silent=True) or {}

    customer_id  = data.get('customer_id')
    project_name = (data.get('project_name') or '').strip()
    jasa_amount = float(data.get('jasa_amount', 0) or 0)
    material_amount = float(data.get('material_amount', 0) or 0)
    overhead_amount = float(data.get('overhead_amount', 0) or 0)
    petty_cash_amount = float(data.get('petty_cash_amount', data.get('patty_cash_amount', 0)) or 0)
    breakdown_total = jasa_amount + material_amount + overhead_amount + petty_cash_amount
    incoming_amount = float(data.get('amount', 0) or 0)
    project_amount = incoming_amount if incoming_amount > 0 else breakdown_total

    if not customer_id or not project_name:
        return jsonify({'success': False,
                        'message': 'customer_id dan project_name wajib diisi.'}), 400

    if not Customer.query.get(customer_id):
        return jsonify({'success': False, 'message': 'Customer tidak ditemukan.'}), 404

    project = Project(
        customer_id   = customer_id,
        project_type  = data.get('project_type', 'po'),
        project_name  = project_name,
        po_number     = data.get('po_number', '').strip() or None,
        po_date       = _parse_date(data.get('po_date')),
        description   = data.get('description', '').strip() or None,
        amount        = project_amount,
        created_by    = session.get('user_id'),
    )
    db.session.add(project)
    db.session.commit()

    if breakdown_total > 0:
        breakdown_items = [
            ('jasa', jasa_amount),
            ('material', material_amount),
            ('overhead', overhead_amount),
            ('patty_cash', petty_cash_amount),
        ]
        added_rab = []
        for kategori, nominal in breakdown_items:
            if nominal <= 0:
                continue
            rab = ProjectRAB(
                project_id=project.id,
                kategori=kategori,
                deskripsi='Auto breakdown dari form project',
                satuan='ls',
                volume=1,
                harga_satuan=nominal,
                total=nominal,
            )
            db.session.add(rab)
            added_rab.append(kategori)
        db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'CREATE', 'Project', f'Menambahkan project: {project_name}')

    return jsonify({'success': True, 'message': 'Project berhasil ditambahkan.',
                    'data': project.to_dict()}), 201


# ─── PUT /api/projects/<id> ──────────────────────────────────────────────────
@projects_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_project(id):
    p = Project.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    p.project_name = (data.get('project_name') or p.project_name).strip()
    p.po_number    = data.get('po_number', p.po_number)
    p.po_date      = _parse_date(data.get('po_date')) or p.po_date
    p.description  = data.get('description', p.description)
    p.amount       = float(data.get('amount', p.amount) or p.amount)
    p.project_type = data.get('project_type', p.project_type)

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'UPDATE', 'Project', f'Mengubah project ID {id}: {p.project_name}')

    return jsonify({'success': True, 'message': 'Project berhasil diperbarui.',
                    'data': p.to_dict()})


# ─── PATCH /api/projects/<id>/archive ────────────────────────────────────────
@projects_bp.route('/<int:id>/archive', methods=['PATCH'])
@login_required
def archive_project(id):
    p = Project.query.get_or_404(id)
    p.status         = 'archived'
    p.completed_date = date.today()
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'ARCHIVE', 'Project', f'Mengarsipkan project: {p.project_name}')

    return jsonify({'success': True, 'message': f'Project "{p.project_name}" dipindahkan ke arsip.',
                    'data': p.to_dict()})


# ─── PATCH /api/projects/<id>/restore ────────────────────────────────────────
@projects_bp.route('/<int:id>/restore', methods=['PATCH'])
@login_required
def restore_project(id):
    p = Project.query.get_or_404(id)
    p.status         = 'active'
    p.completed_date = None
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'RESTORE', 'Project', f'Memulihkan project dari arsip: {p.project_name}')

    return jsonify({'success': True, 'message': f'Project "{p.project_name}" dipulihkan.',
                    'data': p.to_dict()})


# ─── DELETE /api/projects/<id> ───────────────────────────────────────────────
@projects_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_project(id):
    p = Project.query.get_or_404(id)
    name = p.project_name
    db.session.delete(p)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'DELETE', 'Project', f'Menghapus project: {name}')

    return jsonify({'success': True, 'message': f'Project "{name}" berhasil dihapus.'})


# ═══════════════════════════════════════════════════════════════
# RAB (Rencana Anggaran Biaya)
# ═══════════════════════════════════════════════════════════════

# ─── GET /api/projects/<id>/rab ──────────────────────────────────────────────
@projects_bp.route('/<int:id>/rab', methods=['GET'])
@login_required
def get_rab(id):
    Project.query.get_or_404(id)
    rab = ProjectRAB.query.filter_by(project_id=id).all()
    return jsonify({'success': True, 'data': [r.to_dict() for r in rab]})


# ─── POST /api/projects/<id>/rab ─────────────────────────────────────────────
@projects_bp.route('/<int:id>/rab', methods=['POST'])
@login_required
def add_rab(id):
    Project.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    # Support single object or list of objects
    items = data if isinstance(data, list) else [data]
    added = []

    for item in items:
        kategori = item.get('kategori', '').strip()
        if kategori not in ('jasa', 'material', 'overhead', 'patty_cash'):
            continue
        rab = ProjectRAB(
            project_id   = id,
            kategori     = kategori,
            deskripsi    = item.get('deskripsi', '').strip() or None,
            satuan       = item.get('satuan', '').strip() or None,
            volume       = float(item.get('volume', 0) or 0) or None,
            harga_satuan = float(item.get('harga_satuan', 0) or 0) or None,
            total        = float(item.get('total', 0) or 0) or None,
        )
        db.session.add(rab)
        added.append(rab)

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'CREATE', 'RAB', f'Menambahkan {len(added)} item RAB ke project ID {id}')

    return jsonify({'success': True,
                    'message': f'{len(added)} item RAB berhasil ditambahkan.',
                    'data': [r.to_dict() for r in added]}), 201


# ─── PUT /api/projects/rab/<rab_id> ──────────────────────────────────────────
@projects_bp.route('/rab/<int:rab_id>', methods=['PUT'])
@login_required
def update_rab(rab_id):
    rab  = ProjectRAB.query.get_or_404(rab_id)
    data = request.get_json(silent=True) or {}

    rab.deskripsi    = data.get('deskripsi', rab.deskripsi)
    rab.satuan       = data.get('satuan', rab.satuan)
    rab.volume       = float(data.get('volume', rab.volume or 0) or 0) or None
    rab.harga_satuan = float(data.get('harga_satuan', rab.harga_satuan or 0) or 0) or None
    rab.total        = float(data.get('total', rab.total or 0) or 0) or None

    db.session.commit()
    return jsonify({'success': True, 'message': 'RAB berhasil diperbarui.',
                    'data': rab.to_dict()})


# ─── DELETE /api/projects/rab/<rab_id> ───────────────────────────────────────
@projects_bp.route('/rab/<int:rab_id>', methods=['DELETE'])
@login_required
def delete_rab(rab_id):
    rab = ProjectRAB.query.get_or_404(rab_id)
    db.session.delete(rab)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Item RAB berhasil dihapus.'})


# ─── GET /api/projects/<id>/timeline ─────────────────────────────────────────
@projects_bp.route('/<int:id>/timeline', methods=['GET'])
@login_required
def get_timeline(id):
    Project.query.get_or_404(id)
    timeline = ProjectTimeline.query.filter_by(project_id=id).order_by(
        ProjectTimeline.number).all()
    return jsonify({'success': True, 'data': [t.to_dict() for t in timeline]})


# ─── POST /api/projects/<id>/timeline ────────────────────────────────────────
@projects_bp.route('/<int:id>/timeline', methods=['POST'])
@login_required
def add_timeline(id):
    Project.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    # Support single object or list of objects
    items = data if isinstance(data, list) else [data]
    added = []

    for item in items:
        timeline = ProjectTimeline(
            project_id = id,
            number     = item.get('number', 0),
            task_name  = (item.get('task_name') or '').strip(),
            tanggal    = _parse_date(item.get('tanggal')),
            status     = item.get('status', 'planned'),
            notes      = (item.get('notes') or '').strip() or None,
        )
        db.session.add(timeline)
        added.append(timeline)

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'CREATE', 'Timeline', 
              f'Menambahkan {len(added)} timeline item ke project ID {id}')

    return jsonify({'success': True,
                    'message': f'{len(added)} timeline item berhasil ditambahkan.',
                    'data': [t.to_dict() for t in added]}), 201


# ─── PUT /api/projects/timeline/<timeline_id> ────────────────────────────────
@projects_bp.route('/timeline/<int:timeline_id>', methods=['PUT'])
@login_required
def update_timeline(timeline_id):
    timeline = ProjectTimeline.query.get_or_404(timeline_id)
    data = request.get_json(silent=True) or {}

    timeline.number    = data.get('number', timeline.number)
    timeline.task_name = (data.get('task_name') or timeline.task_name).strip()
    timeline.tanggal   = _parse_date(data.get('tanggal')) or timeline.tanggal
    timeline.status    = data.get('status', timeline.status)
    timeline.notes     = data.get('notes', timeline.notes)

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'UPDATE', 'Timeline', f'Mengubah timeline ID {timeline_id}')

    return jsonify({'success': True, 'message': 'Timeline berhasil diperbarui.',
                    'data': timeline.to_dict()})


# ─── DELETE /api/projects/timeline/<timeline_id> ──────────────────────────────
@projects_bp.route('/timeline/<int:timeline_id>', methods=['DELETE'])
@login_required
def delete_timeline(timeline_id):
    timeline = ProjectTimeline.query.get_or_404(timeline_id)
    db.session.delete(timeline)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'DELETE', 'Timeline', f'Menghapus timeline ID {timeline_id}')

    return jsonify({'success': True, 'message': 'Timeline berhasil dihapus.'})


# ─── Utility ──────────────────────────────────────────────────────────────────

def _parse_date(value):
    if not value:
        return None
    try:
        from datetime import datetime
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


# ═══════════════════════════════════════════════════════════════
# JASA SLIP GAJI KARYAWAN (PER PROJECT)
# ═══════════════════════════════════════════════════════════════

# ─── GET /api/projects/<id>/jasa-slips ─────────────────────────────────────
@projects_bp.route('/<int:id>/jasa-slips', methods=['GET'])
@login_required
def get_jasa_slips(id):
    project = Project.query.get_or_404(id)

    period = (request.args.get('period') or '').strip()
    q = ProjectJasaSlip.query.filter_by(project_id=id)
    if period:
        q = q.filter_by(period_month=period)

    items = q.order_by(ProjectJasaSlip.created_at.desc()).all()
    total = sum(float(item.jumlah_gaji or 0) for item in items)

    return jsonify({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.project_name,
        },
        'data': [item.to_dict() for item in items],
        'total': total,
    })


# ─── POST /api/projects/<id>/jasa-slips ────────────────────────────────────
@projects_bp.route('/<int:id>/jasa-slips', methods=['POST'])
@login_required
def create_jasa_slip(id):
    project = Project.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    employee_name = (data.get('employee_name') or '').strip()
    period_month = (data.get('period_month') or '').strip()
    jumlah_gaji = float(data.get('jumlah_gaji', 0) or 0)

    if not employee_name:
        return jsonify({'success': False, 'message': 'Nama karyawan wajib diisi.'}), 400
    if not period_month:
        return jsonify({'success': False, 'message': 'Periode wajib diisi.'}), 400
    if jumlah_gaji <= 0:
        return jsonify({'success': False, 'message': 'Jumlah gaji harus lebih dari 0.'}), 400

    item = ProjectJasaSlip(
        project_id=id,
        employee_name=employee_name,
        period_month=period_month,
        posisi=(data.get('posisi') or '').strip() or None,
        hari_kerja=int(data.get('hari_kerja')) if data.get('hari_kerja') not in (None, '') else None,
        jumlah_gaji=jumlah_gaji,
        tanggal_bayar=_parse_date(data.get('tanggal_bayar')),
        keterangan=(data.get('keterangan') or '').strip() or None,
        created_by=session.get('user_id'),
    )

    db.session.add(item)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'CREATE', 'Project Jasa Slip',
              f'Menambahkan slip gaji {employee_name} untuk project {project.project_name}')

    return jsonify({
        'success': True,
        'message': 'Slip gaji berhasil ditambahkan.',
        'data': item.to_dict(),
    }), 201


# ─── PUT /api/projects/<id>/jasa-slips/<slip_id> ───────────────────────────
@projects_bp.route('/<int:id>/jasa-slips/<int:slip_id>', methods=['PUT'])
@login_required
def update_jasa_slip(id, slip_id):
    Project.query.get_or_404(id)
    item = ProjectJasaSlip.query.filter_by(project_id=id, id=slip_id).first_or_404()
    data = request.get_json(silent=True) or {}

    if 'employee_name' in data:
        item.employee_name = (data.get('employee_name') or '').strip()
        if not item.employee_name:
            return jsonify({'success': False, 'message': 'Nama karyawan wajib diisi.'}), 400

    if 'period_month' in data:
        item.period_month = (data.get('period_month') or '').strip()
        if not item.period_month:
            return jsonify({'success': False, 'message': 'Periode wajib diisi.'}), 400

    if 'posisi' in data:
        item.posisi = (data.get('posisi') or '').strip() or None

    if 'hari_kerja' in data:
        item.hari_kerja = int(data.get('hari_kerja')) if data.get('hari_kerja') not in (None, '') else None

    if 'jumlah_gaji' in data:
        new_gaji = float(data.get('jumlah_gaji', 0) or 0)
        if new_gaji <= 0:
            return jsonify({'success': False, 'message': 'Jumlah gaji harus lebih dari 0.'}), 400
        item.jumlah_gaji = new_gaji

    if 'tanggal_bayar' in data:
        item.tanggal_bayar = _parse_date(data.get('tanggal_bayar'))

    if 'keterangan' in data:
        item.keterangan = (data.get('keterangan') or '').strip() or None

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'UPDATE', 'Project Jasa Slip',
              f'Mengubah slip gaji ID {slip_id} pada project ID {id}')

    return jsonify({
        'success': True,
        'message': 'Slip gaji berhasil diperbarui.',
        'data': item.to_dict(),
    })


# ─── DELETE /api/projects/<id>/jasa-slips/<slip_id> ────────────────────────
@projects_bp.route('/<int:id>/jasa-slips/<int:slip_id>', methods=['DELETE'])
@login_required
def delete_jasa_slip(id, slip_id):
    Project.query.get_or_404(id)
    item = ProjectJasaSlip.query.filter_by(project_id=id, id=slip_id).first_or_404()

    employee_name = item.employee_name
    db.session.delete(item)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'DELETE', 'Project Jasa Slip',
              f'Menghapus slip gaji {employee_name} pada project ID {id}')

    return jsonify({'success': True, 'message': 'Slip gaji berhasil dihapus.'})


# ─── GET /api/projects/<id>/jasa-slips/summary ──────────────────────────────
@projects_bp.route('/<int:id>/jasa-slips/summary', methods=['GET'])
@login_required
def get_jasa_slips_summary(id):
    project = Project.query.get_or_404(id)
    items = ProjectJasaSlip.query.filter_by(project_id=id).all()

    total_slip = len(items)
    total_bayar = sum(float(item.jumlah_gaji or 0) for item in items)

    return jsonify({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.project_name,
        },
        'summary': {
            'total_slip': total_slip,
            'total_bayar': total_bayar,
        },
    })
