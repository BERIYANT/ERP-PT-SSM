from datetime import datetime
from flask import Blueprint, request, jsonify, session
from models import db, OverheadKantor
from routes.auth import login_required, catat_log

overhead_bp = Blueprint('overhead', __name__, url_prefix='/api/overhead')


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


# ─── GET /api/overhead ───────────────────────────────────────────────────────
@overhead_bp.route('/', methods=['GET'])
@login_required
def get_overhead():
    tanggal_dari = request.args.get('dari')
    tanggal_ke   = request.args.get('ke')
    kategori     = request.args.get('kategori')

    q = OverheadKantor.query

    if tanggal_dari:
        tgl = _parse_date(tanggal_dari)
        if tgl:
            q = q.filter(OverheadKantor.tanggal >= tgl)
    if tanggal_ke:
        tgl = _parse_date(tanggal_ke)
        if tgl:
            q = q.filter(OverheadKantor.tanggal <= tgl)
    if kategori:
        q = q.filter(OverheadKantor.kategori.ilike(f'%{kategori}%'))

    items = q.order_by(OverheadKantor.tanggal.desc()).all()

    total = sum(float(i.jumlah) for i in items)

    return jsonify({
        'success': True,
        'data':    [i.to_dict() for i in items],
        'total':   total,
    })


# ─── GET /api/overhead/<id> ──────────────────────────────────────────────────
@overhead_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_item(id):
    item = OverheadKantor.query.get_or_404(id)
    return jsonify({'success': True, 'data': item.to_dict()})


# ─── POST /api/overhead ──────────────────────────────────────────────────────
@overhead_bp.route('/', methods=['POST'])
@login_required
def create_item():
    data = request.get_json(silent=True) or {}

    tanggal  = _parse_date(data.get('tanggal'))
    kategori = (data.get('kategori') or '').strip()
    jumlah   = float(data.get('jumlah', 0) or 0)

    if not tanggal or not kategori:
        return jsonify({'success': False,
                        'message': 'Tanggal dan kategori wajib diisi.'}), 400

    if jumlah <= 0:
        return jsonify({'success': False,
                        'message': 'Jumlah harus lebih dari 0.'}), 400

    item = OverheadKantor(
        tanggal    = tanggal,
        kategori   = kategori,
        deskripsi  = data.get('deskripsi', '').strip() or None,
        jumlah     = jumlah,
        keterangan = data.get('keterangan', '').strip() or None,
        created_by = session.get('user_id'),
    )
    db.session.add(item)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'CREATE', 'Overhead', f'Menambahkan overhead: {kategori} Rp {jumlah:,.0f}')

    return jsonify({'success': True,
                    'message': 'Data overhead berhasil ditambahkan.',
                    'data': item.to_dict()}), 201


# ─── PUT /api/overhead/<id> ──────────────────────────────────────────────────
@overhead_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_item(id):
    item = OverheadKantor.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    tgl = _parse_date(data.get('tanggal'))
    if tgl:
        item.tanggal = tgl

    item.kategori   = data.get('kategori', item.kategori)
    item.deskripsi  = data.get('deskripsi', item.deskripsi)
    item.jumlah     = float(data.get('jumlah', item.jumlah) or item.jumlah)
    item.keterangan = data.get('keterangan', item.keterangan)

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'UPDATE', 'Overhead', f'Mengubah overhead ID {id}')

    return jsonify({'success': True, 'message': 'Data overhead berhasil diperbarui.',
                    'data': item.to_dict()})


# ─── DELETE /api/overhead/<id> ───────────────────────────────────────────────
@overhead_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_item(id):
    item = OverheadKantor.query.get_or_404(id)
    deskripsi = item.deskripsi or item.kategori
    db.session.delete(item)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'DELETE', 'Overhead', f'Menghapus overhead: {deskripsi}')

    return jsonify({'success': True,
                    'message': 'Data overhead berhasil dihapus.'})


# ─── GET /api/overhead/kategori ──────────────────────────────────────────────
@overhead_bp.route('/kategori', methods=['GET'])
@login_required
def get_kategori():
    """Daftar kategori unik yang sudah pernah digunakan."""
    from sqlalchemy import distinct
    rows = db.session.query(distinct(OverheadKantor.kategori)).all()
    return jsonify({'success': True, 'data': [r[0] for r in rows]})


# ─── GET /api/overhead/summary ───────────────────────────────────────────────
@overhead_bp.route('/summary', methods=['GET'])
@login_required
def summary():
    from sqlalchemy import func
    bulan = request.args.get('bulan')   # format: YYYY-MM
    q = db.session.query(
        OverheadKantor.kategori,
        func.sum(OverheadKantor.jumlah).label('total')
    )
    if bulan:
        try:
            tahun, bln = bulan.split('-')
            q = q.filter(
                func.year(OverheadKantor.tanggal) == int(tahun),
                func.month(OverheadKantor.tanggal) == int(bln)
            )
        except Exception:
            pass
    rows = q.group_by(OverheadKantor.kategori).all()

    return jsonify({
        'success': True,
        'data': [{'kategori': r.kategori, 'total': float(r.total)} for r in rows]
    })
