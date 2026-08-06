from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from werkzeug.security import generate_password_hash, check_password_hash
class UM(BaseUserManager):
 def create_user(self,username,password=None,**x):
  u=self.model(username=username,**x); u.set_password(password); u.save(); return u
 def create_superuser(self,username,password=None,**x): x.update(role='admin',is_staff=True,is_superuser=True,nama=x.get('nama','Super Admin')); return self.create_user(username,password,**x)
class User(AbstractBaseUser):
 username=models.CharField(max_length=100,unique=True); password=models.CharField(max_length=255); nama=models.CharField(max_length=150); email=models.CharField(max_length=150,null=True); role=models.CharField(max_length=20,default='user'); phone=models.CharField(max_length=20,null=True); jabatan=models.CharField(max_length=100,null=True); avatar=models.CharField(max_length=255,null=True); is_active=models.BooleanField(default=True); is_staff=models.BooleanField(default=False); is_superuser=models.BooleanField(default=False); created_at=models.DateTimeField(default=timezone.now); updated_at=models.DateTimeField(auto_now=True); objects=UM(); USERNAME_FIELD='username'
 class Meta: db_table='users'
 def set_password(self,p): self.password=generate_password_hash(p,method='pbkdf2:sha256')
 def check_password(self,p):
  try: return check_password_hash(self.password,p)
  except ValueError: return super().check_password(p)
 def has_perm(self,p,obj=None): return self.is_superuser
 def has_module_perms(self,a): return self.is_superuser
 def to_dict(self): return D(self,'id username nama email role phone jabatan avatar is_active created_at')
class Base(models.Model):
 created_at=models.DateTimeField(default=timezone.now); updated_at=models.DateTimeField(auto_now=True)
 class Meta: abstract=True
class Customer(Base):
 name=models.CharField(max_length=200); email=models.CharField(max_length=150,null=True); phone=models.CharField(max_length=30,null=True); address=models.TextField(null=True)
 class Meta: db_table='customers'
 def to_dict(self): return D(self,'id name email phone address created_at')
class Project(Base):
 customer=models.ForeignKey(Customer,on_delete=models.CASCADE); project_type=models.CharField(max_length=20,default='po'); project_name=models.CharField(max_length=200); po_number=models.CharField(max_length=100,null=True); po_date=models.DateField(null=True); description=models.TextField(null=True); amount=models.DecimalField(max_digits=20,decimal_places=2,default=0); status=models.CharField(max_length=20,default='active'); completed_date=models.DateField(null=True); created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,db_column='created_by')
 class Meta: db_table='projects'
 def to_dict(self): d=D(self,'id customer_id project_type project_name po_number po_date description amount status completed_date created_at'); d['customer_name']=self.customer.name; return d
class ProjectAssignment(Base):
 user=models.ForeignKey(User,on_delete=models.CASCADE); project=models.ForeignKey(Project,on_delete=models.CASCADE)
 class Meta: db_table='project_assignments'
class ProjectRAB(Base):
 project=models.ForeignKey(Project,on_delete=models.CASCADE,related_name='rab'); kategori=models.CharField(max_length=30); deskripsi=models.TextField(null=True); satuan=models.CharField(max_length=50,null=True); volume=models.DecimalField(max_digits=15,decimal_places=3,null=True); harga_satuan=models.DecimalField(max_digits=20,decimal_places=2,null=True); total=models.DecimalField(max_digits=20,decimal_places=2,null=True)
 class Meta: db_table='project_rab'
 def to_dict(self): return D(self,'id project_id kategori deskripsi satuan volume harga_satuan total')
class ProjectTimeline(Base):
 project=models.ForeignKey(Project,on_delete=models.CASCADE,related_name='timeline'); number=models.IntegerField(); task_name=models.CharField(max_length=200); tanggal=models.DateField(); status=models.CharField(max_length=30,default='planned'); notes=models.TextField(null=True)
 class Meta: db_table='project_timeline'
 def to_dict(self): return D(self,'id project_id number task_name tanggal status notes')
