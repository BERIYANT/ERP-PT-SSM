import json, os, uuid
from datetime import datetime,date,timedelta
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import login as djlogin,logout as djlogout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Sum,Q,Count
from django.conf import settings
from .models import *
def data(r):
 try:return json.loads(r.body or b'{}')
 except:return {}
def J(x,s=200): return JsonResponse(x,status=s,safe=not isinstance(x,list))
def auth(fn):
 @wraps(fn)
 def w(r,*a,**k): return J({'success':False,'message':'Unauthorized. Silakan login terlebih dahulu.'},401) if not r.user.is_authenticated else fn(r,*a,**k)
 return w
def admin(fn):
 @wraps(fn)
 def w(r,*a,**k): return J({'success':False,'message':'Forbidden. Hanya admin yang dapat mengakses ini.'},403) if not r.user.is_authenticated or r.user.role!='admin' else fn(r,*a,**k)
 return w
def log(r,a,m,d):
 try: LogAktivitas.objects.create(user=r.user,username=r.user.username,aksi=a,modul=m,deskripsi=d,ip_address=r.META.get('REMOTE_ADDR'))
 except: pass
def parse(v):
 try:return datetime.strptime(v,'%Y-%m-%d').date()
 except:return None
@ensure_csrf_cookie
def page(r,name,**ctx):
 if name!='login.html' and not r.user.is_authenticated:return redirect('/login')
 return render(r,name,ctx)
def index(r): return redirect('/dashboard' if r.user.is_authenticated else '/login')
def dashboard(r,project_id=None):
 if r.user.is_authenticated and r.user.role=='mandor':return redirect('/mandor/request-kasbon')
 if r.user.is_authenticated and r.user.role=='supervisi':return redirect('/supervisi/laporan-kegiatan')
 return page(r,'dashboard project.html',dashboard_project_id=project_id)
def auth_api(r,action):
 if action=='login':
  d=data(r); u=User.objects.filter(username=(d.get('username') or '').strip(),is_active=True).first()
  if not u or not u.check_password((d.get('password') or '').strip()):return J({'success':False,'message':'Username atau password salah.'},401)
  djlogin(r,u,backend='django.contrib.auth.backends.ModelBackend'); log(r,'LOGIN','Auth',f'User {u.username} berhasil login')
  return J({'success':True,'message':'Login berhasil.','user':{**u.to_dict(),'jabatan':u.jabatan}})
 if not r.user.is_authenticated:return J({'success':False,'message':'Unauthorized. Silakan login terlebih dahulu.'},401)
 if action=='logout': djlogout(r); return J({'success':True,'message':'Logout berhasil.'})
 if action=='me':return J({'success':True,'user':r.user.to_dict()})
 d=data(r)
 if not r.user.check_password(d.get('old_password','')):return J({'success':False,'message':'Password lama tidak sesuai.'},400)
 if d.get('new_password')!=d.get('confirm_password') or len(d.get('new_password',''))<6:return J({'success':False,'message':'Konfirmasi password tidak cocok atau kurang dari 6 karakter.'},400)
 r.user.set_password(d['new_password']);r.user.save();return J({'success':True,'message':'Password berhasil diubah.'})
@auth
def customers(r,id=None):
 if id:c=get_object_or_404(Customer,pk=id)
 if r.method=='GET':return J({'success':True,'data':c.to_dict() if id else [x.to_dict() for x in Customer.objects.order_by('name')]})
 d=data(r)
 if r.method=='POST':
  if not (d.get('name') or '').strip():return J({'success':False,'message':'Nama customer wajib diisi.'},400)
  c=Customer.objects.create(**{k:d.get(k) or None for k in ('name','email','phone','address')});return J({'success':True,'message':'Customer berhasil ditambahkan.','data':c.to_dict()},201)
 if r.method=='DELETE':n=c.name;c.delete();return J({'success':True,'message':f'Customer "{n}" berhasil dihapus.'})
 for k in ('name','email','phone','address'):
  if k in d:setattr(c,k,d[k])
 c.save();return J({'success':True,'message':'Customer berhasil diperbarui.','data':c.to_dict()})
