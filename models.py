from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─── User ─────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(100), nullable=False, unique=True)
    password   = db.Column(db.String(255), nullable=False)
    nama       = db.Column(db.String(150), nullable=False)
    email      = db.Column(db.String(150))
    role       = db.Column(db.Enum('admin', 'user', 'mandor', 'supervisi'),
                           nullable=False, default='user')
    phone      = db.Column(db.String(20))
    jabatan    = db.Column(db.String(100))
    avatar     = db.Column(db.String(255))
    is_active  = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def to_dict(self):
        return {
            'id':         self.id,
            'username':   self.username,
            'nama':       self.nama,
            'email':      self.email,
            'role':       self.role,
            'phone':      self.phone,
            'jabatan':    self.jabatan,
            'avatar':     self.avatar,
            'is_active':  self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ─── Customer ──────────────────────────────────────────────────────────────────
class Customer(db.Model):
    __tablename__ = 'customers'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(200), nullable=False)
    email      = db.Column(db.String(150))
    phone      = db.Column(db.String(30))
    address    = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    projects   = db.relationship('Project', backref='customer', lazy=True,
                                 cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'email':      self.email,
            'phone':      self.phone,
            'address':    self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ─── Project ───────────────────────────────────────────────────────────────────
class Project(db.Model):
    __tablename__ = 'projects'

    id             = db.Column(db.Integer, primary_key=True)
    customer_id    = db.Column(db.Integer, db.ForeignKey('customers.id',
                               ondelete='CASCADE'), nullable=False)
    project_type   = db.Column(db.Enum('po', 'non_po'), nullable=False, default='po')
    project_name   = db.Column(db.String(200), nullable=False)
    po_number      = db.Column(db.String(100))
    po_date        = db.Column(db.Date)
    description    = db.Column(db.Text)
    amount         = db.Column(db.Numeric(20, 2), nullable=False, default=0)
    status         = db.Column(db.Enum('active', 'archived'), nullable=False,
                               default='active')
    completed_date = db.Column(db.Date)
    created_by     = db.Column(db.Integer, db.ForeignKey('users.id',
                               ondelete='SET NULL'))
    created_at     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                               onupdate=datetime.utcnow)

    rab  = db.relationship('ProjectRAB', backref='project', lazy=True,
                           cascade='all, delete-orphan')
    timeline = db.relationship('ProjectTimeline', backref='project', lazy=True,
                              cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':             self.id,
            'customer_id':    self.customer_id,
            'customer_name':  self.customer.name if self.customer else None,
            'project_type':   self.project_type,
            'project_name':   self.project_name,
            'po_number':      self.po_number,
            'po_date':        self.po_date.isoformat() if self.po_date else None,
            'description':    self.description,
            'amount':         float(self.amount),
            'status':         self.status,
            'completed_date': self.completed_date.isoformat()
                              if self.completed_date else None,
            'created_at':     self.created_at.isoformat() if self.created_at else None,
        }


# ─── Project Assignment ────────────────────────────────────────────────────────
class ProjectAssignment(db.Model):
    __tablename__ = 'project_assignments'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('project_assignments', lazy=True, cascade='all, delete-orphan'))
    project = db.relationship('Project', backref=db.backref('assigned_users', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id':         self.id,
            'user_id':    self.user_id,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ─── Project RAB ───────────────────────────────────────────────────────────────
class ProjectRAB(db.Model):
    __tablename__ = 'project_rab'

    id           = db.Column(db.Integer, primary_key=True)
    project_id   = db.Column(db.Integer, db.ForeignKey('projects.id',
                             ondelete='CASCADE'), nullable=False)
    kategori     = db.Column(db.Enum('jasa', 'material', 'overhead', 'patty_cash'),
                             nullable=False)
    deskripsi    = db.Column(db.Text)
    satuan       = db.Column(db.String(50))
    volume       = db.Column(db.Numeric(15, 3))
    harga_satuan = db.Column(db.Numeric(20, 2))
    total        = db.Column(db.Numeric(20, 2))
    created_at   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':           self.id,
            'project_id':   self.project_id,
            'kategori':     self.kategori,
            'deskripsi':    self.deskripsi,
            'satuan':       self.satuan,
            'volume':       float(self.volume) if self.volume else None,
            'harga_satuan': float(self.harga_satuan) if self.harga_satuan else None,
            'total':        float(self.total) if self.total else None,
        }

# ─── Project Timeline ──────────────────────────────────────────────────────────────
class ProjectTimeline(db.Model):
    __tablename__ = 'project_timeline'

    id           = db.Column(db.Integer, primary_key=True)
    project_id   = db.Column(db.Integer, db.ForeignKey('projects.id',
                             ondelete='CASCADE'), nullable=False)
    number       = db.Column(db.Integer, nullable=False)
    task_name    = db.Column(db.String(200), nullable=False)
    tanggal      = db.Column(db.Date, nullable=False)
    status       = db.Column(db.Enum('planned', 'in_progress', 'completed'),
                             nullable=False, default='planned')
    notes        = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':        self.id,
            'project_id': self.project_id,
            'number':    self.number,
            'task_name': self.task_name,
            'tanggal':   self.tanggal.isoformat() if self.tanggal else None,
            'status':    self.status,
            'notes':     self.notes,
        }