class Invoice(Base):
 customer_name=models.CharField(max_length=200); po_number=models.CharField(max_length=100); po_date=models.DateField(null=True); description=models.TextField(null=True); amount=models.DecimalField(max_digits=20,decimal_places=2,default=0); is_additional=models.BooleanField(default=False); paid_date=models.DateField(null=True); is_archived=models.BooleanField(default=False); project=models.ForeignKey(Project,on_delete=models.SET_NULL,null=True); created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,db_column='created_by')
 class Meta: db_table='invoices'
 def to_dict(self): return D(self,'id customer_name po_number po_date description amount is_additional paid_date is_archived project_id created_at')
class Expense(Base):
 tanggal=models.DateField(); kategori=models.CharField(max_length=100); deskripsi=models.TextField(null=True); jumlah=models.DecimalField(max_digits=20,decimal_places=2,default=0); keterangan=models.TextField(null=True); created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,db_column='created_by')
 class Meta: abstract=True
 def to_dict(self): return D(self,'id tanggal kategori deskripsi jumlah keterangan created_at')
class OverheadKantor(Expense):
 class Meta: db_table='overhead_kantor'
class Absen(Base):
 tanggal=models.DateField(); project=models.ForeignKey(Project,on_delete=models.SET_NULL,null=True); project_name=models.CharField(max_length=200); segmen=models.CharField(max_length=200,null=True); waktu_lapor=models.CharField(max_length=20,null=True); deskripsi=models.TextField(null=True); created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,db_column='created_by')
 class Meta: db_table='absen'
 def to_dict(self):
  d=D(self,'id tanggal project_id project_name segmen waktu_lapor deskripsi created_at'); d.update(detail=[x.to_dict() for x in self.detail.all()],foto=[x.to_dict() for x in self.foto.all()]); return d
class AbsenDetail(Base):
 absen=models.ForeignKey(Absen,on_delete=models.CASCADE,related_name='detail'); kategori=models.CharField(max_length=100); label=models.CharField(max_length=200); nilai=models.CharField(max_length=100,null=True); satuan=models.CharField(max_length=50,null=True)
 class Meta: db_table='absen_detail'
 def to_dict(self): return D(self,'id kategori label nilai satuan')
class AbsenFoto(Base):
 absen=models.ForeignKey(Absen,on_delete=models.CASCADE,related_name='foto'); nama_file=models.CharField(max_length=255); caption=models.CharField(max_length=255,null=True)
 class Meta: db_table='absen_foto'
 def to_dict(self): d=D(self,'id nama_file caption'); d['url']='/static/uploads/'+self.nama_file; return d
class LogAktivitas(models.Model):
 user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True); username=models.CharField(max_length=100,null=True); aksi=models.CharField(max_length=100); modul=models.CharField(max_length=100,null=True); deskripsi=models.TextField(null=True); ip_address=models.CharField(max_length=50,null=True); created_at=models.DateTimeField(default=timezone.now)
 class Meta: db_table='log_aktivitas'
 def to_dict(self): return D(self,'id user_id username aksi modul deskripsi ip_address created_at')
class Setting(models.Model):
 kunci=models.CharField(max_length=100,unique=True); nilai=models.TextField(null=True); deskripsi=models.CharField(max_length=255,null=True); updated_at=models.DateTimeField(auto_now=True)
 class Meta: db_table='settings'
class Material(Base):
 project=models.ForeignKey(Project,on_delete=models.SET_NULL,null=True); name=models.CharField(max_length=200); price=models.DecimalField(max_digits=20,decimal_places=2,default=0); source=models.CharField(max_length=20,default='gudang'); used=models.BooleanField(default=False); created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,db_column='created_by')
 class Meta: db_table='materials'
 def to_dict(self): return D(self,'id project_id name price source used created_at updated_at')
class PettyCash(Expense):
 project=models.ForeignKey(Project,on_delete=models.SET_NULL,null=True)
 class Meta: db_table='petty_cash'
 def to_dict(self): return D(self,'id project_id tanggal kategori deskripsi jumlah keterangan created_at updated_at')
class PettyCashBudget(Base):
 project=models.OneToOneField(Project,on_delete=models.CASCADE,null=True); budget=models.DecimalField(max_digits=20,decimal_places=2,default=0); updated_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,db_column='updated_by')
 class Meta: db_table='petty_cash_budget'
