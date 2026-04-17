from flask import Blueprint, request, jsonify, session
from models import db, Material, ProjectRAB

materials_bp = Blueprint('materials', __name__, url_prefix='/api/materials')


# ─── GET Budget ────────────────────────────────────────────────────────────────
@materials_bp.route('/budget', methods=['GET'])
def get_budget():
    """Get material budget directly from project RAB (same as dashboard project)"""
    try:
        project_id = request.args.get('project_id', type=int)
        
        # Langsung ambil dari ProjectRAB kategori 'material' (sama seperti dashboard project)
        if project_id:
            from sqlalchemy import func
            rab_budget = db.session.query(
                func.sum(ProjectRAB.total)
            ).filter(
                ProjectRAB.project_id == project_id,
                ProjectRAB.kategori == 'material'
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


# ─── GET All Materials ────────────────────────────────────────────────────────
@materials_bp.route('', methods=['GET'])
def get_materials():
    """Get all materials, optionally filter by source"""
    try:
        source = request.args.get('source')  # 'gudang' atau 'lapangan'
        project_id = request.args.get('project_id', type=int)
        
        query = Material.query
        if source:
            query = query.filter_by(source=source)
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        materials = query.all()
        return jsonify({
            'success': True,
            'data': [m.to_dict() for m in materials]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── GET Single Material ──────────────────────────────────────────────────────
@materials_bp.route('/<int:material_id>', methods=['GET'])
def get_material(material_id):
    """Get single material by ID"""
    try:
        material = Material.query.get_or_404(material_id)
        return jsonify({
            'success': True,
            'data': material.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 404


# ─── CREATE Material ──────────────────────────────────────────────────────────
@materials_bp.route('', methods=['POST'])
def create_material():
    """Create new material"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'success': False, 'message': 'Nama material harus diisi'}), 400
        
        if not data.get('price'):
            return jsonify({'success': False, 'message': 'Harga harus diisi'}), 400
        
        material = Material(
            project_id=data.get('project_id'),
            name=data.get('name'),
            price=float(data.get('price', 0)),
            source=data.get('source', 'gudang'),
            used=data.get('used', False),
            created_by=session.get('user_id')
        )
        
        db.session.add(material)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Material berhasil ditambahkan',
            'data': material.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── UPDATE Material ──────────────────────────────────────────────────────────
@materials_bp.route('/<int:material_id>', methods=['PUT'])
def update_material(material_id):
    """Update material"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        material = Material.query.get_or_404(material_id)
        data = request.get_json()
        
        if 'name' in data:
            material.name = data['name']
        if 'project_id' in data:
            material.project_id = data['project_id']
        if 'price' in data:
            material.price = float(data['price'])
        if 'source' in data:
            material.source = data['source']
        if 'used' in data:
            material.used = data['used']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Material berhasil diupdate',
            'data': material.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── MOVE Material (Gudang → Lapangan atau sebaliknya) ──────────────────────
@materials_bp.route('/<int:material_id>/move', methods=['PUT'])
def move_material(material_id):
    """Move material between sources (gudang ↔ lapangan)"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        material = Material.query.get_or_404(material_id)
        data = request.get_json(silent=True) or {}
        project_id = data.get('project_id')
        
        # Jika di gudang, pindah ke lapangan dan tandai sebagai dipakai
        if material.source == 'gudang':
            if not project_id:
                return jsonify({'success': False, 'message': 'Project wajib dipilih untuk memindahkan material ke lapangan'}), 400
            material.source = 'lapangan'
            material.used = True
            material.project_id = int(project_id)
        # Jika di lapangan, pindah kembali ke gudang dan tandai tidak dipakai
        elif material.source == 'lapangan':
            material.source = 'gudang'
            material.used = False
            material.project_id = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Material dipindahkan ke {material.source}',
            'data': material.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── DELETE Material ──────────────────────────────────────────────────────────
@materials_bp.route('/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    """Delete material"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        material = Material.query.get_or_404(material_id)
        
        db.session.delete(material)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Material berhasil dihapus'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