# ─── Invoice ───────────────────────────────────────────────────────────────────
class Invoice(db.Model):
    __tablename__ = 'invoices'

    id            = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(200), nullable=False)
    po_number     = db.Column(db.String(100), nullable=False)
    po_date       = db.Column(db.Date)
    description   = db.Column(db.Text)
    amount        = db.Column(db.Numeric(20, 2), nullable=False, default=0)
    is_additional = db.Column(db.Boolean, nullable=False, default=False)
    paid_date     = db.Column(db.Date)
    is_archived   = db.Column(db.Boolean, nullable=False, default=False)
    project_id    = db.Column(db.Integer, db.ForeignKey('projects.id',
                              ondelete='SET NULL'))
    created_by    = db.Column(db.Integer, db.ForeignKey('users.id',
                              ondelete='SET NULL'))
    created_at    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':            self.id,
            'customer_name': self.customer_name,
            'po_number':     self.po_number,
            'po_date':       self.po_date.isoformat() if self.po_date else None,
            'description':   self.description,
            'amount':        float(self.amount),
            'is_additional': self.is_additional,
            'paid_date':     self.paid_date.isoformat() if self.paid_date else None,
            'is_archived':   self.is_archived,
            'project_id':    self.project_id,
            'created_at':    self.created_at.isoformat() if self.created_at else None,
        }


# ─── Overhead Kantor ───────────────────────────────────────────────────────────
class OverheadKantor(db.Model):
    __tablename__ = 'overhead_kantor'

    id         = db.Column(db.Integer, primary_key=True)
    tanggal    = db.Column(db.Date, nullable=False)
    kategori   = db.Column(db.String(100), nullable=False)
    deskripsi  = db.Column(db.Text)
    jumlah     = db.Column(db.Numeric(20, 2), nullable=False, default=0)
    keterangan = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id',
                           ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':         self.id,
            'tanggal':    self.tanggal.isoformat() if self.tanggal else None,
            'kategori':   self.kategori,
            'deskripsi':  self.deskripsi,
            'jumlah':     float(self.jumlah),
            'keterangan': self.keterangan,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ─── Absen ─────────────────────────────────────────────────────────────────────
class Absen(db.Model):
    __tablename__ = 'absen'

    id           = db.Column(db.Integer, primary_key=True)
    tanggal      = db.Column(db.Date, nullable=False)
    project_id   = db.Column(db.Integer, db.ForeignKey('projects.id',
                             ondelete='SET NULL'))
    project_name = db.Column(db.String(200), nullable=False)
    segmen       = db.Column(db.String(200))
    waktu_lapor  = db.Column(db.String(20))
    deskripsi    = db.Column(db.Text)
    created_by   = db.Column(db.Integer, db.ForeignKey('users.id',
                             ondelete='SET NULL'))
    created_at   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    detail = db.relationship('AbsenDetail', backref='absen', lazy=True,
                             cascade='all, delete-orphan')
    foto   = db.relationship('AbsenFoto', backref='absen', lazy=True,
                             cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':           self.id,
            'tanggal':      self.tanggal.isoformat() if self.tanggal else None,
            'project_id':   self.project_id,
            'project_name': self.project_name,
            'segmen':       self.segmen,
            'waktu_lapor':  self.waktu_lapor,
            'deskripsi':    self.deskripsi,
            'detail':       [d.to_dict() for d in self.detail],
            'foto':         [f.to_dict() for f in self.foto],
            'created_at':   self.created_at.isoformat() if self.created_at else None,
        }