class Kasbon(Base):
 user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='kasbon_requests'); project=models.ForeignKey(Project,on_delete=models.SET_NULL,null=True); tanggal_pengajuan=models.DateField(); jumlah=models.DecimalField(max_digits=20,decimal_places=2,default=0); keperluan=models.TextField(); status=models.CharField(max_length=20,default='pending'); tanggal_verifikasi=models.DateTimeField(null=True); verifier=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='+',db_column='verified_by'); rejection_reason=models.TextField(null=True); keterangan=models.TextField(null=True)
 class Meta: db_table='kasbon'
 def to_dict(self): d=D(self,'id user_id project_id tanggal_pengajuan jumlah keperluan status tanggal_verifikasi rejection_reason keterangan created_at updated_at'); d.update(user_name=self.user.nama,user_jabatan=self.user.jabatan,project_name=self.project.project_name if self.project else None,verified_by=self.verifier_id,verifier_name=self.verifier.nama if self.verifier else None); return d
class ProjectJasaSlip(Base):
 project=models.ForeignKey(Project,on_delete=models.CASCADE); employee_name=models.CharField(max_length=200); period_month=models.CharField(max_length=20); posisi=models.CharField(max_length=120,null=True); hari_kerja=models.IntegerField(null=True); jumlah_gaji=models.DecimalField(max_digits=20,decimal_places=2,default=0); tanggal_bayar=models.DateField(null=True); keterangan=models.TextField(null=True); created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,db_column='created_by')
 class Meta: db_table='project_jasa_slip'
 def to_dict(self): return D(self,'id project_id employee_name period_month posisi hari_kerja jumlah_gaji tanggal_bayar keterangan created_at updated_at')
class ProjectOverheadOpname(Base):
 project=models.ForeignKey(Project,on_delete=models.CASCADE); mandor_name=models.CharField(max_length=200); jumlah_pekerja=models.IntegerField(null=True); span=models.CharField(max_length=100,null=True); item_pekerjaan=models.TextField(); volume_progress=models.DecimalField(max_digits=15,decimal_places=3,default=0); harga_satuan=models.DecimalField(max_digits=20,decimal_places=2,default=0); nilai_opname=models.DecimalField(max_digits=20,decimal_places=2,default=0); keterangan=models.TextField(null=True); created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,db_column='created_by')
 class Meta: db_table='project_overhead_opname'
 def to_dict(self): return D(self,'id project_id mandor_name jumlah_pekerja span item_pekerjaan volume_progress harga_satuan nilai_opname keterangan created_at updated_at')
class ProjectOverheadKasbonMandor(Base):
 project=models.ForeignKey(Project,on_delete=models.CASCADE); mandor_name=models.CharField(max_length=200); unit_name=models.CharField(max_length=200,null=True); plafon=models.DecimalField(max_digits=20,decimal_places=2,default=0); kasbon_belum_dibayar=models.DecimalField(max_digits=20,decimal_places=2,default=0); pembayaran_terakhir=models.DecimalField(max_digits=20,decimal_places=2,default=0); status=models.CharField(max_length=20,default='saldo'); keterangan=models.TextField(null=True); created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,db_column='created_by')
 class Meta: db_table='project_overhead_kasbon_mandor'
 def to_dict(self): return D(self,'id project_id mandor_name unit_name plafon kasbon_belum_dibayar pembayaran_terakhir status keterangan created_at updated_at')
class SupervisiLaporan(Base):
 jenis=models.CharField(max_length=20,default='laporan'); tanggal=models.DateField(); project=models.ForeignKey(Project,on_delete=models.SET_NULL,null=True); project_name=models.CharField(max_length=200); lokasi=models.CharField(max_length=200,null=True); waktu_lapor=models.CharField(max_length=20,null=True); judul=models.CharField(max_length=255,null=True); catatan=models.TextField(null=True); created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,db_column='created_by')
 class Meta: db_table='supervisi_laporan'
 def to_dict(self): d=D(self,'id jenis tanggal project_id project_name lokasi waktu_lapor judul catatan created_at updated_at'); d.update(items=[x.to_dict() for x in self.items.all()],foto=[x.to_dict() for x in self.foto.all()]); return d
