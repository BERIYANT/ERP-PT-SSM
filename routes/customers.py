from flask import Blueprint, request, jsonify, session
from models import db, Customer, LogAktivitas
from routes.auth import login_required, catat_log

customers_bp = Blueprint('customers', __name__, url_prefix='/api/customers')


# ─── GET /api/customers ──────────────────────────────────────────────────────
@customers_bp.route('/', methods=['GET'])
@login_required
def get_customers():
    customers = Customer.query.order_by(Customer.name).all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in customers]
    })


# ─── GET /api/customers/<id> ─────────────────────────────────────────────────
@customers_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_customer(id):
    c = Customer.query.get_or_404(id)
    return jsonify({'success': True, 'data': c.to_dict()})


# ─── POST /api/customers ─────────────────────────────────────────────────────
@customers_bp.route('/', methods=['POST'])
@login_required
def create_customer():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Nama customer wajib diisi.'}), 400

    customer = Customer(
        name    = name,
        email   = data.get('email', '').strip() or None,
        phone   = data.get('phone', '').strip() or None,
        address = data.get('address', '').strip() or None,
    )
    db.session.add(customer)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'CREATE', 'Customer', f'Menambahkan customer: {name}')

    return jsonify({'success': True, 'message': 'Customer berhasil ditambahkan.',
                    'data': customer.to_dict()}), 201


# ─── PUT /api/customers/<id> ─────────────────────────────────────────────────
@customers_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_customer(id):
    c = Customer.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    c.name    = data.get('name', c.name).strip()
    c.email   = data.get('email', c.email)
    c.phone   = data.get('phone', c.phone)
    c.address = data.get('address', c.address)

    if not c.name:
        return jsonify({'success': False, 'message': 'Nama customer wajib diisi.'}), 400

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'UPDATE', 'Customer', f'Mengubah customer ID {id}: {c.name}')

    return jsonify({'success': True, 'message': 'Customer berhasil diperbarui.',
                    'data': c.to_dict()})


# ─── DELETE /api/customers/<id> ──────────────────────────────────────────────
@customers_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_customer(id):
    c = Customer.query.get_or_404(id)
    name = c.name
    db.session.delete(c)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'DELETE', 'Customer', f'Menghapus customer: {name}')

    return jsonify({'success': True, 'message': f'Customer "{name}" berhasil dihapus.'})
