from datetime import datetime
from flask import Blueprint, request, jsonify, session
from models import db, ProjectOverheadOpname, ProjectOverheadKasbonMandor, Project
from routes.auth import login_required, catat_log

project_overhead_bp = Blueprint('project_overhead', __name__, url_prefix='/api/projects')
VALID_KASBON_STATUS = {'saldo', 'pending', 'approved', 'rejected', 'paid'}


# ─── GET /api/projects/<project_id>/overhead ──────────────────────────────────
@project_overhead_bp.route('/<int:project_id>/overhead', methods=['GET'])
@login_required
def get_overhead_list(project_id):
    """Get all overhead opname items for a specific project."""
    project = Project.query.get_or_404(project_id)
    
    items = ProjectOverheadOpname.query.filter_by(
        project_id=project_id
    ).order_by(ProjectOverheadOpname.created_at.desc()).all()
    
    total_nilai = sum(float(item.nilai_opname or 0) for item in items)
    
    return jsonify({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.project_name,
        },
        'data': [item.to_dict() for item in items],
        'total': total_nilai,
    })


# ─── GET /api/projects/<project_id>/overhead/<overhead_id> ────────────────────
@project_overhead_bp.route('/<int:project_id>/overhead/<int:overhead_id>', methods=['GET'])
@login_required
def get_overhead_item(project_id, overhead_id):
    """Get a specific overhead opname item."""
    item = ProjectOverheadOpname.query.filter_by(
        id=overhead_id,
        project_id=project_id
    ).first_or_404()
    
    return jsonify({
        'success': True,
        'data': item.to_dict()
    })


