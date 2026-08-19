import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
user, _ = User.objects.get_or_create(username='verify_overhead_ext', defaults={'nama':'Verify','role':'superadmin'})
user.set_password('test')
user.save()
emp, _ = Employee.objects.get_or_create(company=company, employee_no='VE', defaults={'name':'Verify Ext','is_active':True})
UserOrganization.objects.get_or_create(user=user, defaults={'company':company,'employee':emp,'role':role})

client = Client()
client.force_login(user)

# Create
resp = client.post('/erp/office-overheads/create/', data={
    'expense_date': '2025-01-03',
    'category': 'MEALS',
    'description': 'Test Meals',
    'amount': '500000',
    'reference_number': 'REF-EXT',
    'notes': 'Extended test',
})
assert resp.status_code == 302 and resp.url == '/erp/office-overheads/', f'create failed: {resp.status_code}'
overhead = OfficeOverhead.objects.filter(description='Test Meals').first()
assert overhead is not None
assert overhead.company == company

# Edit GET
resp = client.get(f'/erp/office-overheads/{overhead.pk}/')
assert resp.status_code == 200, f'edit get failed: {resp.status_code}'

# Edit POST
resp = client.post(f'/erp/office-overheads/{overhead.pk}/', data={
    'expense_date': '2025-01-04',
    'category': 'MEALS',
    'description': 'Test Meals Edited',
    'amount': '550000',
    'reference_number': 'REF-EXT',
    'notes': 'Updated',
})
assert resp.status_code == 302, f'edit post failed: {resp.status_code}'
overhead.refresh_from_db()
assert overhead.description == 'Test Meals Edited'
assert overhead.amount == 550000

# Approve
resp = client.post(f'/erp/office-overheads/{overhead.pk}/approve/')
assert resp.status_code == 302, f'approve failed: {resp.status_code}'
overhead.refresh_from_db()
assert overhead.is_approved

# Delete
resp = client.post(f'/erp/office-overheads/{overhead.pk}/delete/')
assert resp.status_code == 302, f'delete failed: {resp.status_code}'
assert not OfficeOverhead.objects.filter(pk=overhead.pk).exists()

print('OK: overhead extended verified')
