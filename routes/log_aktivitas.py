from flask import Blueprint, request, jsonify, session
from models import db, LogAktivitas
from routes.auth import login_required, admin_required

log_bp = Blueprint('log', __name__, url_prefix='/api/log')

from models import User

# ─── GET /api/log ─────────────────────────────────────────────────────────────
@log_bp.route('/', methods=['GET'])
@login_required
def get_log():
    modul    = request.args.get('modul')
    aksi     = request.args.get('aksi')
    username = request.args.get('username')
    role     = request.args.get('role')
    dari     = request.args.get('dari')
    ke       = request.args.get('ke')
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    q = db.session.query(LogAktivitas, User).outerjoin(User, LogAktivitas.user_id == User.id)

    if modul:
        q = q.filter(LogAktivitas.modul.ilike(f'%{modul}%'))
    if aksi and aksi != 'all':
        q = q.filter(LogAktivitas.aksi.ilike(f'%{aksi}%'))
    if username and username != 'all':
        q = q.filter(LogAktivitas.username.ilike(f'%{username}%'))
    if role and role != 'all':
        q = q.filter(User.role == role.lower())
        
    if dari:
        from datetime import datetime
        try:
            tgl = datetime.strptime(dari, '%Y-%m-%d')
            q = q.filter(LogAktivitas.created_at >= tgl)
        except ValueError:
            pass
    if ke:
        from datetime import datetime
        try:
            tgl = datetime.strptime(ke + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            q = q.filter(LogAktivitas.created_at <= tgl)
        except ValueError:
            pass

    # Build stats grouped by aksi before pagination occurs
    stats_req = q.with_entities(LogAktivitas.aksi, db.func.count(LogAktivitas.id)).group_by(LogAktivitas.aksi).all()
    stats = {row[0].lower() if row[0] else 'unknown': row[1] for row in stats_req}

    paginated = q.order_by(LogAktivitas.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    data = []
    for log, user in paginated.items:
        ldict = log.to_dict()
        ldict['role'] = user.role.capitalize() if user and user.role else 'User'
        ldict['nama'] = user.nama if user else log.username
        data.append(ldict)

    return jsonify({
        'success':   True,
        'data':      data,
        'stats':     stats,
        'total':     paginated.total,
        'pages':     paginated.pages,
        'page':      paginated.page,
        'per_page':  per_page,
    })


# ─── DELETE /api/log (admin only, hapus semua log lama) ──────────────────────
@log_bp.route('/clear', methods=['DELETE'])
@admin_required
def clear_log():
    days = request.args.get('days', 90, type=int)
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    count = LogAktivitas.query.filter(LogAktivitas.created_at < cutoff).delete()
    db.session.commit()
    return jsonify({'success': True,
                    'message': f'{count} log aktivitas yang lebih dari {days} hari berhasil dihapus.'})


# ─── GET /api/log/modules ─────────────────────────────────────────────────────
@log_bp.route('/modules', methods=['GET'])
@login_required
def get_modules():
    from sqlalchemy import distinct
    rows = db.session.query(distinct(LogAktivitas.modul)).filter(
        LogAktivitas.modul.isnot(None)
    ).all()
    return jsonify({'success': True, 'data': [r[0] for r in rows]})


# ─── GET /api/log/users ─────────────────────────────────────────────────────
@log_bp.route('/users', methods=['GET'])
@login_required
def get_log_users():
    from sqlalchemy import distinct
    rows = db.session.query(distinct(LogAktivitas.username)).filter(
        LogAktivitas.username.isnot(None)
    ).all()
    return jsonify({'success': True, 'data': [r[0] for r in rows]})