# ─── POST /api/projects/<project_id>/overhead ─────────────────────────────────
@project_overhead_bp.route('/<int:project_id>/overhead', methods=['POST'])
@login_required
def create_overhead_item(project_id):
    """Create a new overhead opname item for a project."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json(silent=True) or {}
    
    mandor_name = (data.get('mandor_name') or '').strip()
    item_pekerjaan = (data.get('item_pekerjaan') or '').strip()
    
    if not mandor_name or not item_pekerjaan:
        return jsonify({
            'success': False,
            'message': 'Nama Mandor dan Item Pekerjaan wajib diisi.'
        }), 400
    
    volume_progress = float(data.get('volume_progress', 0) or 0)
    harga_satuan = float(data.get('harga_satuan', 0) or 0)
    nilai_opname = volume_progress * harga_satuan
    
    item = ProjectOverheadOpname(
        project_id      = project_id,
        mandor_name     = mandor_name,
        jumlah_pekerja  = data.get('jumlah_pekerja'),
        span            = (data.get('span') or '').strip() or None,
        item_pekerjaan  = item_pekerjaan,
        volume_progress = volume_progress,
        harga_satuan    = harga_satuan,
        nilai_opname    = nilai_opname,
        keterangan      = (data.get('keterangan') or '').strip() or None,
        created_by      = session.get('user_id'),
    )
    
    db.session.add(item)
    db.session.commit()
    
    catat_log(
        session.get('user_id'),
        session.get('username'),
        'CREATE',
        'Project Overhead',
        f'Menambahkan overhead opname untuk project {project.project_name}: {mandor_name} - {item_pekerjaan}'
    )
    
    return jsonify({
        'success': True,
        'message': 'Data overhead berhasil ditambahkan.',
        'data': item.to_dict()
    }), 201


# ─── PUT /api/projects/<project_id>/overhead/<overhead_id> ────────────────────
@project_overhead_bp.route('/<int:project_id>/overhead/<int:overhead_id>', methods=['PUT'])
@login_required
def update_overhead_item(project_id, overhead_id):
    """Update an existing overhead opname item."""
    item = ProjectOverheadOpname.query.filter_by(
        id=overhead_id,
        project_id=project_id
    ).first_or_404()
    
    data = request.get_json(silent=True) or {}
    
    if 'mandor_name' in data:
        item.mandor_name = (data['mandor_name'] or '').strip()
    if 'jumlah_pekerja' in data:
        item.jumlah_pekerja = data.get('jumlah_pekerja')
    if 'span' in data:
        item.span = (data.get('span') or '').strip() or None
    if 'item_pekerjaan' in data:
        item.item_pekerjaan = (data['item_pekerjaan'] or '').strip()
    if 'volume_progress' in data:
        item.volume_progress = float(data.get('volume_progress', 0) or 0)
    if 'harga_satuan' in data:
        item.harga_satuan = float(data.get('harga_satuan', 0) or 0)
    if 'keterangan' in data:
        item.keterangan = (data.get('keterangan') or '').strip() or None
    
    # Recalculate nilai_opname
    item.nilai_opname = float(item.volume_progress or 0) * float(item.harga_satuan or 0)
    
    db.session.commit()
    
    catat_log(
        session.get('user_id'),
        session.get('username'),
        'UPDATE',
        'Project Overhead',
        f'Mengubah overhead opname ID {overhead_id}'
    )
    
    return jsonify({
        'success': True,
        'message': 'Data overhead berhasil diperbarui.',
        'data': item.to_dict()
    })


# ─── DELETE /api/projects/<project_id>/overhead/<overhead_id> ─────────────────
@project_overhead_bp.route('/<int:project_id>/overhead/<int:overhead_id>', methods=['DELETE'])
@login_required
def delete_overhead_item(project_id, overhead_id):
    """Delete an overhead opname item."""
    item = ProjectOverheadOpname.query.filter_by(
        id=overhead_id,
        project_id=project_id
    ).first_or_404()
    
    mandor = item.mandor_name
    
    db.session.delete(item)
    db.session.commit()
    
    catat_log(
        session.get('user_id'),
        session.get('username'),
        'DELETE',
        'Project Overhead',
        f'Menghapus overhead opname: {mandor}'
    )
    
    return jsonify({
        'success': True,
        'message': 'Data overhead berhasil dihapus.'
    })


# ─── GET /api/projects/<project_id>/overhead/summary ──────────────────────────
@project_overhead_bp.route('/<int:project_id>/overhead/summary', methods=['GET'])
@login_required
def get_overhead_summary(project_id):
    """Get summary statistics for project overhead."""
    project = Project.query.get_or_404(project_id)
    
    items = ProjectOverheadOpname.query.filter_by(project_id=project_id).all()
    
    total_nilai = sum(float(item.nilai_opname or 0) for item in items)
    total_items = len(items)
    
    # Get RAB overhead budget if exists
    from models import ProjectRAB
    rab_overhead = ProjectRAB.query.filter_by(
        project_id=project_id,
        kategori='overhead'
    ).first()
    
    budget = float(rab_overhead.total) if rab_overhead and rab_overhead.total else 0
    remaining = budget - total_nilai
    percentage = (total_nilai / budget * 100) if budget > 0 else 0
    
    return jsonify({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.project_name,
        },
        'summary': {
            'total_items': total_items,
            'total_nilai': total_nilai,
            'budget': budget,
            'remaining': remaining,
            'percentage': round(percentage, 2),
        }
    })


# ─── GET /api/projects/<project_id>/overhead/kasbon-mandor ───────────────────
@project_overhead_bp.route('/<int:project_id>/overhead/kasbon-mandor', methods=['GET'])
@login_required
def get_kasbon_mandor_list(project_id):
    """Get kasbon mandor list for a specific project."""
    project = Project.query.get_or_404(project_id)

    status = (request.args.get('status') or 'saldo').strip().lower()
    if status not in VALID_KASBON_STATUS and status != 'all':
        return jsonify({
            'success': False,
            'message': 'Status kasbon tidak valid.'
        }), 400

    query = ProjectOverheadKasbonMandor.query.filter_by(project_id=project_id)
    if status != 'all':
        query = query.filter_by(status=status)

    items = query.order_by(ProjectOverheadKasbonMandor.created_at.desc()).all()

    total_plafon = sum(float(item.plafon or 0) for item in items)
    total_kasbon = sum(float(item.kasbon_belum_dibayar or 0) for item in items)
    total_pembayaran = sum(float(item.pembayaran_terakhir or 0) for item in items)

    return jsonify({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.project_name,
        },
        'status': status,
        'data': [item.to_dict() for item in items],
        'totals': {
            'total_plafon': total_plafon,
            'total_kasbon_belum_dibayar': total_kasbon,
            'total_pembayaran_terakhir': total_pembayaran,
        }
    })


# ─── POST /api/projects/<project_id>/overhead/kasbon-mandor ──────────────────
@project_overhead_bp.route('/<int:project_id>/overhead/kasbon-mandor', methods=['POST'])
@login_required
def create_kasbon_mandor(project_id):
    """Create a new kasbon mandor item for a project."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json(silent=True) or {}

    mandor_name = (data.get('mandor_name') or '').strip()
    if not mandor_name:
        return jsonify({
            'success': False,
            'message': 'Nama mandor wajib diisi.'
        }), 400

    status = (data.get('status') or 'saldo').strip().lower()
    if status not in VALID_KASBON_STATUS:
        return jsonify({
            'success': False,
            'message': 'Status kasbon tidak valid.'
        }), 400

    item = ProjectOverheadKasbonMandor(
        project_id=project_id,
        mandor_name=mandor_name,
        unit_name=(data.get('unit_name') or '').strip() or None,
        plafon=float(data.get('plafon', 0) or 0),
        kasbon_belum_dibayar=float(data.get('kasbon_belum_dibayar', 0) or 0),
        pembayaran_terakhir=float(data.get('pembayaran_terakhir', 0) or 0),
        status=status,
        keterangan=(data.get('keterangan') or '').strip() or None,
        created_by=session.get('user_id'),
    )

    try:
        db.session.add(item)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    catat_log(
        session.get('user_id'),
        session.get('username'),
        'CREATE',
        'Project Overhead Kasbon Mandor',
        f'Menambahkan kasbon mandor untuk project {project.project_name}: {mandor_name}'
    )

    return jsonify({
        'success': True,
        'message': 'Data kasbon mandor berhasil ditambahkan.',
        'data': item.to_dict()
    }), 201