class AbsenDetail(db.Model):
    __tablename__ = 'absen_detail'

    id         = db.Column(db.Integer, primary_key=True)
    absen_id   = db.Column(db.Integer, db.ForeignKey('absen.id',
                           ondelete='CASCADE'), nullable=False)
    kategori   = db.Column(db.String(100), nullable=False)
    label      = db.Column(db.String(200), nullable=False)
    nilai      = db.Column(db.String(100))
    satuan     = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':       self.id,
            'kategori': self.kategori,
            'label':    self.label,
            'nilai':    self.nilai,
            'satuan':   self.satuan,
        }


class AbsenFoto(db.Model):
    __tablename__ = 'absen_foto'

    id         = db.Column(db.Integer, primary_key=True)
    absen_id   = db.Column(db.Integer, db.ForeignKey('absen.id',
                           ondelete='CASCADE'), nullable=False)
    nama_file  = db.Column(db.String(255), nullable=False)
    caption    = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':        self.id,
            'nama_file': self.nama_file,
            'caption':   self.caption,
            'url':       f'/static/uploads/{self.nama_file}',
        }


# ─── Log Aktivitas ─────────────────────────────────────────────────────────────
class LogAktivitas(db.Model):
    __tablename__ = 'log_aktivitas'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id',
                           ondelete='SET NULL'))
    username   = db.Column(db.String(100))
    aksi       = db.Column(db.String(100), nullable=False)
    modul      = db.Column(db.String(100))
    deskripsi  = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':         self.id,
            'user_id':    self.user_id,
            'username':   self.username,
            'aksi':       self.aksi,
            'modul':      self.modul,
            'deskripsi':  self.deskripsi,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ─── Settings ──────────────────────────────────────────────────────────────────
class Setting(db.Model):
    __tablename__ = 'settings'

    id         = db.Column(db.Integer, primary_key=True)
    kunci      = db.Column(db.String(100), nullable=False, unique=True)
    nilai      = db.Column(db.Text)
    deskripsi  = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':        self.id,
            'kunci':     self.kunci,
            'nilai':     self.nilai,
            'deskripsi': self.deskripsi,
        }


# ─── Material ──────────────────────────────────────────────────────────────────
class Material(db.Model):
    __tablename__ = 'materials'

    id         = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'))
    name       = db.Column(db.String(200), nullable=False)
    price      = db.Column(db.Numeric(20, 2), nullable=False, default=0)
    source     = db.Column(db.Enum('gudang', 'lapangan'), nullable=False, default='gudang')
    used       = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':         self.id,
            'project_id': self.project_id,
            'name':       self.name,
            'price':      float(self.price),
            'source':     self.source,
            'used':       self.used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── Petty Cash ────────────────────────────────────────────────────────────────
class PettyCash(db.Model):
    __tablename__ = 'petty_cash'

    id          = db.Column(db.Integer, primary_key=True)
    project_id  = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'))
    tanggal     = db.Column(db.Date, nullable=False)
    kategori    = db.Column(db.String(100), nullable=False)
    deskripsi   = db.Column(db.Text)
    jumlah      = db.Column(db.Numeric(20, 2), nullable=False, default=0)
    keterangan  = db.Column(db.Text)
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':         self.id,
            'project_id': self.project_id,
            'tanggal':    self.tanggal.isoformat() if self.tanggal else None,
            'kategori':   self.kategori,
            'deskripsi':  self.deskripsi,
            'jumlah':     float(self.jumlah),
            'keterangan': self.keterangan,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── Petty Cash Budget ─────────────────────────────────────────────────────────
class PettyCashBudget(db.Model):
    __tablename__ = 'petty_cash_budget'

    id          = db.Column(db.Integer, primary_key=True)
    project_id  = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), 
                           unique=True, nullable=True)
    budget      = db.Column(db.Numeric(20, 2), nullable=False, default=0)
    updated_by  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':         self.id,
            'project_id': self.project_id,
            'budget':     float(self.budget),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── Kasbon ────────────────────────────────────────────────────────────────────