class SupervisiLaporanItem(Base):
 laporan=models.ForeignKey(SupervisiLaporan,on_delete=models.CASCADE,related_name='items'); segmen=models.CharField(max_length=200,null=True); kategori=models.CharField(max_length=100); nama_item=models.CharField(max_length=255); nilai=models.DecimalField(max_digits=15,decimal_places=3,null=True); satuan=models.CharField(max_length=50,null=True)
 class Meta: db_table='supervisi_laporan_item'
 def to_dict(self): return D(self,'id segmen kategori nama_item nilai satuan')
class SupervisiLaporanFoto(Base):
 laporan=models.ForeignKey(SupervisiLaporan,on_delete=models.CASCADE,related_name='foto'); nama_file=models.CharField(max_length=255); caption=models.CharField(max_length=255,null=True)
 class Meta: db_table='supervisi_laporan_foto'
 def to_dict(self): d=D(self,'id nama_file caption created_at'); d['url']='/static/uploads/'+self.nama_file; return d
class ProjectSegment(Base):
 project=models.ForeignKey(Project,on_delete=models.PROTECT,related_name='segments'); code=models.CharField(max_length=50); name=models.CharField(max_length=200); location=models.CharField(max_length=255,blank=True); is_active=models.BooleanField(default=True)
 class Meta: db_table='project_segments'; constraints=[models.UniqueConstraint(fields=['project','code'],name='uniq_project_segment_code')]
class ProjectMember(Base):
 project=models.ForeignKey(Project,on_delete=models.PROTECT,related_name='members'); segment=models.ForeignKey(ProjectSegment,on_delete=models.PROTECT,null=True,blank=True); user=models.ForeignKey(User,on_delete=models.PROTECT,related_name='erp_assignments'); start_date=models.DateField(); end_date=models.DateField(null=True,blank=True); is_active=models.BooleanField(default=True)
 class Meta: db_table='project_members'
class PurchaseOrder(Base):
 project=models.ForeignKey(Project,on_delete=models.PROTECT,related_name='purchase_orders'); number=models.CharField(max_length=80,unique=True); date=models.DateField(); tax_percent=models.DecimalField(max_digits=5,decimal_places=2,default=0); status=models.CharField(max_length=20,default='DRAFT'); created_by=models.ForeignKey(User,on_delete=models.PROTECT,related_name='+')
 class Meta: db_table='customer_purchase_orders'
class PurchaseOrderItem(Base):
 po=models.ForeignKey(PurchaseOrder,on_delete=models.CASCADE,related_name='items'); description=models.CharField(max_length=255); unit=models.CharField(max_length=30); quantity=models.DecimalField(max_digits=18,decimal_places=4); unit_price=models.DecimalField(max_digits=18,decimal_places=2)
 class Meta: db_table='purchase_order_items'
 @property
 def total(self): return self.quantity*self.unit_price
class BudgetLine(Base):
 project=models.ForeignKey(Project,on_delete=models.PROTECT,related_name='budget_lines'); po_item=models.ForeignKey(PurchaseOrderItem,on_delete=models.PROTECT,null=True,blank=True); code=models.CharField(max_length=50); description=models.CharField(max_length=255); category=models.CharField(max_length=50); unit=models.CharField(max_length=30); quantity=models.DecimalField(max_digits=18,decimal_places=4); unit_price=models.DecimalField(max_digits=18,decimal_places=2); version=models.PositiveIntegerField(default=1); status=models.CharField(max_length=20,default='DRAFT')
 class Meta: db_table='project_budget_lines'; constraints=[models.UniqueConstraint(fields=['project','code','version'],name='uniq_budget_version')]
 @property
 def total(self): return self.quantity*self.unit_price
class DailyReport(Base):
 number=models.CharField(max_length=80,unique=True); project=models.ForeignKey(Project,on_delete=models.PROTECT); segment=models.ForeignKey(ProjectSegment,on_delete=models.PROTECT); report_date=models.DateField(); activity=models.TextField(); quantity=models.DecimalField(max_digits=18,decimal_places=4,default=0); unit=models.CharField(max_length=30,blank=True); location=models.CharField(max_length=255,blank=True); attachment=models.FileField(upload_to='erp/daily/',blank=True); status=models.CharField(max_length=20,default='DRAFT'); notes=models.TextField(blank=True); created_by=models.ForeignKey(User,on_delete=models.PROTECT,related_name='daily_reports')
 class Meta: db_table='daily_reports'
