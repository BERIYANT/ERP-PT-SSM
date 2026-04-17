import os
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from models import db, Setting, User, ProjectAssignment
from routes.auth import login_required, admin_required, catat_log

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')


# ══════════════════════════════════════════════════════════════
# SETTINGS (System Configuration) — Admin only
# ══════════════════════════════════════════════════════════════

@settings_bp.route('/', methods=['GET'])
@login_required
def get_settings():
    settings = Setting.query.all()
    result   = {s.kunci: s.nilai for s in settings}
    return jsonify({'success': True, 'data': result})


@settings_bp.route('/', methods=['PUT'])
@admin_required
def update_settings():
    data   = request.get_json(silent=True) or {}
    updated = []

    for kunci, nilai in data.items():
        setting = Setting.query.filter_by(kunci=kunci).first()
        if setting:
            setting.nilai = nilai
            updated.append(kunci)
        else:
            # Buat setting baru jika belum ada
            new_setting = Setting(kunci=kunci, nilai=nilai)
            db.session.add(new_setting)
            updated.append(kunci)

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'UPDATE', 'Settings',
              f'Mengubah {len(updated)} setting: {", ".join(updated)}')

    return jsonify({'success': True,
                    'message': 'Pengaturan berhasil disimpan.',
                    'updated': updated})


# ══════════════════════════════════════════════════════════════
# USER MANAGEMENT — Admin only
# ══════════════════════════════════════════════════════════════

@settings_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.order_by(User.nama).all()
    return jsonify({'success': True, 'data': [u.to_dict() for u in users]})


@settings_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    data     = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    nama     = (data.get('nama') or '').strip()

    if not username or not password or not nama:
        return jsonify({'success': False,
                        'message': 'Username, password, dan nama wajib diisi.'}), 400

    if len(password) < 6:
        return jsonify({'success': False,
                        'message': 'Password minimal 6 karakter.'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False,
                        'message': 'Username sudah digunakan.'}), 409

    user = User(
        username = username,
        nama     = nama,
        email    = data.get('email', '').strip() or None,
        role     = data.get('role', 'user'),
        phone    = data.get('phone', '').strip() or None,
        jabatan  = data.get('jabatan', '').strip() or None,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'CREATE', 'User', f'Membuat user baru: {username}')

    return jsonify({'success': True,
                    'message': 'User berhasil dibuat.',
                    'data': user.to_dict()}), 201


@settings_bp.route('/users/<int:id>', methods=['PUT'])
@admin_required
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    user.nama     = data.get('nama', user.nama)
    user.email    = data.get('email', user.email)
    user.role     = data.get('role', user.role)
    user.phone    = data.get('phone', user.phone)
    user.jabatan  = data.get('jabatan', user.jabatan)
    user.is_active = data.get('is_active', user.is_active)

    if data.get('password'):
        if len(data['password']) < 6:
            return jsonify({'success': False,
                            'message': 'Password minimal 6 karakter.'}), 400
        user.set_password(data['password'])

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'UPDATE', 'User', f'Mengubah user: {user.username}')

    return jsonify({'success': True, 'message': 'User berhasil diperbarui.',
                    'data': user.to_dict()})


@settings_bp.route('/users/<int:id>', methods=['DELETE'])
@admin_required
def delete_user(id):
    if id == session.get('user_id'):
        return jsonify({'success': False,
                        'message': 'Tidak dapat menghapus akun Anda sendiri.'}), 400

    user = User.query.get_or_404(id)
    uname = user.username
    db.session.delete(user)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'DELETE', 'User', f'Menghapus user: {uname}')

    return jsonify({'success': True, 'message': f'User {uname} berhasil dihapus.'})


# ══════════════════════════════════════════════════════════════
# PROJECT ASSIGNMENTS — Admin only
# ══════════════════════════════════════════════════════════════

@settings_bp.route('/assignments', methods=['GET'])
@admin_required
def get_assignments():
    assignments = ProjectAssignment.query.all()
    grouped = {}
    for a in assignments:
        if a.user_id not in grouped:
            grouped[a.user_id] = []
        grouped[a.user_id].append(a.project_id)
        
    result = [{'userId': uid, 'projectIds': pids} for uid, pids in grouped.items()]
    return jsonify({'success': True, 'data': result})


@settings_bp.route('/assignments', methods=['POST'])
@admin_required
def set_assignments():
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId')
    project_ids = data.get('projectIds', [])

    if not user_id:
        return jsonify({'success': False, 'message': 'User ID required.'}), 400

    ProjectAssignment.query.filter_by(user_id=user_id).delete()
    
    added = 0
    for pid in project_ids:
        pa = ProjectAssignment(user_id=user_id, project_id=pid)
        db.session.add(pa)
        added += 1
        
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'UPDATE', 'Project Assignment', f'Menetapkan {added} project ke user ID {user_id}')

    return jsonify({'success': True, 'message': 'Assignment berhasil disimpan.'})


# ══════════════════════════════════════════════════════════════
# PROFILE — Current logged-in user
# ══════════════════════════════════════════════════════════════

@settings_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    user = User.query.get_or_404(session['user_id'])
    return jsonify({'success': True, 'data': user.to_dict()})


@settings_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    user = User.query.get_or_404(session['user_id'])
    data = request.get_json(silent=True) or {}

    user.nama    = data.get('nama', user.nama)
    user.email   = data.get('email', user.email)
    user.phone   = data.get('phone', user.phone)
    user.jabatan = data.get('jabatan', user.jabatan)

    db.session.commit()

    # Update session
    session['nama'] = user.nama

    catat_log(user.id, user.username,
              'UPDATE', 'Profile', f'User {user.username} memperbarui profil')

    return jsonify({'success': True, 'message': 'Profil berhasil diperbarui.',
                    'data': user.to_dict()})


@settings_bp.route('/profile/avatar', methods=['POST'])
@login_required
def upload_avatar():
    user = User.query.get_or_404(session['user_id'])

    if 'avatar' not in request.files:
        return jsonify({'success': False, 'message': 'Tidak ada file yang dikirim.'}), 400

    file = request.files['avatar']
    if not file or not file.filename:
        return jsonify({'success': False, 'message': 'File tidak valid.'}), 400

    allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in allowed:
        return jsonify({'success': False,
                        'message': 'Format file tidak didukung. Gunakan PNG/JPG/JPEG.'}), 400

    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    filename  = f'avatar_{user.id}.{ext}'
    save_path = os.path.join(upload_dir, filename)
    file.save(save_path)

    user.avatar = f'/static/uploads/{filename}'
    db.session.commit()
    session['avatar'] = user.avatar

    return jsonify({'success': True,
                    'message': 'Avatar berhasil diperbarui.',
                    'avatar': user.avatar})
