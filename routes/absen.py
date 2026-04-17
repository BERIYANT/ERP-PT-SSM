import os
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from models import db, Absen, AbsenDetail, AbsenFoto
from routes.auth import login_required, catat_log

absen_bp = Blueprint('absen', __name__, url_prefix='/api/absen')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── GET /api/absen ──────────────────────────────────────────────────────────
@absen_bp.route('/', methods=['GET'])
@login_required
def get_absen():
    tanggal     = request.args.get('tanggal')
    project_id  = request.args.get('project_id', type=int)
    dari        = request.args.get('dari')
    ke          = request.args.get('ke')

    q = Absen.query

    if tanggal:
        tgl = _parse_date(tanggal)
        if tgl:
            q = q.filter_by(tanggal=tgl)
    else:
        if dari:
            tgl = _parse_date(dari)
            if tgl:
                q = q.filter(Absen.tanggal >= tgl)
        if ke:
            tgl = _parse_date(ke)
            if tgl:
                q = q.filter(Absen.tanggal <= tgl)

    if project_id:
        q = q.filter_by(project_id=project_id)

    items = q.order_by(Absen.tanggal.desc(), Absen.created_at.desc()).all()
    return jsonify({'success': True, 'data': [i.to_dict() for i in items]})


# ─── GET /api/absen/<id> ─────────────────────────────────────────────────────
@absen_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_item(id):
    item = Absen.query.get_or_404(id)
    return jsonify({'success': True, 'data': item.to_dict()})


# ─── POST /api/absen ─────────────────────────────────────────────────────────
@absen_bp.route('/', methods=['POST'])
@login_required
def create_absen():
    data = request.get_json(silent=True) or {}

    tanggal      = _parse_date(data.get('tanggal'))
    project_name = (data.get('project_name') or '').strip()

    if not tanggal or not project_name:
        return jsonify({'success': False,
                        'message': 'Tanggal dan project_name wajib diisi.'}), 400

    absen = Absen(
        tanggal      = tanggal,
        project_id   = data.get('project_id'),
        project_name = project_name,
        segmen       = data.get('segmen', '').strip() or None,
        waktu_lapor  = data.get('waktu_lapor', '').strip() or None,
        deskripsi    = data.get('deskripsi', '').strip() or None,
        created_by   = session.get('user_id'),
    )
    db.session.add(absen)
    db.session.flush()  # dapatkan absen.id sebelum commit

    # Tambahkan detail jika ada
    detail_list = data.get('detail', [])
    for d in detail_list:
        detail = AbsenDetail(
            absen_id = absen.id,
            kategori = d.get('kategori', 'info'),
            label    = d.get('label', ''),
            nilai    = d.get('nilai'),
            satuan   = d.get('satuan'),
        )
        db.session.add(detail)

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'CREATE', 'Absen',
              f'Menambahkan laporan absen: {project_name} tgl {tanggal}')

    return jsonify({'success': True,
                    'message': 'Laporan absen berhasil ditambahkan.',
                    'data': absen.to_dict()}), 201


# ─── PUT /api/absen/<id> ─────────────────────────────────────────────────────
@absen_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_absen(id):
    absen = Absen.query.get_or_404(id)
    data  = request.get_json(silent=True) or {}

    tgl = _parse_date(data.get('tanggal'))
    if tgl:
        absen.tanggal = tgl

    absen.project_name = data.get('project_name', absen.project_name)
    absen.segmen       = data.get('segmen', absen.segmen)
    absen.waktu_lapor  = data.get('waktu_lapor', absen.waktu_lapor)
    absen.deskripsi    = data.get('deskripsi', absen.deskripsi)

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'UPDATE', 'Absen', f'Mengubah laporan absen ID {id}')

    return jsonify({'success': True, 'message': 'Laporan absen berhasil diperbarui.',
                    'data': absen.to_dict()})


# ─── DELETE /api/absen/<id> ──────────────────────────────────────────────────
@absen_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_absen(id):
    absen = Absen.query.get_or_404(id)
    project_name = absen.project_name
    db.session.delete(absen)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'DELETE', 'Absen', f'Menghapus laporan absen: {project_name}')

    return jsonify({'success': True, 'message': 'Laporan absen berhasil dihapus.'})


# ─── POST /api/absen/<id>/foto ───────────────────────────────────────────────
@absen_bp.route('/<int:id>/foto', methods=['POST'])
@login_required
def upload_foto(id):
    absen = Absen.query.get_or_404(id)

    if 'foto' not in request.files:
        return jsonify({'success': False, 'message': 'Tidak ada file yang dikirim.'}), 400

    files   = request.files.getlist('foto')
    caption = request.form.get('caption', '')
    added   = []

    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        if file and _allowed_file(file.filename):
            filename  = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_fn = f'absen_{absen.id}_{timestamp}_{filename}'
            file.save(os.path.join(upload_dir, unique_fn))

            foto = AbsenFoto(
                absen_id  = absen.id,
                nama_file = unique_fn,
                caption   = caption or None,
            )
            db.session.add(foto)
            added.append(foto)

    if not added:
        return jsonify({'success': False,
                        'message': 'Tidak ada file foto yang valid.'}), 400

    db.session.commit()
    return jsonify({'success': True,
                    'message': f'{len(added)} foto berhasil diupload.',
                    'data': [f.to_dict() for f in added]}), 201


# ─── DELETE /api/absen/foto/<foto_id> ────────────────────────────────────────
@absen_bp.route('/foto/<int:foto_id>', methods=['DELETE'])
@login_required
def delete_foto(foto_id):
    foto = AbsenFoto.query.get_or_404(foto_id)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], foto.nama_file)

    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(foto)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Foto berhasil dihapus.'})