class FundRequest(Base):
 number=models.CharField(max_length=80,unique=True); project=models.ForeignKey(Project,on_delete=models.PROTECT); segment=models.ForeignKey(ProjectSegment,on_delete=models.PROTECT); budget_line=models.ForeignKey(BudgetLine,on_delete=models.PROTECT); amount=models.DecimalField(max_digits=18,decimal_places=2); purpose=models.TextField(); status=models.CharField(max_length=20,default='DRAFT'); notes=models.TextField(blank=True); created_by=models.ForeignKey(User,on_delete=models.PROTECT,related_name='fund_requests')
 class Meta: db_table='fund_requests'
class Disbursement(Base):
 fund_request=models.ForeignKey(FundRequest,on_delete=models.PROTECT,related_name='disbursements'); date=models.DateField(); amount=models.DecimalField(max_digits=18,decimal_places=2); reference=models.CharField(max_length=100,unique=True); created_by=models.ForeignKey(User,on_delete=models.PROTECT,related_name='+')
 class Meta: db_table='disbursements'
class ExpenseReport(Base):
 number=models.CharField(max_length=80,unique=True); fund_request=models.ForeignKey(FundRequest,on_delete=models.PROTECT,related_name='expense_reports'); date=models.DateField(); amount=models.DecimalField(max_digits=18,decimal_places=2); description=models.TextField(); receipt=models.FileField(upload_to='erp/receipts/',blank=True); status=models.CharField(max_length=20,default='DRAFT'); notes=models.TextField(blank=True); created_by=models.ForeignKey(User,on_delete=models.PROTECT,related_name='+')
 class Meta: db_table='expense_reports'
class ProgressReport(Base):
 number=models.CharField(max_length=80,unique=True); project=models.ForeignKey(Project,on_delete=models.PROTECT); po_item=models.ForeignKey(PurchaseOrderItem,on_delete=models.PROTECT); period=models.DateField(); quantity=models.DecimalField(max_digits=18,decimal_places=4); status=models.CharField(max_length=20,default='DRAFT'); notes=models.TextField(blank=True); created_by=models.ForeignKey(User,on_delete=models.PROTECT,related_name='+')
 class Meta: db_table='progress_reports'
class ErpInvoice(Base):
 number=models.CharField(max_length=80,unique=True); project=models.ForeignKey(Project,on_delete=models.PROTECT); progress=models.ForeignKey(ProgressReport,on_delete=models.PROTECT); issue_date=models.DateField(); due_date=models.DateField(); subtotal=models.DecimalField(max_digits=18,decimal_places=2); tax=models.DecimalField(max_digits=18,decimal_places=2,default=0); status=models.CharField(max_length=20,default='DRAFT'); created_by=models.ForeignKey(User,on_delete=models.PROTECT,related_name='+')
 class Meta: db_table='erp_invoices'
 @property
 def total(self): return self.subtotal+self.tax
 @property
 def paid(self): return self.payments.aggregate(x=models.Sum('amount'))['x'] or __import__('decimal').Decimal('0')
class Payment(Base):
 invoice=models.ForeignKey(ErpInvoice,on_delete=models.PROTECT,related_name='payments'); date=models.DateField(); amount=models.DecimalField(max_digits=18,decimal_places=2); reference=models.CharField(max_length=100,unique=True); created_by=models.ForeignKey(User,on_delete=models.PROTECT,related_name='+')
 class Meta: db_table='payments'
class Approval(Base):
 module=models.CharField(max_length=40); object_id=models.PositiveBigIntegerField(); decision=models.CharField(max_length=20); notes=models.TextField(blank=True); decided_by=models.ForeignKey(User,on_delete=models.PROTECT); decided_at=models.DateTimeField(default=timezone.now)
 class Meta: db_table='approvals'; indexes=[models.Index(fields=['module','object_id'])]
def D(o,n):
 d={}
 for k in n.split():
  v=getattr(o,k); d[k]=float(v) if isinstance(v,__import__('decimal').Decimal) else v.isoformat() if hasattr(v,'isoformat') else v
 return d
