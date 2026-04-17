from flask import Blueprint, request, jsonify, session, render_template
from models import db, Kasbon, User, Project
from datetime import datetime
from sqlalchemy import or_, and_

kasbon_bp = Blueprint('kasbon', __name__)


# ─── RENDER PAGE ───────────────────────────────────────────────────────────────
@kasbon_bp.route('/verifikasi-kasbon', methods=['GET'])
def verifikasi_kasbon_page():
    """Render verifikasi kasbon page"""
    if 'user_id' not in session:
        return render_template('login.html'), 401
    
    user = User.query.get(session['user_id'])
    return render_template('verifikasi kasbon.html', current_user=user)


@kasbon_bp.route('/pengajuan-kasbon', methods=['GET'])
def pengajuan_kasbon_page():
    """Render pengajuan kasbon page (untuk user biasa)"""
    if 'user_id' not in session:
        return render_template('login.html'), 401
    
    user = User.query.get(session['user_id'])
    return render_template('pengajuan_kasbon.html', current_user=user)


# ─── API ENDPOINTS ─────────────────────────────────────────────────────────────

# ─── GET All Kasbon ────────────────────────────────────────────────────────────
@kasbon_bp.route('/api/kasbon', methods=['GET'])
def get_kasbon_list():
    """Get all kasbon with filters"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        # Get query parameters
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')
        project_id = request.args.get('project_id', type=int)
        user_id = request.args.get('user_id', type=int)
        
        query = Kasbon.query
        
        # Apply filters
        if status and status != 'all':
            query = query.filter_by(status=status)
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Kasbon.tanggal_pengajuan >= start)
            except:
                pass
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Kasbon.tanggal_pengajuan <= end)
            except:
                pass
        
        if search:
            query = query.join(User, Kasbon.user_id == User.id).filter(
                or_(
                    User.nama.ilike(f'%{search}%'),
                    Kasbon.keperluan.ilike(f'%{search}%')
                )
            )
        
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        kasbon_list = query.order_by(Kasbon.tanggal_pengajuan.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [k.to_dict() for k in kasbon_list]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── GET Single Kasbon ─────────────────────────────────────────────────────────
@kasbon_bp.route('/api/kasbon/<int:kasbon_id>', methods=['GET'])
def get_kasbon(kasbon_id):
    """Get single kasbon detail"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        kasbon = Kasbon.query.get_or_404(kasbon_id)
        return jsonify({
            'success': True,
            'data': kasbon.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 404


# ─── CREATE Kasbon ─────────────────────────────────────────────────────────────
@kasbon_bp.route('/api/kasbon', methods=['POST'])
def create_kasbon():
    """Create new kasbon request"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        
        # Validation
        if not data.get('tanggal_pengajuan'):
            return jsonify({'success': False, 'message': 'Tanggal pengajuan harus diisi'}), 400
        
        if not data.get('jumlah'):
            return jsonify({'success': False, 'message': 'Jumlah harus diisi'}), 400
        
        if not data.get('keperluan'):
            return jsonify({'success': False, 'message': 'Keperluan harus diisi'}), 400
        
        # Parse tanggal
        try:
            tanggal = datetime.strptime(data['tanggal_pengajuan'], '%Y-%m-%d').date()
        except:
            return jsonify({'success': False, 'message': 'Format tanggal harus YYYY-MM-DD'}), 400
        
        kasbon = Kasbon(
            user_id=session['user_id'],
            project_id=data.get('project_id'),
            tanggal_pengajuan=tanggal,
            jumlah=float(data['jumlah']),
            keperluan=data['keperluan'],
            keterangan=data.get('keterangan'),
            status='pending'
        )
        
        db.session.add(kasbon)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kasbon berhasil diajukan',
            'data': kasbon.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── APPROVE Kasbon ────────────────────────────────────────────────────────────
@kasbon_bp.route('/api/kasbon/<int:kasbon_id>/approve', methods=['POST'])
def approve_kasbon(kasbon_id):
    """Approve kasbon request"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        kasbon = Kasbon.query.get_or_404(kasbon_id)
        
        if kasbon.status != 'pending':
            return jsonify({
                'success': False, 
                'message': 'Kasbon sudah diverifikasi sebelumnya'
            }), 400
        
        kasbon.status = 'approved'
        kasbon.tanggal_verifikasi = datetime.utcnow()
        kasbon.verified_by = session['user_id']
        kasbon.rejection_reason = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kasbon berhasil disetujui',
            'data': kasbon.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── REJECT Kasbon ─────────────────────────────────────────────────────────────
@kasbon_bp.route('/api/kasbon/<int:kasbon_id>/reject', methods=['POST'])
def reject_kasbon(kasbon_id):
    """Reject kasbon request"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        reason = data.get('reason', '')
        
        if not reason:
            return jsonify({
                'success': False, 
                'message': 'Alasan penolakan harus diisi'
            }), 400
        
        kasbon = Kasbon.query.get_or_404(kasbon_id)
        
        if kasbon.status != 'pending':
            return jsonify({
                'success': False, 
                'message': 'Kasbon sudah diverifikasi sebelumnya'
            }), 400
        
        kasbon.status = 'rejected'
        kasbon.tanggal_verifikasi = datetime.utcnow()
        kasbon.verified_by = session['user_id']
        kasbon.rejection_reason = reason
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kasbon berhasil ditolak',
            'data': kasbon.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── UPDATE Kasbon ─────────────────────────────────────────────────────────────
@kasbon_bp.route('/api/kasbon/<int:kasbon_id>', methods=['PUT'])
def update_kasbon(kasbon_id):
    """Update kasbon (only if still pending)"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        kasbon = Kasbon.query.get_or_404(kasbon_id)
        
        # Only allow update if kasbon is still pending and owned by current user
        if kasbon.user_id != session['user_id']:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if kasbon.status != 'pending':
            return jsonify({
                'success': False, 
                'message': 'Tidak dapat mengubah kasbon yang sudah diverifikasi'
            }), 400
        
        data = request.get_json()
        
        if data.get('tanggal_pengajuan'):
            try:
                kasbon.tanggal_pengajuan = datetime.strptime(
                    data['tanggal_pengajuan'], '%Y-%m-%d'
                ).date()
            except:
                return jsonify({
                    'success': False, 
                    'message': 'Format tanggal harus YYYY-MM-DD'
                }), 400
        
        if data.get('jumlah'):
            kasbon.jumlah = float(data['jumlah'])
        
        if data.get('keperluan'):
            kasbon.keperluan = data['keperluan']
        
        if 'keterangan' in data:
            kasbon.keterangan = data['keterangan']
        
        if 'project_id' in data:
            kasbon.project_id = data['project_id']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kasbon berhasil diupdate',
            'data': kasbon.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── DELETE Kasbon ─────────────────────────────────────────────────────────────
@kasbon_bp.route('/api/kasbon/<int:kasbon_id>', methods=['DELETE'])
def delete_kasbon(kasbon_id):
    """Delete kasbon (only if still pending and owned by user)"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        kasbon = Kasbon.query.get_or_404(kasbon_id)
        
        # Only allow delete if kasbon is still pending and owned by current user
        if kasbon.user_id != session['user_id']:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if kasbon.status != 'pending':
            return jsonify({
                'success': False, 
                'message': 'Tidak dapat menghapus kasbon yang sudah diverifikasi'
            }), 400
        
        db.session.delete(kasbon)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kasbon berhasil dihapus'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── GET Kasbon Summary ────────────────────────────────────────────────────────
@kasbon_bp.route('/api/kasbon/summary', methods=['GET'])
def get_kasbon_summary():
    """Get kasbon summary statistics"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        from sqlalchemy import func
        
        # Get counts by status
        pending = Kasbon.query.filter_by(status='pending').count()
        approved = Kasbon.query.filter_by(status='approved').count()
        rejected = Kasbon.query.filter_by(status='rejected').count()
        total = Kasbon.query.count()
        
        # Get total amount by status
        pending_amount = db.session.query(func.sum(Kasbon.jumlah)).filter_by(
            status='pending'
        ).scalar() or 0
        
        approved_amount = db.session.query(func.sum(Kasbon.jumlah)).filter_by(
            status='approved'
        ).scalar() or 0
        
        rejected_amount = db.session.query(func.sum(Kasbon.jumlah)).filter_by(
            status='rejected'
        ).scalar() or 0
        
        total_amount = db.session.query(func.sum(Kasbon.jumlah)).scalar() or 0
        
        return jsonify({
            'success': True,
            'data': {
                'counts': {
                    'pending': pending,
                    'approved': approved,
                    'rejected': rejected,
                    'total': total
                },
                'amounts': {
                    'pending': float(pending_amount),
                    'approved': float(approved_amount),
                    'rejected': float(rejected_amount),
                    'total': float(total_amount)
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
