from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from portal.models import (BudgetLine, Customer, DailyReport, ErpInvoice, Project,
 ProjectMember, ProjectSegment, PurchaseOrder, PurchaseOrderItem, User)

class Command(BaseCommand):
 help='Membuat akun dan data demonstrasi ERP secara idempoten.'
 @transaction.atomic
 def handle(self,*args,**kwargs):
  users={}
  for username,nama,role in [('superadmin','Superadmin ERP','superadmin'),('admin.erp','Admin ERP','admin'),('mandor.erp','Mandor ERP','mandor'),('karyawan.erp','Karyawan Lapangan','karyawan')]:
   u,_=User.objects.get_or_create(username=username,defaults={'nama':nama,'role':role,'is_active':True});u.nama=nama;u.role=role;u.is_active=True;u.set_password('demo123');u.save();users[role]=u
  customer,_=Customer.objects.get_or_create(name='PT Pelanggan Demo ERP')
  project,_=Project.objects.get_or_create(project_name='Proyek Implementasi ERP',defaults={'customer':customer,'po_number':'PO-DEMO-001','po_date':date.today(),'amount':Decimal('1000000000'),'created_by':users['admin']})
  segment,_=ProjectSegment.objects.get_or_create(project=project,code='SEG-A',defaults={'name':'Pekerjaan Struktur','location':'Lokasi Proyek'})
  for role in ('mandor','karyawan'):ProjectMember.objects.get_or_create(project=project,segment=segment,user=users[role],start_date=date.today())
  po,_=PurchaseOrder.objects.get_or_create(number='PO-DEMO-001',defaults={'project':project,'date':date.today(),'tax_percent':11,'status':'ACTIVE','created_by':users['admin']})
  item,_=PurchaseOrderItem.objects.get_or_create(po=po,description='Pekerjaan Struktur Beton',defaults={'unit':'m3','quantity':100,'unit_price':Decimal('5000000')})
  BudgetLine.objects.get_or_create(project=project,code='RAB-001',version=1,defaults={'po_item':item,'description':'Material dan upah beton','category':'struktur','unit':'LS','quantity':1,'unit_price':Decimal('400000000'),'status':'APPROVED'})
  DailyReport.objects.get_or_create(number='LH-DEMO-001',defaults={'project':project,'segment':segment,'report_date':date.today(),'activity':'Pengecoran area A','quantity':10,'unit':'m3','status':'SUBMITTED','created_by':users['karyawan']})
  self.stdout.write(self.style.SUCCESS('Data ERP siap. Login: superadmin/admin.erp/mandor.erp/karyawan.erp; password semua: demo123'))
