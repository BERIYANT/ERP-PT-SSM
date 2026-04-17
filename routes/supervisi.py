import os
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from models import db, SupervisiLaporan, SupervisiLaporanItem, SupervisiLaporanFoto
from routes.auth import login_required, catat_log

supervisi_bp = Blueprint('supervisi', __name__, url_prefix='/api/supervisi')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _can_access_role():
    return session.get('role') in ('admin', 'supervisi')


@supervisi_bp.route('/laporan', methods=['GET'])
@login_required
def get_laporan_list():
    if not _can_access_role():
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    jenis = (request.args.get('jenis') or '').strip()
    project_id = request.args.get('project_id', type=int)
    tanggal = _parse_date(request.args.get('tanggal'))
    dari = _parse_date(request.args.get('dari'))
    ke = _parse_date(request.args.get('ke'))

    q = SupervisiLaporan.query

    if jenis in ('absen', 'laporan'):
        q = q.filter_by(jenis=jenis)
    if project_id:
        q = q.filter_by(project_id=project_id)
    if tanggal:
        q = q.filter_by(tanggal=tanggal)
    if dari:
        q = q.filter(SupervisiLaporan.tanggal >= dari)
    if ke:
        q = q.filter(SupervisiLaporan.tanggal <= ke)

    items = q.order_by(SupervisiLaporan.tanggal.desc(), SupervisiLaporan.created_at.desc()).all()
    return jsonify({'success': True, 'data': [i.to_dict() for i in items]})


@supervisi_bp.route('/laporan/<int:id>', methods=['GET'])
@login_required
def get_laporan_item(id):
    if not _can_access_role():
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    item = SupervisiLaporan.query.get_or_404(id)
    return jsonify({'success': True, 'data': item.to_dict()})


@supervisi_bp.route('/laporan', methods=['POST'])
@login_required
def create_laporan():
    if not _can_access_role():
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    data = request.get_json(silent=True) or {}

    jenis = (data.get('jenis') or 'laporan').strip()
    if jenis not in ('absen', 'laporan'):
        return jsonify({'success': False, 'message': 'Jenis laporan tidak valid.'}), 400

    tanggal = _parse_date(data.get('tanggal'))
    project_name = (data.get('project_name') or '').strip()

    if not tanggal or not project_name:
        return jsonify({'success': False, 'message': 'Tanggal dan project_name wajib diisi.'}), 400

    item = SupervisiLaporan(
        jenis=jenis,
        tanggal=tanggal,
        project_id=data.get('project_id'),
        project_name=project_name,
        lokasi=(data.get('lokasi') or '').strip() or None,
        waktu_lapor=(data.get('waktu_lapor') or '').strip() or None,
        judul=(data.get('judul') or '').strip() or None,
        catatan=(data.get('catatan') or '').strip() or None,
        created_by=session.get('user_id'),
    )

    db.session.add(item)
    db.session.flush()

    raw_items = data.get('items', [])
    for raw in raw_items:
        nama_item = (raw.get('nama_item') or '').strip()
        kategori = (raw.get('kategori') or '').strip()
        if not nama_item or not kategori:
            continue

        detail = SupervisiLaporanItem(
            laporan_id=item.id,
            segmen=(raw.get('segmen') or '').strip() or None,
            kategori=kategori,
            nama_item=nama_item,
            nilai=_to_float(raw.get('nilai')),
            satuan=(raw.get('satuan') or '').strip() or None,
        )
        db.session.add(detail)

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'CREATE', 'Supervisi',
              f'Membuat laporan {jenis}: {project_name} ({tanggal})')

    return jsonify({'success': True, 'message': 'Laporan berhasil dibuat.', 'data': item.to_dict()}), 201


@supervisi_bp.route('/laporan/<int:id>', methods=['PUT'])
@login_required
def update_laporan(id):
    if not _can_access_role():
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    item = SupervisiLaporan.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    tanggal = _parse_date(data.get('tanggal'))
    if tanggal:
        item.tanggal = tanggal

    if data.get('project_name'):
        item.project_name = data.get('project_name').strip()

    if 'project_id' in data:
        item.project_id = data.get('project_id')

    item.lokasi = (data.get('lokasi') or item.lokasi or '').strip() or None
    item.waktu_lapor = (data.get('waktu_lapor') or item.waktu_lapor or '').strip() or None
    item.judul = (data.get('judul') or item.judul or '').strip() or None
    item.catatan = (data.get('catatan') or item.catatan or '').strip() or None

    if isinstance(data.get('items'), list):
        SupervisiLaporanItem.query.filter_by(laporan_id=item.id).delete()
        for raw in data.get('items', []):
            nama_item = (raw.get('nama_item') or '').strip()
            kategori = (raw.get('kategori') or '').strip()
            if not nama_item or not kategori:
                continue
            db.session.add(SupervisiLaporanItem(
                laporan_id=item.id,
                segmen=(raw.get('segmen') or '').strip() or None,
                kategori=kategori,
                nama_item=nama_item,
                nilai=_to_float(raw.get('nilai')),
                satuan=(raw.get('satuan') or '').strip() or None,
            ))

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'UPDATE', 'Supervisi', f'Mengubah laporan ID {id}')

    return jsonify({'success': True, 'message': 'Laporan berhasil diperbarui.', 'data': item.to_dict()})