@auth
def project_nested_legacy(r,sub,item):
 M={'rab':ProjectRAB,'timeline':ProjectTimeline}[sub];obj=get_object_or_404(M,pk=item)
 return projects(r,obj.project_id,sub,str(item))
@auth
def projects(r,id=None,sub=None,item=None):
 if id:p=get_object_or_404(Project,pk=id)
 if sub in ('archive','restore'):
  p.status='archived' if sub=='archive' else 'active';p.completed_date=date.today() if sub=='archive' else None;p.save();return J({'success':True,'message':f'Project "{p.project_name}" berhasil diperbarui.','data':p.to_dict()})
 M={'rab':ProjectRAB,'timeline':ProjectTimeline,'jasa-slips':ProjectJasaSlip}.get(sub)
 if M:
  if sub=='jasa-slips' and item=='summary':
   q=M.objects.filter(project=p);return J({'success':True,'project':{'id':p.id,'name':p.project_name},'summary':{'total_slip':q.count(),'total_bayar':float(q.aggregate(x=Sum('jumlah_gaji'))['x'] or 0)}})
  q=M.objects.filter(project=p); obj=get_object_or_404(q,pk=item) if item else None
  if r.method=='GET':return J({'success':True,'project':{'id':p.id,'name':p.project_name},'data':obj.to_dict() if obj else [x.to_dict() for x in q] ,'total':float(q.aggregate(x=Sum('jumlah_gaji'))['x'] or 0) if sub=='jasa-slips' else 0})
  if r.method=='DELETE':obj.delete();return J({'success':True,'message':'Data berhasil dihapus.'})
  raw=data(r); rows=raw if isinstance(raw,list) else [raw]; made=[]
  for d in rows:
   vals={k:v for k,v in d.items() if k in [f.name for f in M._meta.fields]}; vals['project']=p
   for k in ('tanggal','tanggal_bayar'):
    if k in vals:vals[k]=parse(vals[k])
   if obj:
    for k,v in vals.items():setattr(obj,k,v)
    obj.save();made=[obj]
   else:made.append(M.objects.create(**vals))
  return J({'success':True,'message':'Data berhasil disimpan.','data':made[0].to_dict() if obj else [x.to_dict() for x in made]},200 if obj else 201)
 if id and r.method=='GET':d=p.to_dict();d['rab']=[x.to_dict() for x in p.rab.all()];return J({'success':True,'data':d})
 if not id and r.method=='GET':
  q=Project.objects.select_related('customer');
  for key,field in [('type','project_type'),('status','status'),('customer_id','customer_id')]:
   if r.GET.get(key):q=q.filter(**{field:r.GET[key]})
  return J({'success':True,'data':[x.to_dict() for x in q.order_by('-created_at')]})
 if r.method=='DELETE':n=p.project_name;p.delete();return J({'success':True,'message':f'Project "{n}" berhasil dihapus.'})
 d=data(r)
 if not id:
  c=get_object_or_404(Customer,pk=d.get('customer_id')); p=Project(customer=c,created_by=r.user,project_name=d.get('project_name',''),project_type=d.get('project_type','po'))
 for k in ('project_name','project_type','po_number','description','amount'):
  if k in d:setattr(p,k,d[k] or (0 if k=='amount' else None))
 if d.get('po_date'):p.po_date=parse(d['po_date'])
 p.save();return J({'success':True,'message':'Project berhasil disimpan.','data':p.to_dict()},201 if not id else 200)
def crud(r,model,id=None,authmut=True):
 if authmut and r.method!='GET' and not r.user.is_authenticated:return J({'success':False,'message':'Unauthorized'},401)
 obj=get_object_or_404(model,pk=id) if id else None
 if r.method=='GET':return J({'success':True,'data':obj.to_dict() if obj else [x.to_dict() for x in model.objects.all()]})
 if r.method=='DELETE':obj.delete();return J({'success':True,'message':'Data berhasil dihapus'})
 d=data(r); vals={k:v for k,v in d.items() if k in [f.name for f in model._meta.fields]}
 for k in ('tanggal','tanggal_pengajuan'):
  if k in vals:vals[k]=parse(vals[k])
 if 'created_by' in [f.name for f in model._meta.fields]:vals['created_by']=r.user
 if obj:
  for k,v in vals.items():setattr(obj,k,v)
  obj.save()
 else:obj=model.objects.create(**vals)
 return J({'success':True,'message':'Data berhasil disimpan','data':obj.to_dict()},200 if id else 201)