# ─── PUT /api/projects/<project_id>/overhead/kasbon-mandor/<id> ──────────────
@project_overhead_bp.route('/<int:project_id>/overhead/kasbon-mandor/<int:kasbon_id>', methods=['PUT'])
@login_required
def update_kasbon_mandor(project_id, kasbon_id):
    """Update an existing kasbon mandor item."""
    item = ProjectOverheadKasbonMandor.query.filter_by(
        id=kasbon_id,
        project_id=project_id
    ).first_or_404()

    data = request.get_json(silent=True) or {}

    if 'mandor_name' in data:
        item.mandor_name = (data.get('mandor_name') or '').strip()
        if not item.mandor_name:
            return jsonify({
                'success': False,
                'message': 'Nama mandor wajib diisi.'
            }), 400

    if 'unit_name' in data:
        item.unit_name = (data.get('unit_name') or '').strip() or None

    if 'plafon' in data:
        item.plafon = float(data.get('plafon', 0) or 0)

    if 'kasbon_belum_dibayar' in data:
        item.kasbon_belum_dibayar = float(data.get('kasbon_belum_dibayar', 0) or 0)

    if 'pembayaran_terakhir' in data:
        item.pembayaran_terakhir = float(data.get('pembayaran_terakhir', 0) or 0)

    if 'status' in data:
        status = (data.get('status') or '').strip().lower()
        if status not in VALID_KASBON_STATUS:
            return jsonify({
                'success': False,
                'message': 'Status kasbon tidak valid.'
            }), 400
        item.status = status

    if 'keterangan' in data:
        item.keterangan = (data.get('keterangan') or '').strip() or None

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    catat_log(
        session.get('user_id'),
        session.get('username'),
        'UPDATE',
        'Project Overhead Kasbon Mandor',
        f'Mengubah kasbon mandor ID {kasbon_id}'
    )

    return jsonify({
        'success': True,
        'message': 'Data kasbon mandor berhasil diperbarui.',
        'data': item.to_dict()
    })


# ─── DELETE /api/projects/<project_id>/overhead/kasbon-mandor/<id> ───────────
@project_overhead_bp.route('/<int:project_id>/overhead/kasbon-mandor/<int:kasbon_id>', methods=['DELETE'])
@login_required
def delete_kasbon_mandor(project_id, kasbon_id):
    """Delete kasbon mandor item."""
    item = ProjectOverheadKasbonMandor.query.filter_by(
        id=kasbon_id,
        project_id=project_id
    ).first_or_404()

    mandor = item.mandor_name

    try:
        db.session.delete(item)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    catat_log(
        session.get('user_id'),
        session.get('username'),
        'DELETE',
        'Project Overhead Kasbon Mandor',
        f'Menghapus kasbon mandor: {mandor}'
    )

    return jsonify({
        'success': True,
        'message': 'Data kasbon mandor berhasil dihapus.'
    })