@supervisi_bp.route('/laporan/<int:id>', methods=['DELETE'])
@login_required
def delete_laporan(id):
    if not _can_access_role():
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    item = SupervisiLaporan.query.get_or_404(id)
    for foto in item.foto:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], foto.nama_file)
        if os.path.exists(filepath):
            os.remove(filepath)

    db.session.delete(item)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'DELETE', 'Supervisi', f'Menghapus laporan ID {id}')

    return jsonify({'success': True, 'message': 'Laporan berhasil dihapus.'})


@supervisi_bp.route('/laporan/<int:id>/foto', methods=['POST'])
@login_required
def upload_laporan_foto(id):
    if not _can_access_role():
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    item = SupervisiLaporan.query.get_or_404(id)

    if 'foto' not in request.files:
        return jsonify({'success': False, 'message': 'Tidak ada file yang dikirim.'}), 400

    files = request.files.getlist('foto')
    caption = (request.form.get('caption') or '').strip()
    added = []

    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        if not file or not _allowed_file(file.filename):
            continue

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        unique_name = f'supervisi_{item.id}_{timestamp}_{filename}'
        file.save(os.path.join(upload_dir, unique_name))

        foto = SupervisiLaporanFoto(
            laporan_id=item.id,
            nama_file=unique_name,
            caption=caption or None,
        )
        db.session.add(foto)
        added.append(foto)

    if not added:
        return jsonify({'success': False, 'message': 'Tidak ada foto valid.'}), 400

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'{len(added)} foto berhasil diupload.',
        'data': [f.to_dict() for f in added],
    }), 201


@supervisi_bp.route('/laporan/foto/<int:foto_id>', methods=['DELETE'])
@login_required
def delete_laporan_foto(foto_id):
    if not _can_access_role():
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    foto = SupervisiLaporanFoto.query.get_or_404(foto_id)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], foto.nama_file)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(foto)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Foto berhasil dihapus.'})


@supervisi_bp.route('/evidence', methods=['GET'])
@login_required
def get_evidence():
    if not _can_access_role():
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    project_id = request.args.get('project_id', type=int)
    tanggal = _parse_date(request.args.get('tanggal'))

    q = SupervisiLaporanFoto.query.join(SupervisiLaporan)

    if project_id:
        q = q.filter(SupervisiLaporan.project_id == project_id)
    if tanggal:
        q = q.filter(SupervisiLaporan.tanggal == tanggal)

    rows = q.order_by(SupervisiLaporan.tanggal.desc(), SupervisiLaporanFoto.created_at.desc()).all()

    data = []
    for row in rows:
        item = row.to_dict()
        item['laporan_id'] = row.laporan_id
        item['project_id'] = row.laporan.project_id
        item['project_name'] = row.laporan.project_name
        item['tanggal'] = row.laporan.tanggal.isoformat() if row.laporan.tanggal else None
        item['jenis'] = row.laporan.jenis
        data.append(item)

    return jsonify({'success': True, 'data': data})


@supervisi_bp.route('/evidence', methods=['POST'])
@login_required
def upload_evidence():
    if not _can_access_role():
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    project_name = (request.form.get('project_name') or '').strip()
    project_id = request.form.get('project_id', type=int)
    tanggal = _parse_date(request.form.get('tanggal'))
    caption = (request.form.get('caption') or '').strip()
    jenis = (request.form.get('jenis') or 'absen').strip()

    if jenis not in ('absen', 'laporan'):
        return jsonify({'success': False, 'message': 'Jenis evidence tidak valid.'}), 400

    if not project_name or not tanggal:
        return jsonify({'success': False, 'message': 'Project dan tanggal wajib diisi.'}), 400

    laporan = SupervisiLaporan.query.filter_by(
        jenis=jenis,
        tanggal=tanggal,
        project_id=project_id,
        project_name=project_name,
        created_by=session.get('user_id')
    ).order_by(SupervisiLaporan.id.desc()).first()

    if not laporan:
        laporan = SupervisiLaporan(
            jenis=jenis,
            tanggal=tanggal,
            project_id=project_id,
            project_name=project_name,
            judul=f'{"ABSEN" if jenis == "absen" else "LAPORAN"} {project_name}',
            created_by=session.get('user_id'),
        )
        db.session.add(laporan)
        db.session.flush()

    if 'foto' not in request.files:
        return jsonify({'success': False, 'message': 'Tidak ada file yang dikirim.'}), 400

    files = request.files.getlist('foto')
    added = []

    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        if not file or not _allowed_file(file.filename):
            continue

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        unique_name = f'evidence_{laporan.id}_{timestamp}_{filename}'
        file.save(os.path.join(upload_dir, unique_name))

        foto = SupervisiLaporanFoto(
            laporan_id=laporan.id,
            nama_file=unique_name,
            caption=caption or None,
        )
        db.session.add(foto)
        added.append(foto)

    if not added:
        return jsonify({'success': False, 'message': 'Tidak ada foto valid.'}), 400

    db.session.commit()

    return jsonify({'success': True, 'message': f'{len(added)} foto berhasil diupload.',
                    'data': [f.to_dict() for f in added], 'laporan_id': laporan.id}), 201