@auth
def invoices(r,id=None,action=None):
 if action=='summary':
  q=Invoice.objects.filter(is_archived=False);a=float(q.aggregate(x=Sum('amount'))['x'] or 0);p=float(q.filter(paid_date__isnull=False).aggregate(x=Sum('amount'))['x'] or 0);return J({'success':True,'data':{'total_amount':a,'total_paid':p,'total_unpaid':a-p}})
 if action:
  o=get_object_or_404(Invoice,pk=id); setattr(o,'is_archived',action=='archive') if action in ('archive','restore') else setattr(o,'paid_date',parse(data(r).get('paid_date')) or date.today());o.save();return J({'success':True,'message':'Invoice berhasil diperbarui.','data':o.to_dict()})
 if not id and r.method=='GET':
  q=Invoice.objects.filter(is_archived=r.GET.get('is_archived','false').lower()=='true')
  if r.GET.get('customer_name'):q=q.filter(customer_name__icontains=r.GET['customer_name'])
  if r.GET.get('is_additional') is not None:q=q.filter(is_additional=r.GET['is_additional'].lower()=='true')
  rows=[x.to_dict() for x in q.order_by('-created_at')];grouped={}
  for x in rows:grouped.setdefault(x['customer_name'],[]).append(x)
  return J({'success':True,'data':rows,'grouped':grouped})
 if not id and r.method=='POST':
  raw=data(r);items=raw if isinstance(raw,list) else [raw];made=[]
  for d in items:
   vals={k:d.get(k) for k in ('customer_name','po_number','description','amount','is_additional','project_id') if k in d};vals['created_by']=r.user
   if d.get('po_date'):vals['po_date']=parse(d['po_date'])
   made.append(Invoice.objects.create(**vals))
  return J({'success':True,'message':f'{len(made)} invoice berhasil ditambahkan.','data':[x.to_dict() for x in made]},201)
 return crud(r,Invoice,id,False)
def settings_api(r,sub=None,id=None):
 if not r.user.is_authenticated:return J({'success':False,'message':'Unauthorized.'},401)
 if sub=='profile':
  if r.method=='GET':return J({'success':True,'data':r.user.to_dict()})
  d=data(r)
  for k in ('nama','email','phone','jabatan'):
   if k in d:setattr(r.user,k,d[k])
  r.user.save();return J({'success':True,'message':'Profil berhasil diperbarui.','data':r.user.to_dict()})
 if sub=='users':
  if r.user.role!='admin':return J({'success':False,'message':'Forbidden.'},403)
  if r.method=='GET':return J({'success':True,'data':[u.to_dict() for u in User.objects.order_by('nama')]})
  d=data(r);u=get_object_or_404(User,pk=id) if id else User(username=d.get('username'),nama=d.get('nama',''),role=d.get('role','user'))
  if r.method=='DELETE':u.delete();return J({'success':True,'message':'User berhasil dihapus.'})
  for k in ('nama','email','role','phone','jabatan','is_active'):
   if k in d:setattr(u,k,d[k])
  if d.get('password'):u.set_password(d['password'])
  u.save();return J({'success':True,'message':'User berhasil disimpan.','data':u.to_dict()},200 if id else 201)
 if sub=='assignments':
  if r.method=='GET':return J({'success':True,'data':[{'userId':u,'projectIds':list(ProjectAssignment.objects.filter(user_id=u).values_list('project_id',flat=True))} for u in ProjectAssignment.objects.values_list('user_id',flat=True).distinct()]})
  d=data(r);ProjectAssignment.objects.filter(user_id=d.get('userId')).delete();ProjectAssignment.objects.bulk_create([ProjectAssignment(user_id=d['userId'],project_id=x) for x in d.get('projectIds',[])]);return J({'success':True,'message':'Assignment berhasil disimpan.'})
 if r.method=='GET':return J({'success':True,'data':{x.kunci:x.nilai for x in Setting.objects.all()}})
 d=data(r)
 for k,v in d.items():Setting.objects.update_or_create(kunci=k,defaults={'nilai':v})
 return J({'success':True,'message':'Pengaturan berhasil disimpan.','updated':list(d)})
