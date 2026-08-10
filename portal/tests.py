import io
from pathlib import Path
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import Client,TestCase
from django.urls import URLPattern,get_resolver
from .models import Customer,Project,User

class ContractSmoke(TestCase):
 def setUp(self):
  self.u=User.objects.create_user('admin','admin123',nama='Admin',role='admin')
  self.c=Client();self.c.force_login(self.u)
  self.customer=Customer.objects.create(name='Contract Customer')
  self.project=Project.objects.create(customer=self.customer,project_name='Contract Project',created_by=self.u)
 def test_no_legacy_root_templates_remain(self):
  templates=[path for path in sorted(Path(settings.BASE_DIR/'templates').rglob('*.html')) if 'templates/erp/' not in str(path)]
  self.assertEqual(templates,[])
 def test_every_api_url_pattern_is_reachable(self):
  checked=[]
  for pattern in get_resolver().url_patterns:
   if not isinstance(pattern,URLPattern):continue
   raw=str(pattern.pattern)
   if not raw.startswith(('api/','^api/')):continue
   url='/'+raw.replace('^','').replace('$','').replace('\\/?','').replace('\\','')
   replacements={'<str:action>':'me','<str:sub>':'rab','<str:item>':'999999','<str:kind>':'x','<int:project_id>':str(self.project.id),'<int:id>':'999999'}
   for old,new in replacements.items():url=url.replace(old,new)
   response=self.c.get(url)
   with self.subTest(url=url):self.assertNotEqual(response.status_code,500)
   checked.append(url)
  self.assertGreaterEqual(len(checked),35)
 def test_legacy_html_aliases(self):
  urls=['/project/1/jasa','/project/1/overhead','/pengajuan-kasbon','/supervisi/profile-supervisi.html','/supervisi/absen.html','/supervisi/absen-supervisi.html','/supervisi/evidence-foto.html','/supervisi/laporan-kegiatan.html']
  for url in urls:
   with self.subTest(url=url):self.assertIn(self.c.get(url).status_code,(200,302))
 def test_supervisi_full_contract(self):
  payload={'jenis':'laporan','tanggal':'2026-08-06','project_id':self.project.id,'project_name':self.project.project_name,'judul':'Awal','items':[{'kategori':'progress','nama_item':'Pondasi','nilai':10,'satuan':'%'}]}
  response=self.c.post('/api/supervisi/laporan',payload,content_type='application/json');self.assertEqual(response.status_code,201);laporan_id=response.json()['data']['id']
  self.assertEqual(len(response.json()['data']['items']),1)
  self.assertEqual(len(self.c.get(f'/api/supervisi/laporan?jenis=laporan&project_id={self.project.id}&tanggal=2026-08-06&dari=2026-08-01&ke=2026-08-31').json()['data']),1)
  payload['judul']='Diubah';payload['items']=[{'kategori':'quality','nama_item':'Beton','nilai':90,'satuan':'%'}]
  response=self.c.put(f'/api/supervisi/laporan/{laporan_id}',payload,content_type='application/json');self.assertEqual(response.status_code,200);self.assertEqual(response.json()['data']['items'][0]['nama_item'],'Beton')
  photo=SimpleUploadedFile('proof.jpg',b'jpeg bytes',content_type='image/jpeg')
  response=self.c.post(f'/api/supervisi/laporan/{laporan_id}/foto',{'foto':photo,'caption':'bukti'});self.assertEqual(response.status_code,201);foto_id=response.json()['data'][0]['id']
  self.assertEqual(len(self.c.get(f'/api/supervisi/evidence?project_id={self.project.id}&tanggal=2026-08-06').json()['data']),1)
  self.assertEqual(self.c.delete(f'/api/supervisi/laporan/foto/{foto_id}').status_code,200)
  photo=SimpleUploadedFile('evidence.png',b'png bytes',content_type='image/png')
  response=self.c.post('/api/supervisi/evidence',{'project_id':self.project.id,'project_name':self.project.project_name,'tanggal':'2026-08-07','jenis':'absen','foto':photo});self.assertEqual(response.status_code,201)
  second=response.json()['laporan_id'];self.assertEqual(self.c.delete(f'/api/supervisi/laporan/{second}').status_code,200)
  self.assertEqual(self.c.delete(f'/api/supervisi/laporan/{laporan_id}').status_code,200)
 def test_supervisi_role_guard(self):
  user=User.objects.create_user('ordinary','secret12',nama='Ordinary',role='user');self.c.force_login(user)
  self.assertEqual(self.c.get('/api/supervisi/laporan').status_code,403)

class CsrfAndAuthSmoke(TestCase):
 def setUp(self):self.u=User.objects.create_user('admin','admin123',nama='Admin',role='admin');self.c=Client(enforce_csrf_checks=True)
 def test_health_login_and_csrf(self):
  self.assertTrue(self.c.get('/api/health').json()['success']);self.c.get('/login');token=self.c.cookies['csrftoken'].value
  response=self.c.post('/api/auth/login',{'username':'admin','password':'admin123'},content_type='application/json',HTTP_X_CSRFTOKEN=token);self.assertEqual(response.status_code,200)
  self.assertEqual(self.c.post('/api/customers',{'name':'X'},content_type='application/json').status_code,403)
 def test_werkzeug_password(self):self.assertTrue(self.u.check_password('admin123'))
