from datetime import date
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from .models import (Approval, BudgetLine, DailyReport, Disbursement, ErpInvoice,
 ExpenseReport, FundRequest, Payment, ProgressReport, Project, ProjectMember,
 ProjectSegment, PurchaseOrder, PurchaseOrderItem, User)

ADMIN_ROLES=('admin','superadmin')

def _role(user,*roles): return user.is_authenticated and user.role in roles
def _projects(user):
 q=Project.objects.all()
 if user.role in ('mandor','karyawan'): q=q.filter(members__user=user,members__is_active=True).distinct()
 return q

def _num(prefix,model): return f'{prefix}/{date.today():%Y%m}/{model.objects.count()+1:05d}'
def _money(v):
 try:return Decimal(v or 0)
 except:return Decimal('0')

def _context(request):
 projects=_projects(request.user)
 invoices=ErpInvoice.objects.filter(project__in=projects)
 incoming=Payment.objects.filter(invoice__project__in=projects).aggregate(x=Sum('amount'))['x'] or 0
 outgoing=Disbursement.objects.filter(fund_request__project__in=projects).aggregate(x=Sum('amount'))['x'] or 0
 return {'projects':projects,'segments':ProjectSegment.objects.filter(project__in=projects),'users':User.objects.filter(is_active=True),'pos':PurchaseOrder.objects.filter(project__in=projects),'po_items':PurchaseOrderItem.objects.filter(po__project__in=projects),'budgets':BudgetLine.objects.filter(project__in=projects),'daily':DailyReport.objects.filter(project__in=projects).order_by('-report_date')[:50],'funds':FundRequest.objects.filter(project__in=projects).order_by('-created_at')[:50],'expenses':ExpenseReport.objects.filter(fund_request__project__in=projects).order_by('-date')[:50],'progresses':ProgressReport.objects.filter(project__in=projects).order_by('-period')[:50],'erp_invoices':invoices.order_by('-issue_date')[:50],'incoming':incoming,'outgoing':outgoing,'balance':incoming-outgoing}

@login_required
def dashboard(request): return render(request,'erp/dashboard.html',_context(request))