class Kasbon(db.Model):
    __tablename__ = 'kasbon'

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), 
                                  nullable=False)
    project_id        = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'))
    tanggal_pengajuan = db.Column(db.Date, nullable=False)
    jumlah            = db.Column(db.Numeric(20, 2), nullable=False, default=0)
    keperluan         = db.Column(db.Text, nullable=False)
    status            = db.Column(db.Enum('pending', 'approved', 'rejected'), 
                                  nullable=False, default='pending')
    tanggal_verifikasi = db.Column(db.DateTime)
    verified_by       = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    rejection_reason  = db.Column(db.Text)
    keterangan        = db.Column(db.Text)
    created_at        = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at        = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                                  onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='kasbon_requests')
    verifier = db.relationship('User', foreign_keys=[verified_by])
    project = db.relationship('Project', backref='kasbon_list')

    def to_dict(self):
        return {
            'id':                  self.id,
            'user_id':             self.user_id,
            'user_name':           self.user.nama if self.user else None,
            'user_jabatan':        self.user.jabatan if self.user else None,
            'project_id':          self.project_id,
            'project_name':        self.project.project_name if self.project else None,
            'tanggal_pengajuan':   self.tanggal_pengajuan.isoformat() if self.tanggal_pengajuan else None,
            'jumlah':              float(self.jumlah),
            'keperluan':           self.keperluan,
            'status':              self.status,
            'tanggal_verifikasi':  self.tanggal_verifikasi.isoformat() if self.tanggal_verifikasi else None,
            'verified_by':         self.verified_by,
            'verifier_name':       self.verifier.nama if self.verifier else None,
            'rejection_reason':    self.rejection_reason,
            'keterangan':          self.keterangan,
            'created_at':          self.created_at.isoformat() if self.created_at else None,
            'updated_at':          self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── Project Jasa Slip ───────────────────────────────────────────────────────
class ProjectJasaSlip(db.Model):
    __tablename__ = 'project_jasa_slip'

    id            = db.Column(db.Integer, primary_key=True)
    project_id    = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'),
                              nullable=False)
    employee_name = db.Column(db.String(200), nullable=False)
    period_month  = db.Column(db.String(20), nullable=False)
    posisi        = db.Column(db.String(120))
    hari_kerja    = db.Column(db.Integer)
    jumlah_gaji   = db.Column(db.Numeric(20, 2), nullable=False, default=0)
    tanggal_bayar = db.Column(db.Date)
    keterangan    = db.Column(db.Text)
    created_by    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    project = db.relationship('Project', backref='jasa_slip_list')

    def to_dict(self):
        return {
            'id':            self.id,
            'project_id':    self.project_id,
            'employee_name': self.employee_name,
            'period_month':  self.period_month,
            'posisi':        self.posisi,
            'hari_kerja':    self.hari_kerja,
            'jumlah_gaji':   float(self.jumlah_gaji) if self.jumlah_gaji else 0,
            'tanggal_bayar': self.tanggal_bayar.isoformat() if self.tanggal_bayar else None,
            'keterangan':    self.keterangan,
            'created_at':    self.created_at.isoformat() if self.created_at else None,
            'updated_at':    self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── Project Overhead Opname ────────────────────────────────────────────────────
class ProjectOverheadOpname(db.Model):
    __tablename__ = 'project_overhead_opname'

    id              = db.Column(db.Integer, primary_key=True)
    project_id      = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), 
                                nullable=False)
    mandor_name     = db.Column(db.String(200), nullable=False)
    jumlah_pekerja  = db.Column(db.Integer)
    span            = db.Column(db.String(100))
    item_pekerjaan  = db.Column(db.Text, nullable=False)
    volume_progress = db.Column(db.Numeric(15, 3), default=0)
    harga_satuan    = db.Column(db.Numeric(20, 2), default=0)
    nilai_opname    = db.Column(db.Numeric(20, 2), default=0)
    keterangan      = db.Column(db.Text)
    created_by      = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at      = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                                onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref='overhead_opname')

    def to_dict(self):
        return {
            'id':              self.id,
            'project_id':      self.project_id,
            'mandor_name':     self.mandor_name,
            'jumlah_pekerja':  self.jumlah_pekerja,
            'span':            self.span,
            'item_pekerjaan':  self.item_pekerjaan,
            'volume_progress': float(self.volume_progress) if self.volume_progress else 0,
            'harga_satuan':    float(self.harga_satuan) if self.harga_satuan else 0,
            'nilai_opname':    float(self.nilai_opname) if self.nilai_opname else 0,
            'keterangan':      self.keterangan,
            'created_at':      self.created_at.isoformat() if self.created_at else None,
            'updated_at':      self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── Project Overhead Kasbon Mandor ──────────────────────────────────────────
class ProjectOverheadKasbonMandor(db.Model):
    __tablename__ = 'project_overhead_kasbon_mandor'

    id                  = db.Column(db.Integer, primary_key=True)
    project_id          = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'),
                                    nullable=False)
    mandor_name         = db.Column(db.String(200), nullable=False)
    unit_name           = db.Column(db.String(200))
    plafon              = db.Column(db.Numeric(20, 2), default=0)
    kasbon_belum_dibayar = db.Column(db.Numeric(20, 2), default=0)
    pembayaran_terakhir = db.Column(db.Numeric(20, 2), default=0)
    status              = db.Column(db.Enum('saldo', 'pending', 'approved', 'rejected', 'paid'),
                                    nullable=False, default='saldo')
    keterangan          = db.Column(db.Text)
    created_by          = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at          = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at          = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                                    onupdate=datetime.utcnow)

    project = db.relationship('Project', backref='overhead_kasbon_mandor')

    def to_dict(self):
        return {
            'id':                   self.id,
            'project_id':           self.project_id,
            'mandor_name':          self.mandor_name,
            'unit_name':            self.unit_name,
            'plafon':               float(self.plafon) if self.plafon else 0,
            'kasbon_belum_dibayar': float(self.kasbon_belum_dibayar)
                                    if self.kasbon_belum_dibayar else 0,
            'pembayaran_terakhir':  float(self.pembayaran_terakhir)
                                    if self.pembayaran_terakhir else 0,
            'status':               self.status,
            'keterangan':           self.keterangan,
            'created_at':           self.created_at.isoformat() if self.created_at else None,
            'updated_at':           self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── Supervisi Laporan (Absensi & Kegiatan) ─────────────────────────────────
class SupervisiLaporan(db.Model):
    __tablename__ = 'supervisi_laporan'

    id          = db.Column(db.Integer, primary_key=True)
    jenis       = db.Column(db.Enum('absen', 'laporan'), nullable=False, default='laporan')
    tanggal     = db.Column(db.Date, nullable=False)
    project_id  = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'))
    project_name = db.Column(db.String(200), nullable=False)
    lokasi      = db.Column(db.String(200))
    waktu_lapor = db.Column(db.String(20))
    judul       = db.Column(db.String(255))
    catatan     = db.Column(db.Text)
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    items = db.relationship('SupervisiLaporanItem', backref='laporan', lazy=True,
                            cascade='all, delete-orphan')
    foto  = db.relationship('SupervisiLaporanFoto', backref='laporan', lazy=True,
                            cascade='all, delete-orphan')
    project = db.relationship('Project', backref='supervisi_laporan_list')

    def to_dict(self):
        return {
            'id':           self.id,
            'jenis':        self.jenis,
            'tanggal':      self.tanggal.isoformat() if self.tanggal else None,
            'project_id':   self.project_id,
            'project_name': self.project_name,
            'lokasi':       self.lokasi,
            'waktu_lapor':  self.waktu_lapor,
            'judul':        self.judul,
            'catatan':      self.catatan,
            'items':        [i.to_dict() for i in self.items],
            'foto':         [f.to_dict() for f in self.foto],
            'created_at':   self.created_at.isoformat() if self.created_at else None,
            'updated_at':   self.updated_at.isoformat() if self.updated_at else None,
        }


class SupervisiLaporanItem(db.Model):
    __tablename__ = 'supervisi_laporan_item'

    id         = db.Column(db.Integer, primary_key=True)
    laporan_id = db.Column(db.Integer, db.ForeignKey('supervisi_laporan.id',
                           ondelete='CASCADE'), nullable=False)
    segmen     = db.Column(db.String(200))
    kategori   = db.Column(db.String(100), nullable=False)
    nama_item  = db.Column(db.String(255), nullable=False)
    nilai      = db.Column(db.Numeric(15, 3))
    satuan     = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':        self.id,
            'segmen':    self.segmen,
            'kategori':  self.kategori,
            'nama_item': self.nama_item,
            'nilai':     float(self.nilai) if self.nilai is not None else None,
            'satuan':    self.satuan,
        }


class SupervisiLaporanFoto(db.Model):
    __tablename__ = 'supervisi_laporan_foto'

    id         = db.Column(db.Integer, primary_key=True)
    laporan_id = db.Column(db.Integer, db.ForeignKey('supervisi_laporan.id',
                           ondelete='CASCADE'), nullable=False)
    nama_file  = db.Column(db.String(255), nullable=False)
    caption    = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':        self.id,
            'nama_file': self.nama_file,
            'caption':   self.caption,
            'url':       f'/static/uploads/{self.nama_file}',
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }



