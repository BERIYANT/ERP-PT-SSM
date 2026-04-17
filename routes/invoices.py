from datetime import datetime
from flask import Blueprint, request, jsonify, session
from models import db, Invoice
from routes.auth import login_required, catat_log

invoices_bp = Blueprint('invoices', __name__, url_prefix='/api/invoices')


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


# ─── GET /api/invoices ───────────────────────────────────────────────────────
@invoices_bp.route('/', methods=['GET'])
@login_required
def get_invoices():
    customer_name = request.args.get('customer')
    is_additional = request.args.get('is_additional')
    is_archived   = request.args.get('is_archived', 'false').lower() == 'true'

    q = Invoice.query.filter_by(is_archived=is_archived)
    if customer_name:
        q = q.filter(Invoice.customer_name.ilike(f'%{customer_name}%'))
    if is_additional is not None:
        q = q.filter_by(is_additional=(is_additional.lower() == 'true'))

    invoices = q.order_by(Invoice.created_at.desc()).all()

    # Group by customer
    grouped = {}
    for inv in invoices:
        key = inv.customer_name
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(inv.to_dict())

    return jsonify({'success': True, 'data': invoices_to_list(invoices), 'grouped': grouped})


def invoices_to_list(invoices):
    return [i.to_dict() for i in invoices]


# ─── GET /api/invoices/<id> ──────────────────────────────────────────────────
@invoices_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_invoice(id):
    inv = Invoice.query.get_or_404(id)
    return jsonify({'success': True, 'data': inv.to_dict()})


# ─── POST /api/invoices ──────────────────────────────────────────────────────
@invoices_bp.route('/', methods=['POST'])
@login_required
def create_invoice():
    data = request.get_json(silent=True) or {}

    # Support bulk creation (list) or single object
    items = data if isinstance(data, list) else [data]
    added = []

    for item in items:
        customer_name = (item.get('customer_name') or '').strip()
        po_number     = (item.get('po_number') or '').strip()
        if not customer_name or not po_number:
            continue

        inv = Invoice(
            customer_name = customer_name,
            po_number     = po_number,
            po_date       = _parse_date(item.get('po_date')),
            description   = item.get('description', '').strip() or None,
            amount        = float(item.get('amount', 0) or 0),
            is_additional = bool(item.get('is_additional', False)),
            project_id    = item.get('project_id'),
            created_by    = session.get('user_id'),
        )
        db.session.add(inv)
        added.append(inv)

    if not added:
        return jsonify({'success': False,
                        'message': 'Tidak ada data invoice yang valid.'}), 400

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'CREATE', 'Invoice',
              f'Menambahkan {len(added)} invoice untuk '
              f'{added[0].customer_name if added else ""}')

    return jsonify({
        'success': True,
        'message': f'{len(added)} invoice berhasil ditambahkan.',
        'data': [i.to_dict() for i in added]
    }), 201


# ─── PUT /api/invoices/<id> ──────────────────────────────────────────────────
@invoices_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_invoice(id):
    inv  = Invoice.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    inv.customer_name = data.get('customer_name', inv.customer_name)
    inv.po_number     = data.get('po_number', inv.po_number)
    inv.po_date       = _parse_date(data.get('po_date')) or inv.po_date
    inv.description   = data.get('description', inv.description)
    inv.amount        = float(data.get('amount', inv.amount) or inv.amount)
    inv.is_additional = data.get('is_additional', inv.is_additional)

    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'UPDATE', 'Invoice', f'Mengubah invoice ID {id}: {inv.po_number}')

    return jsonify({'success': True, 'message': 'Invoice berhasil diperbarui.',
                    'data': inv.to_dict()})


# ─── PATCH /api/invoices/<id>/paid ───────────────────────────────────────────
@invoices_bp.route('/<int:id>/paid', methods=['PATCH'])
@login_required
def mark_paid(id):
    inv  = Invoice.query.get_or_404(id)
    data = request.get_json(silent=True) or {}
    paid_date = _parse_date(data.get('paid_date'))

    inv.paid_date = paid_date or inv.paid_date
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'PAID', 'Invoice',
              f'Menandai invoice {inv.po_number} sebagai lunas pada {inv.paid_date}')

    return jsonify({'success': True,
                    'message': f'Invoice {inv.po_number} ditandai sebagai lunas.',
                    'data': inv.to_dict()})


# ─── PATCH /api/invoices/<id>/archive ────────────────────────────────────────
@invoices_bp.route('/<int:id>/archive', methods=['PATCH'])
@login_required
def archive_invoice(id):
    inv = Invoice.query.get_or_404(id)
    inv.is_archived = True
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'ARCHIVE', 'Invoice', f'Mengarsipkan invoice: {inv.po_number}')

    return jsonify({'success': True,
                    'message': f'Invoice {inv.po_number} berhasil diarsipkan.',
                    'data': inv.to_dict()})


# ─── PATCH /api/invoices/<id>/restore ────────────────────────────────────────
@invoices_bp.route('/<int:id>/restore', methods=['PATCH'])
@login_required
def restore_invoice(id):
    inv = Invoice.query.get_or_404(id)
    inv.is_archived = False
    db.session.commit()

    return jsonify({'success': True,
                    'message': f'Invoice {inv.po_number} berhasil dipulihkan.',
                    'data': inv.to_dict()})


# ─── DELETE /api/invoices/<id> ───────────────────────────────────────────────
@invoices_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_invoice(id):
    inv = Invoice.query.get_or_404(id)
    po  = inv.po_number
    db.session.delete(inv)
    db.session.commit()

    catat_log(session.get('user_id'), session.get('username'),
              'DELETE', 'Invoice', f'Menghapus invoice: {po}')

    return jsonify({'success': True, 'message': f'Invoice {po} berhasil dihapus.'})


# ─── GET /api/invoices/summary ───────────────────────────────────────────────
@invoices_bp.route('/summary', methods=['GET'])
@login_required
def summary():
    from sqlalchemy import func
    total_amount = db.session.query(func.sum(Invoice.amount)).filter_by(
        is_archived=False).scalar() or 0
    total_paid   = db.session.query(func.sum(Invoice.amount)).filter(
        Invoice.is_archived == False,
        Invoice.paid_date.isnot(None)
    ).scalar() or 0
    total_unpaid = float(total_amount) - float(total_paid)

    return jsonify({
        'success': True,
        'data': {
            'total_amount': float(total_amount),
            'total_paid':   float(total_paid),
            'total_unpaid': total_unpaid,
        }
    })
