import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ssm.settings')
import django
django.setup()

from django.test import RequestFactory, Client
from django.urls import reverse
from erp.models import OfficeOverhead
from erp.forms import OfficeOverheadForm
from erp.views import office_overhead_list, office_overhead_form, office_overhead_delete, office_overhead_approve
from erp.context_processors import navigation
from django.contrib.auth import get_user_model
from erp.models import Company, Role, UserOrganization, Employee

User = get_user_model()

company = Company.objects.first()
if not company:
    company = Company.objects.create(name='PT ABC', address='Jakarta')
role = Role.objects.filter(code='SUPERADMIN').first()
if not role:
    role = Role.objects.create(code='SUPERADMIN', name='Superadmin')
user, _ = User.objects.get_or_create(username='verify_overhead_3', defaults={'nama':'Verify','role':'superadmin'})
user.set_password('test')
user.save()
emp, _ = Employee.objects.get_or_create(company=company, employee_no='V3', defaults={'name':'Verify','is_active':True})
UserOrganization.objects.get_or_create(user=user, defaults={'company':company,'employee':emp,'role':role})

req = RequestFactory().get('/erp/office-overheads/')
req.user = user
ctx = navigation(req)
menu = ctx.get('global_navigation', [])
assert any(k == 'office_overheads' for k, _, _ in menu), 'menu missing'

assert reverse('erp:office-overheads') == '/erp/office-overheads/'
assert reverse('erp:office-overhead-create') == '/erp/office-overheads/create/'
assert reverse('erp:office-overhead-edit', kwargs={'pk': 1}) == '/erp/office-overheads/1/'
assert reverse('erp:office-overhead-delete', kwargs={'pk': 1}) == '/erp/office-overheads/1/delete/'
assert reverse('erp:office-overhead-approve', kwargs={'pk': 1}) == '/erp/office-overheads/1/approve/'

fields = [f.name for f in OfficeOverhead._meta.get_fields()]
for expected in ['company', 'expense_date', 'category', 'description', 'amount', 'reference_number', 'notes', 'attachment', 'approved_by', 'approved_at', 'created_by']:
    assert expected in fields, f'missing field {expected}'

form = OfficeOverheadForm(data={
    'expense_date': '2025-01-01',
    'category': 'ELECTRICITY',
    'description': 'Test bill',
    'amount': '100000',
    'reference_number': 'REF-1',
    'notes': 'Test',
})
assert form.is_valid(), form.errors.as_json()

client = Client()
client.force_login(user)
resp = client.get('/erp/office-overheads/')
assert resp.status_code == 200, f'list failed: {resp.status_code}'

resp = client.get('/erp/office-overheads/create/')
assert resp.status_code == 200, f'create get failed: {resp.status_code}'
resp = client.post('/erp/office-overheads/create/', data={
    'expense_date': '2025-01-02',
    'category': 'SALARY',
    'description': 'Gaji',
    'amount': '2000000',
    'reference_number': 'REF-2',
    'notes': '',
})
assert resp.status_code == 302, f'create post failed: {resp.status_code}'
assert resp.url == '/erp/office-overheads/'

overhead = OfficeOverhead.objects.filter(description='Gaji').first()
assert overhead is not None
assert overhead.company == company
assert overhead.created_by == user

resp = client.post(f'/erp/office-overheads/{overhead.pk}/approve/')
assert resp.status_code == 302, f'approve failed: {resp.status_code}'
overhead.refresh_from_db()
assert overhead.is_approved
assert overhead.approved_by == user

print('OK: overhead feature verified')
