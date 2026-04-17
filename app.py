import os
from datetime import timedelta
from functools import wraps
from flask import Flask, jsonify, render_template, send_from_directory, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from config import config
from models import db

# Load .env jika ada
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def create_app(config_name='default'):
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )

    # ─── Load Config ───────────────────────────────────────────
    app.config.from_object(config[config_name])
    app.permanent_session_lifetime = timedelta(hours=8)

    # ─── Init Extensions ───────────────────────────────────────
    db.init_app(app)

    # ─── Register Blueprints ───────────────────────────────────
    from routes.auth            import auth_bp
    from routes.customers       import customers_bp
    from routes.projects        import projects_bp
    from routes.invoices        import invoices_bp
    from routes.overhead        import overhead_bp
    from routes.absen           import absen_bp
    from routes.log_aktivitas   import log_bp
    from routes.settings        import settings_bp
    from routes.materials       import materials_bp
    from routes.petty_cash      import petty_cash_bp
    from routes.kasbon          import kasbon_bp
    from routes.project_overhead import project_overhead_bp
    from routes.supervisi       import supervisi_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(overhead_bp)
    app.register_blueprint(absen_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(petty_cash_bp)
    app.register_blueprint(kasbon_bp)
    app.register_blueprint(project_overhead_bp)
    app.register_blueprint(supervisi_bp)

    # ─── Create upload folder ──────────────────────────────────
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ══════════════════════════════════════════════════════════
    # TEMPLATE ROUTES (serve HTML pages)
    # ══════════════════════════════════════════════════════════

    @app.route('/')
    def index():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return redirect(url_for('dashboard_page'))

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/dashboard')
    def dashboard_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        if session.get('role') == 'mandor':
            return redirect(url_for('mandor_request_kasbon_page'))
        if session.get('role') == 'supervisi':
            return redirect(url_for('supervisi_laporan_page'))
        return render_template('dashboard project.html', dashboard_project_id=None)

    @app.route('/dashboard/project/<int:project_id>')
    def dashboard_project_page(project_id):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('dashboard project.html', dashboard_project_id=project_id)

    @app.route('/project/<int:project_id>/jasa')
    def project_jasa_page(project_id):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('jasa.html', project_id=project_id)

    @app.route('/project-po')
    def project_po_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('project po.html')

    @app.route('/project-non-po')
    def project_non_po_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('project non-po.html')

    @app.route('/invoice')
    def invoice_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('invoice.html')

    @app.route('/overhead')
    def overhead_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('overhead kantor.html')

    @app.route('/absen')
    def absen_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('absen.html')

    @app.route('/arsip')
    def arsip_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('beranda arsip.html')

    @app.route('/arsip/invoice')
    def arsip_invoice_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('arsip invoice.html')

    @app.route('/arsip/project')
    def arsip_project_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('arsip project.html')

    @app.route('/log-aktivitas')
    def log_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('log aktivitas.html')

    @app.route('/profile')
    def profile_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        if session.get('role') == 'mandor':
            return redirect(url_for('mandor_profile_page'))
        if session.get('role') == 'supervisi':
            return redirect(url_for('supervisi_profile_page'))
        return render_template('profile.html')

    # ─── Role-based page guards ─────────────────────────────────
    def role_required(*roles):
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                if 'user_id' not in session:
                    return redirect(url_for('login_page'))
                if session.get('role') not in roles and session.get('role') != 'admin':
                    return redirect(url_for('dashboard_page'))
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    # ─── Mandor Pages ───────────────────────────────────────────
    @app.route('/mandor/profile')
    @app.route('/mandor/profile.html')
    @role_required('mandor')
    def mandor_profile_page():
        return render_template('mandor/profile.html')

    @app.route('/mandor/request-kasbon')
    @app.route('/mandor/request-kasbon.html')
    @role_required('mandor')
    def mandor_request_kasbon_page():
        return render_template('mandor/request kasbon.html')

    # ─── Supervisi Pages ────────────────────────────────────────
    @app.route('/supervisi/profile')
    @app.route('/supervisi/profile-supervisi.html')
    @role_required('supervisi')
    def supervisi_profile_page():
        return render_template('supervisi/profile.html')

    @app.route('/supervisi/absen')
    @app.route('/supervisi/absen.html')
    @app.route('/supervisi/absen-supervisi.html')
    @role_required('supervisi')
    def supervisi_absen_page():
        return render_template('supervisi/absen.html')

    @app.route('/supervisi/evidence-foto')
    @app.route('/supervisi/evidence-foto.html')
    @role_required('supervisi')
    def supervisi_evidence_page():
        return render_template('supervisi/evidence foto.html')

    @app.route('/supervisi/laporan-kegiatan')
    @app.route('/supervisi/laporan-kegiatan.html')
    @role_required('supervisi')
    def supervisi_laporan_page():
        return render_template('supervisi/laporan kegiatan.html')

    @app.route('/setting')
    def setting_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('setting.html')

    @app.route('/material')
    def material_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('material.html')

    @app.route('/petty-cash')
    def petty_cash_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('petty_cash.html')

    @app.route('/project/<int:project_id>/overhead')
    def project_overhead_page(project_id):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('project_overhead.html', project_id=project_id)

    @app.route('/verifikasi-kasbon')
    def verifikasi_kasbon_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('verifikasi_kasbon.html')

    # ─── Serve uploaded files ──────────────────────────────────
    @app.route('/static/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # ─── Error Handlers ────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Endpoint tidak ditemukan.'}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'success': False, 'message': 'Method tidak diizinkan.'}), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

    # ─── API Root / Health Check ───────────────────────────────
    @app.route('/api/')
    @app.route('/api/health')
    def api_health():
        return jsonify({
            'success': True,
            'message': 'SSM Portal API berjalan.',
            'version': '1.0.0',
        })

    # ─── Context Processor ─────────────────────────────────────
    @app.context_processor
    def inject_user():
        return {
            'current_user': {
                'id':       session.get('user_id'),
                'username': session.get('username'),
                'nama':     session.get('nama'),
                'role':     session.get('role'),
                'avatar':   session.get('avatar'),
            }
        }

    return app


# ─── CLI command: init-db ──────────────────────────────────────────────────
def init_db(app):
    from models import User
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username = 'admin',
                nama     = 'Super Admin',
                email    = 'admin@ssm.co.id',
                role     = 'admin',
                jabatan  = 'Administrator',
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('✅ Default admin dibuat: username=admin, password=admin123')
        else:
            print('ℹ️  Admin sudah ada.')
        print('✅ Database berhasil diinisialisasi.')


if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000, debug=True)