def upload(r,kind,parent):
 if not r.user.is_authenticated:return J({'success':False,'message':'Unauthorized'},401)
 files=r.FILES.getlist('foto') or r.FILES.getlist('avatar'); os.makedirs(settings.MEDIA_ROOT,exist_ok=True); out=[]
 for f in files:
  ext=f.name.rsplit('.',1)[-1].lower()
  if ext not in {'png','jpg','jpeg','gif','webp'}:continue
  n=f'{kind}_{parent}_{uuid.uuid4().hex}.{ext}'; open(settings.MEDIA_ROOT/n,'wb').write(b''.join(f.chunks()))
  if kind=='absen':o=AbsenFoto.objects.create(absen_id=parent,nama_file=n,caption=r.POST.get('caption'))
  elif kind=='supervisi':o=SupervisiLaporanFoto.objects.create(laporan_id=parent,nama_file=n,caption=r.POST.get('caption'))
  else:r.user.avatar='/static/uploads/'+n;r.user.save();return J({'success':True,'message':'Avatar berhasil diperbarui.','avatar':r.user.avatar})
  out.append(o.to_dict())
 return J({'success':bool(out),'message':f'{len(out)} foto berhasil diupload.','data':out},201 if out else 400)
def _delete_upload(name):
 try:
  path=os.path.join(settings.MEDIA_ROOT,os.path.basename(name))
  if os.path.isfile(path):os.remove(path)
 except OSError:pass
@auth
def supervisi_api(r,id=None,action=None):
 if r.user.role not in ('admin','supervisi'):return J({'success':False,'message':'Forbidden.'},403)
 if action=='delete-foto':
  foto=get_object_or_404(SupervisiLaporanFoto,pk=id);_delete_upload(foto.nama_file);foto.delete();return J({'success':True,'message':'Foto berhasil dihapus.'})
 if action=='foto':get_object_or_404(SupervisiLaporan,pk=id);return upload(r,'supervisi',id)
 q=SupervisiLaporan.objects.all()
 if not id and r.method=='GET':
  if r.GET.get('jenis') in ('absen','laporan'):q=q.filter(jenis=r.GET['jenis'])
  if r.GET.get('project_id'):q=q.filter(project_id=r.GET['project_id'])
  if parse(r.GET.get('tanggal')):q=q.filter(tanggal=parse(r.GET['tanggal']))
  if parse(r.GET.get('dari')):q=q.filter(tanggal__gte=parse(r.GET['dari']))
  if parse(r.GET.get('ke')):q=q.filter(tanggal__lte=parse(r.GET['ke']))
  return J({'success':True,'data':[x.to_dict() for x in q.order_by('-tanggal','-created_at')]})
 obj=get_object_or_404(q,pk=id) if id else None
 if r.method=='GET':return J({'success':True,'data':obj.to_dict()})
 if r.method=='DELETE':
  for foto in obj.foto.all():_delete_upload(foto.nama_file)
  obj.delete();return J({'success':True,'message':'Laporan berhasil dihapus.'})
 d=data(r);jenis=(d.get('jenis') or 'laporan').strip();tanggal=parse(d.get('tanggal'));project_name=(d.get('project_name') or '').strip()
 if jenis not in ('absen','laporan'):return J({'success':False,'message':'Jenis laporan tidak valid.'},400)
 if not obj and (not tanggal or not project_name):return J({'success':False,'message':'Tanggal dan project_name wajib diisi.'},400)
 if not obj:obj=SupervisiLaporan(jenis=jenis,tanggal=tanggal,project_name=project_name,created_by=r.user)
 for key in ('project_id','project_name','lokasi','waktu_lapor','judul','catatan'):
  if key in d:setattr(obj,key,d[key] or None)
 if tanggal:obj.tanggal=tanggal
 obj.save()
 if isinstance(d.get('items'),list):
  obj.items.all().delete()
  for raw in d['items']:
   nama=(raw.get('nama_item') or '').strip();kategori=(raw.get('kategori') or '').strip()
   if nama and kategori:SupervisiLaporanItem.objects.create(laporan=obj,nama_item=nama,kategori=kategori,segmen=(raw.get('segmen') or '').strip() or None,nilai=raw.get('nilai') or None,satuan=(raw.get('satuan') or '').strip() or None)
 return J({'success':True,'message':'Laporan berhasil dibuat.' if not id else 'Laporan berhasil diperbarui.','data':obj.to_dict()},201 if not id else 200)