@login_required
@transaction.atomic
def create(request,kind):
 if request.method!='POST': return redirect('erp-dashboard')
 p=request.POST; user=request.user
 try:
  project=get_object_or_404(_projects(user),pk=p.get('project')) if p.get('project') else None
  if kind=='segment' and _role(user,*ADMIN_ROLES): ProjectSegment.objects.create(project=project,code=p['code'],name=p['name'],location=p.get('location',''))
  elif kind=='member' and _role(user,*ADMIN_ROLES): ProjectMember.objects.create(project=project,segment_id=p.get('segment') or None,user_id=p['user'],start_date=p['start_date'])
  elif kind=='po' and _role(user,*ADMIN_ROLES): PurchaseOrder.objects.create(project=project,number=p['number'],date=p['date'],tax_percent=_money(p.get('tax_percent')),created_by=user)
  elif kind=='po-item' and _role(user,*ADMIN_ROLES): PurchaseOrderItem.objects.create(po_id=p['po'],description=p['description'],unit=p['unit'],quantity=_money(p['quantity']),unit_price=_money(p['unit_price']))
  elif kind=='budget' and _role(user,*ADMIN_ROLES): BudgetLine.objects.create(project=project,po_item_id=p.get('po_item') or None,code=p['code'],description=p['description'],category=p['category'],unit=p['unit'],quantity=_money(p['quantity']),unit_price=_money(p['unit_price']))
  elif kind=='daily' and user.role=='karyawan':
   segment=get_object_or_404(ProjectSegment,pk=p['segment'],project=project)
   if not ProjectMember.objects.filter(project=project,segment=segment,user=user,is_active=True).exists(): return HttpResponseForbidden('Anda tidak ditugaskan pada segmen ini.')
   DailyReport.objects.create(number=_num('LH',DailyReport),project=project,segment=segment,report_date=p['date'],activity=p['activity'],quantity=_money(p['quantity']),unit=p.get('unit',''),location=p.get('location',''),attachment=request.FILES.get('attachment'),status='SUBMITTED',created_by=user)
  elif kind=='fund' and user.role=='mandor':
   budget=get_object_or_404(BudgetLine,pk=p['budget'],project=project); amount=_money(p['amount'])
   used=FundRequest.objects.filter(budget_line=budget).exclude(status__in=['REJECTED','DRAFT']).aggregate(x=Sum('amount'))['x'] or 0
   if amount+used>budget.total: raise ValueError('Nominal melebihi sisa anggaran.')
   FundRequest.objects.create(number=_num('PD',FundRequest),project=project,segment_id=p['segment'],budget_line=budget,amount=amount,purpose=p['purpose'],status='SUBMITTED',created_by=user)
  elif kind=='expense' and user.role=='mandor': ExpenseReport.objects.create(number=_num('ER',ExpenseReport),fund_request_id=p['fund'],date=p['date'],amount=_money(p['amount']),description=p['description'],receipt=request.FILES.get('receipt'),status='SUBMITTED',created_by=user)
  elif kind=='progress' and user.role=='mandor':
   item=get_object_or_404(PurchaseOrderItem,pk=p['po_item'],po__project=project); qty=_money(p['quantity']); prior=ProgressReport.objects.filter(po_item=item,status='APPROVED').aggregate(x=Sum('quantity'))['x'] or 0
   if qty+prior>item.quantity: raise ValueError('Progres kumulatif melebihi kuantitas kontrak.')
   ProgressReport.objects.create(number=_num('OP',ProgressReport),project=project,po_item=item,period=p['date'],quantity=qty,status='SUBMITTED',created_by=user)
  elif kind=='invoice' and _role(user,*ADMIN_ROLES):
   progress=get_object_or_404(ProgressReport,pk=p['progress'],project=project,status='APPROVED'); ErpInvoice.objects.create(number=p.get('number') or _num('INV',ErpInvoice),project=project,progress=progress,issue_date=p['date'],due_date=p['due_date'],subtotal=_money(p['subtotal']),tax=_money(p.get('tax')),created_by=user)
  elif kind=='payment' and _role(user,*ADMIN_ROLES):
   inv=get_object_or_404(ErpInvoice,pk=p['invoice']); amount=_money(p['amount'])
   if amount<=0 or inv.paid+amount>inv.total: raise ValueError('Pembayaran tidak valid atau melebihi piutang.')
   Payment.objects.create(invoice=inv,date=p['date'],amount=amount,reference=p['reference'],created_by=user); inv.status='PAID' if inv.paid>=inv.total else 'PARTIALLY_PAID';inv.save()
  else:return HttpResponseForbidden('Role tidak diizinkan untuk aksi ini.')
  messages.success(request,'Data berhasil disimpan.')
 except (ValueError,KeyError) as e: messages.error(request,str(e))
 return redirect('erp-dashboard')

@login_required
@transaction.atomic
def decide(request,module,pk,decision):
 if request.method!='POST':return redirect('erp-dashboard')
 mapping={'daily':(DailyReport,('mandor','admin','superadmin')),'fund':(FundRequest,ADMIN_ROLES),'expense':(ExpenseReport,ADMIN_ROLES),'progress':(ProgressReport,ADMIN_ROLES),'invoice':(ErpInvoice,ADMIN_ROLES)}
 if module not in mapping or not _role(request.user,*mapping[module][1]):return HttpResponseForbidden('Role tidak diizinkan.')
 obj=get_object_or_404(mapping[module][0],pk=pk); statuses={'approve':{'daily':'VERIFIED','fund':'APPROVED','expense':'VERIFIED','progress':'APPROVED','invoice':'APPROVED'},'revision':{'daily':'REVISION','fund':'REVISION','expense':'REVISION','progress':'REVISION','invoice':'DRAFT'},'reject':{'daily':'REVISION','fund':'REJECTED','expense':'REJECTED','progress':'REJECTED','invoice':'DRAFT'}}
 obj.status=statuses[decision][module]; obj.notes=request.POST.get('notes','');obj.save();Approval.objects.create(module=module,object_id=obj.pk,decision=obj.status,notes=obj.notes,decided_by=request.user)
 if module=='fund' and decision=='approve' and request.POST.get('disburse'):
  Disbursement.objects.create(fund_request=obj,date=date.today(),amount=obj.amount,reference=_num('CASHOUT',Disbursement),created_by=request.user);obj.status='DISBURSED';obj.save()
 messages.success(request,'Keputusan tersimpan dalam audit persetujuan.');return redirect('erp-dashboard')
