from flask import Blueprint, request, jsonify, session
from models import db, PettyCash, ProjectRAB
from datetime import datetime

petty_cash_bp = Blueprint('petty_cash', __name__, url_prefix='/api/petty-cash')


# ─── GET All Petty Cash ────────────────────────────────────────────────────────
@petty_cash_bp.route('', methods=['GET'])
def get_petty_cash_list():
    """Get all petty cash transactions"""
    try:
        kategori = request.args.get('kategori')
        project_id = request.args.get('project_id', type=int)
        
        query = PettyCash.query
        if kategori:
            query = query.filter_by(kategori=kategori)
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        transactions = query.order_by(PettyCash.tanggal.desc()).all()
        return jsonify({
            'success': True,
            'data': [t.to_dict() for t in transactions]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── GET Single Petty Cash ────────────────────────────────────────────────────
@petty_cash_bp.route('/<int:petty_cash_id>', methods=['GET'])
def get_petty_cash(petty_cash_id):
    """Get single petty cash transaction"""
    try:
        transaction = PettyCash.query.get_or_404(petty_cash_id)
        return jsonify({
            'success': True,
            'data': transaction.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 404


# ─── CREATE Petty Cash ────────────────────────────────────────────────────────
@petty_cash_bp.route('', methods=['POST'])
def create_petty_cash():
    """Create new petty cash transaction"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        
        if not data.get('tanggal'):
            return jsonify({'success': False, 'message': 'Tanggal harus diisi'}), 400
        
        if not data.get('kategori'):
            return jsonify({'success': False, 'message': 'Kategori harus diisi'}), 400
        
        if not data.get('jumlah'):
            return jsonify({'success': False, 'message': 'Jumlah harus diisi'}), 400
        
        # Parse tanggal
        try:
            tanggal = datetime.strptime(data['tanggal'], '%Y-%m-%d').date()
        except:
            return jsonify({'success': False, 'message': 'Format tanggal harus YYYY-MM-DD'}), 400
        
        transaction = PettyCash(
            project_id=data.get('project_id'),
            tanggal=tanggal,
            kategori=data.get('kategori'),
            deskripsi=data.get('deskripsi'),
            jumlah=float(data.get('jumlah', 0)),
            keterangan=data.get('keterangan'),
            created_by=session.get('user_id')
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Petty Cash berhasil ditambahkan',
            'data': transaction.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── UPDATE Petty Cash ────────────────────────────────────────────────────────
@petty_cash_bp.route('/<int:petty_cash_id>', methods=['PUT'])
def update_petty_cash(petty_cash_id):
    """Update petty cash transaction"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        transaction = PettyCash.query.get_or_404(petty_cash_id)
        data = request.get_json()
        
        if 'tanggal' in data:
            try:
                transaction.tanggal = datetime.strptime(data['tanggal'], '%Y-%m-%d').date()
            except:
                return jsonify({'success': False, 'message': 'Format tanggal harus YYYY-MM-DD'}), 400
        
        if 'project_id' in data:
            transaction.project_id = data['project_id']
        if 'kategori' in data:
            transaction.kategori = data['kategori']
        if 'deskripsi' in data:
            transaction.deskripsi = data['deskripsi']
        if 'jumlah' in data:
            transaction.jumlah = float(data['jumlah'])
        if 'keterangan' in data:
            transaction.keterangan = data['keterangan']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Petty Cash berhasil diupdate',
            'data': transaction.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── DELETE Petty Cash ────────────────────────────────────────────────────────
@petty_cash_bp.route('/<int:petty_cash_id>', methods=['DELETE'])
def delete_petty_cash(petty_cash_id):
    """Delete petty cash transaction"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        transaction = PettyCash.query.get_or_404(petty_cash_id)
        
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Petty Cash berhasil dihapus'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── GET Summary (Total by Kategori) ───────────────────────────────────────────
@petty_cash_bp.route('/summary/by-category', methods=['GET'])
def get_petty_cash_summary():
    """Get total petty cash grouped by kategori"""
    try:
        from sqlalchemy import func
        project_id = request.args.get('project_id', type=int)
        
        query = db.session.query(
            PettyCash.kategori,
            func.sum(PettyCash.jumlah).label('total')
        )
        if project_id:
            query = query.filter(PettyCash.project_id == project_id)

        summary = query.group_by(PettyCash.kategori).all()
        
        data = [{'kategori': s[0], 'total': float(s[1]) if s[1] else 0} for s in summary]
        grand_total = sum(s['total'] for s in data)
        
        return jsonify({
            'success': True,
            'data': data,
            'grand_total': grand_total
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── GET Budget ────────────────────────────────────────────────────────────────
@petty_cash_bp.route('/budget', methods=['GET'])
def get_budget():
    """Get petty cash budget directly from project RAB (same as dashboard project)"""
    try:
        project_id = request.args.get('project_id', type=int)
        
        # Langsung ambil dari ProjectRAB kategori 'patty_cash' (sama seperti dashboard project)
        if project_id:
            from sqlalchemy import func
            rab_budget = db.session.query(
                func.sum(ProjectRAB.total)
            ).filter(
                ProjectRAB.project_id == project_id,
                ProjectRAB.kategori == 'patty_cash'
            ).scalar()
            
            if rab_budget and float(rab_budget) > 0:
                return jsonify({
                    'success': True,
                    'budget': float(rab_budget),
                    'source': 'rab'
                })
        
        # No budget found
        return jsonify({
            'success': True,
            'budget': 0,
            'source': 'none'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── SET Budget ────────────────────────────────────────────────────────────────
@petty_cash_bp.route('/budget', methods=['POST'])
def set_budget():
    """Budget is now read-only from Project RAB - no manual editing needed"""
    try:
        return jsonify({
            'success': False,
            'message': 'Budget otomatis diambil dari Project RAB kategori Petty Cash. Edit budget melalui RAB Project.'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