@auth
def supervisi_evidence(r):
 if r.user.role not in ('admin','supervisi'):return J({'success':False,'message':'Forbidden.'},403)
 if r.method=='GET':
  q=SupervisiLaporanFoto.objects.select_related('laporan')
  if r.GET.get('project_id'):q=q.filter(laporan__project_id=r.GET['project_id'])
  if parse(r.GET.get('tanggal')):q=q.filter(laporan__tanggal=parse(r.GET['tanggal']))
  rows=[]
  for foto in q.order_by('-laporan__tanggal','-created_at'):
   d=foto.to_dict();d.update(laporan_id=foto.laporan_id,project_id=foto.laporan.project_id,project_name=foto.laporan.project_name,tanggal=foto.laporan.tanggal.isoformat(),jenis=foto.laporan.jenis);rows.append(d)
  return J({'success':True,'data':rows})
 jenis=(r.POST.get('jenis') or 'absen').strip();tanggal=parse(r.POST.get('tanggal'));project_name=(r.POST.get('project_name') or '').strip()
 if jenis not in ('absen','laporan'):return J({'success':False,'message':'Jenis evidence tidak valid.'},400)
 if not tanggal or not project_name:return J({'success':False,'message':'Project dan tanggal wajib diisi.'},400)
 laporan=SupervisiLaporan.objects.filter(jenis=jenis,tanggal=tanggal,project_id=r.POST.get('project_id') or None,project_name=project_name,created_by=r.user).order_by('-id').first()
 if not laporan:laporan=SupervisiLaporan.objects.create(jenis=jenis,tanggal=tanggal,project_id=r.POST.get('project_id') or None,project_name=project_name,judul=('ABSEN' if jenis=='absen' else 'LAPORAN')+' '+project_name,created_by=r.user)
 response=upload(r,'supervisi',laporan.id)
 if response.status_code==201:
  payload=json.loads(response.content);payload['laporan_id']=laporan.id;return J(payload,201)
 if not laporan.foto.exists() and not laporan.items.exists():laporan.delete()
 return response
def health(r):return J({'success':True,'message':'SSM Portal API berjalan.','version':'1.0.0'})

