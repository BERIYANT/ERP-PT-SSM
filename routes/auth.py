from flask import Blueprint, request, jsonify, session
from models import db, User, LogAktivitas
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# ─── Helper: catat log ────────────────────────────────────────────────────────
def catat_log(user_id, username, aksi, modul, deskripsi):
    try:
        ip = request.remote_addr
        log = LogAktivitas(
            user_id=user_id, username=username,
            aksi=aksi, modul=modul, deskripsi=deskripsi,
            ip_address=ip
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass


# ─── Decorator: login required ───────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized. Silakan login terlebih dahulu.'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized.'}), 401
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Forbidden. Hanya admin yang dapat mengakses ini.'}), 403
        return f(*args, **kwargs)
    return decorated


# ─── POST /api/auth/login ────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username dan password wajib diisi.'}), 400

    user = User.query.filter_by(username=username, is_active=True).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Username atau password salah.'}), 401

    session.permanent = True
    session['user_id']  = user.id
    session['username'] = user.username
    session['nama']     = user.nama
    session['role']     = user.role
    session['avatar']   = user.avatar or ''

    catat_log(user.id, user.username, 'LOGIN', 'Auth',
              f'User {user.username} berhasil login dari {request.remote_addr}')

    return jsonify({
        'success': True,
        'message': 'Login berhasil.',
        'user': {
            'id':       user.id,
            'username': user.username,
            'nama':     user.nama,
            'role':     user.role,
            'avatar':   user.avatar,
            'jabatan':  user.jabatan,
        }
    })


# ─── POST /api/auth/logout ───────────────────────────────────────────────────
@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    username = session.get('username')
    user_id  = session.get('user_id')
    catat_log(user_id, username, 'LOGOUT', 'Auth',
              f'User {username} logout')
    session.clear()
    return jsonify({'success': True, 'message': 'Logout berhasil.'})


# ─── GET /api/auth/me ────────────────────────────────────────────────────────
@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return jsonify({'success': False, 'message': 'User tidak ditemukan.'}), 404
    return jsonify({'success': True, 'user': user.to_dict()})


# ─── POST /api/auth/change-password ─────────────────────────────────────────
@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    old_pw  = data.get('old_password', '')
    new_pw  = data.get('new_password', '')
    conf_pw = data.get('confirm_password', '')

    if not old_pw or not new_pw or not conf_pw:
        return jsonify({'success': False, 'message': 'Semua field wajib diisi.'}), 400

    if new_pw != conf_pw:
        return jsonify({'success': False, 'message': 'Konfirmasi password tidak cocok.'}), 400

    if len(new_pw) < 6:
        return jsonify({'success': False, 'message': 'Password minimal 6 karakter.'}), 400

    user = User.query.get(session['user_id'])
    if not user.check_password(old_pw):
        return jsonify({'success': False, 'message': 'Password lama tidak sesuai.'}), 400

    user.set_password(new_pw)
    db.session.commit()

    catat_log(user.id, user.username, 'CHANGE_PASSWORD', 'Auth',
              f'User {user.username} mengganti password')

    return jsonify({'success': True, 'message': 'Password berhasil diubah.'})