@auth
def log_api(r, action=None):
 q=LogAktivitas.objects.all()
 if action=='modules': return J({'success':True,'data':list(q.exclude(modul__isnull=True).values_list('modul',flat=True).distinct().order_by('modul'))})
 if action=='users': return J({'success':True,'data':list(q.exclude(username__isnull=True).values_list('username',flat=True).distinct().order_by('username'))})
 if action=='clear':
  if r.user.role!='admin': return J({'success':False,'message':'Forbidden.'},403)
  cutoff=datetime.now()-timedelta(days=int(r.GET.get('days',30))); n,_=q.filter(created_at__lt=cutoff).delete(); return J({'success':True,'message':f'{n} log aktivitas berhasil dihapus.'})
 for key,field in [('module','modul'),('user','username'),('action','aksi')]:
  if r.GET.get(key): q=q.filter(**{field+'__icontains':r.GET[key]})
 if parse(r.GET.get('from')): q=q.filter(created_at__date__gte=parse(r.GET['from']))
 if parse(r.GET.get('to')): q=q.filter(created_at__date__lte=parse(r.GET['to']))
 page_no=max(int(r.GET.get('page',1)),1); per=max(min(int(r.GET.get('per_page',50)),200),1); total=q.count()
 return J({'success':True,'data':[x.to_dict() for x in q.order_by('-created_at')[(page_no-1)*per:page_no*per]],'pagination':{'page':page_no,'per_page':per,'total':total,'pages':(total+per-1)//per}})

def material_api(r,id=None,action=None):
 if action=='budget':
  pid=r.GET.get('project_id'); q=ProjectRAB.objects.filter(kategori='material'); q=q.filter(project_id=pid) if pid else q
  return J({'success':True,'budget':float(q.aggregate(x=Sum('total'))['x'] or 0),'source':'rab'})
 if action=='move':
  if not r.user.is_authenticated:return J({'success':False,'message':'Unauthorized'},401)
  o=get_object_or_404(Material,pk=id); d=data(r); o.source=d.get('source',o.source); o.used=d.get('used',o.used); o.save(); return J({'success':True,'message':'Material berhasil dipindahkan.','data':o.to_dict()})
 return crud(r,Material,id)

def petty_api(r,id=None,action=None):
 if action=='summary':
  q=PettyCash.objects.all(); q=q.filter(project_id=r.GET['project_id']) if r.GET.get('project_id') else q
  rows=[{'kategori':x['kategori'],'total':float(x['total'] or 0)} for x in q.values('kategori').annotate(total=Sum('jumlah')).order_by('kategori')]
  return J({'success':True,'data':rows,'grand_total':sum(x['total'] for x in rows)})
 if action=='budget':
  if r.method=='POST':return J({'success':False,'message':'Budget otomatis diambil dari Project RAB kategori Petty Cash. Edit budget melalui RAB Project.'},400)
  q=ProjectRAB.objects.filter(kategori='patty_cash'); q=q.filter(project_id=r.GET['project_id']) if r.GET.get('project_id') else q
  amount=float(q.aggregate(x=Sum('total'))['x'] or 0);return J({'success':True,'budget':amount,'source':'rab' if amount else 'none'})
 return crud(r,PettyCash,id)

@auth
def overhead_api(r,id=None,action=None):
 if action=='kategori':return J({'success':True,'data':list(OverheadKantor.objects.values_list('kategori',flat=True).distinct().order_by('kategori'))})
 if action=='summary':
  q=OverheadKantor.objects.all(); bulan=r.GET.get('bulan')
  if bulan:
   try:y,m=map(int,bulan.split('-'));q=q.filter(tanggal__year=y,tanggal__month=m)
   except ValueError:pass
  rows=[{'kategori':x['kategori'],'total':float(x['total'] or 0)} for x in q.values('kategori').annotate(total=Sum('jumlah'))]
  return J({'success':True,'data':rows,'grand_total':sum(x['total'] for x in rows)})
 if not id and r.method=='GET':
  q=OverheadKantor.objects.all()
  if parse(r.GET.get('tanggal_dari')):q=q.filter(tanggal__gte=parse(r.GET['tanggal_dari']))
  if parse(r.GET.get('tanggal_ke')):q=q.filter(tanggal__lte=parse(r.GET['tanggal_ke']))
  if r.GET.get('kategori'):q=q.filter(kategori__icontains=r.GET['kategori'])
  return J({'success':True,'data':[x.to_dict() for x in q.order_by('-tanggal')]})
 return crud(r,OverheadKantor,id,False)

@auth
def absen_api(r,id=None,action=None):
 if action=='delete-foto':
  o=get_object_or_404(AbsenFoto,pk=id);o.delete();return J({'success':True,'message':'Foto berhasil dihapus.'})
 if r.method=='POST' and id and action=='foto':return upload(r,'absen',id)
 if not id and r.method=='GET':
  q=Absen.objects.all()
  for key in ('tanggal','dari','ke'):
   if parse(r.GET.get(key)):q=q.filter(**{'tanggal' + ({'dari':'__gte','ke':'__lte'}.get(key,'')):parse(r.GET[key])})
  if r.GET.get('project_id'):q=q.filter(project_id=r.GET['project_id'])
  return J({'success':True,'data':[x.to_dict() for x in q.order_by('-tanggal','-created_at')]})
 if r.method in ('POST','PUT'):
  d=data(r);o=get_object_or_404(Absen,pk=id) if id else Absen(created_by=r.user)
  for k in ('project_id','project_name','segmen','waktu_lapor','deskripsi'):
   if k in d:setattr(o,k,d[k] or None)
  if parse(d.get('tanggal')):o.tanggal=parse(d['tanggal'])
  o.save()
  if not id:
   for x in d.get('detail',[]):AbsenDetail.objects.create(absen=o,**{k:x.get(k) for k in ('kategori','label','nilai','satuan')})
  return J({'success':True,'message':'Laporan absen berhasil disimpan.','data':o.to_dict()},200 if id else 201)
 return crud(r,Absen,id,False)

@auth
def kasbon_api(r,id=None,action=None):
 q=Kasbon.objects.select_related('user','project','verifier')
 if action=='summary':
  return J({'success':True,'data':{s:float(q.filter(status=s).aggregate(x=Sum('jumlah'))['x'] or 0) for s in ('pending','approved','rejected')}})
 if id and action in ('approve','reject'):
  o=get_object_or_404(q,pk=id);d=data(r);o.status='approved' if action=='approve' else 'rejected';o.verifier=r.user;o.tanggal_verifikasi=datetime.now();o.rejection_reason=d.get('reason') or d.get('rejection_reason') if action=='reject' else None;o.save();return J({'success':True,'message':f'Kasbon berhasil di{action}.','data':o.to_dict()})
 return crud(r,Kasbon,id,False)

@auth
def project_overhead(r,project_id,id=None,kind='opname'):
 p=get_object_or_404(Project,pk=project_id); M=ProjectOverheadKasbonMandor if kind=='kasbon' else ProjectOverheadOpname
 if kind=='summary':
  q=ProjectOverheadOpname.objects.filter(project=p);total=float(q.aggregate(x=Sum('nilai_opname'))['x'] or 0);budget=float(ProjectRAB.objects.filter(project=p,kategori='overhead').aggregate(x=Sum('total'))['x'] or 0)
  return J({'success':True,'project':{'id':p.id,'name':p.project_name},'summary':{'total_items':q.count(),'total_nilai':total,'budget':budget,'remaining':budget-total,'percentage':round(total/budget*100,2) if budget else 0}})
 q=M.objects.filter(project=p)
 if kind=='kasbon' and r.method=='GET':
  status=r.GET.get('status','saldo');q=q if status=='all' else q.filter(status=status)
 if id:o=get_object_or_404(q,pk=id)
 if r.method=='GET':
  rows=[x.to_dict() for x in q.order_by('-created_at')]; result={'success':True,'project':{'id':p.id,'name':p.project_name},'data':o.to_dict() if id else rows}
  if kind=='opname':result['total']=sum(x['nilai_opname'] for x in rows)
  else:result.update(status=r.GET.get('status','saldo'),totals={'total_plafon':sum(x['plafon'] for x in rows),'total_kasbon_belum_dibayar':sum(x['kasbon_belum_dibayar'] for x in rows),'total_pembayaran_terakhir':sum(x['pembayaran_terakhir'] for x in rows)})
  return J(result)
 if r.method=='DELETE':o.delete();return J({'success':True,'message':'Data berhasil dihapus.'})
 d=data(r);vals={k:v for k,v in d.items() if k in [f.name for f in M._meta.fields]};vals.update(project=p,created_by=r.user)
 if kind=='opname':vals['nilai_opname']=float(vals.get('volume_progress',getattr(o,'volume_progress',0) if id else 0) or 0)*float(vals.get('harga_satuan',getattr(o,'harga_satuan',0) if id else 0) or 0)
 if id:
  for k,v in vals.items():setattr(o,k,v)
  o.save()
 else:o=M.objects.create(**vals)
 return J({'success':True,'message':'Data berhasil disimpan.','data':o.to_dict()},200 if id else 201)
