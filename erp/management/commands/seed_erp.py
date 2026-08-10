from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from erp.models import (
    BusinessPartner,
    Company,
    CustomerPurchaseOrder,
    Employee,
    Project,
    ProjectBudgetLine,
    ProjectMember,
    ProjectSegment,
    PurchaseOrderItem,
    Role,
    UserOrganization,
)
from portal.models import User


class Command(BaseCommand):
    help = "Membuat akun dan data demo ERP yang saling terhubung secara idempoten."

    @transaction.atomic
    def handle(self, *args, **options):
        company, _ = Company.objects.update_or_create(name="PT Satria Sakti Mandiri", defaults={"address": "Indonesia"})
        roles = {}
        for code, name in Role.Code.choices:
            roles[code] = Role.objects.update_or_create(code=code, defaults={"name": name})[0]
        users = {}
        specs = [
            ("superadmin", "Superadmin ERP", "SUPERADMIN"),
            ("admin.erp", "Admin ERP", "ADMIN"),
            ("mandor.erp", "Mandor ERP", "MANDOR"),
            ("karyawan.erp", "Karyawan Lapangan", "LAPANGAN"),
        ]
        for index, (username, name, role_code) in enumerate(specs, 1):
            user, _ = User.objects.get_or_create(username=username, defaults={"nama": name, "role": role_code.lower(), "is_active": True})
            user.nama = name
            user.role = role_code.lower()
            user.is_active = True
            user.set_password("demo123")
            user.save()
            employee = None
            if role_code != "SUPERADMIN":
                employee, _ = Employee.objects.update_or_create(company=company, employee_no=f"EMP-{index:03d}", defaults={"name": name, "position": name})
            UserOrganization.objects.update_or_create(user=user, defaults={"company": company, "employee": employee, "role": roles[role_code]})
            users[role_code] = (user, employee)
        client, _ = BusinessPartner.objects.update_or_create(company=company, name="Kopindosat", defaults={"partner_type": "CLIENT", "address": "Jakarta"})
        project, _ = Project.objects.update_or_create(company=company, project_code="ERP-ROLL-UTARA", defaults={"client": client, "name": "RollOut Utara Kopindosat", "start_date": date(2024, 8, 1), "status": "ACTIVE"})
        segment, _ = ProjectSegment.objects.update_or_create(project=project, segment_code="CRB-TGL", defaults={"segment_name": "Cirebon - Tegal", "location": "Jalur Utara"})
        for role_code in ("ADMIN", "MANDOR", "LAPANGAN"):
            employee = users[role_code][1]
            ProjectMember.objects.get_or_create(project=project, segment=segment, employee=employee, assigned_at=date.today(), defaults={"assignment_role": role_code})
        po, _ = CustomerPurchaseOrder.objects.update_or_create(project=project, po_number="PO17877", defaults={"po_date": date(2024, 9, 5), "contract_value": Decimal("1453173217.70"), "tax_percent": 11, "status": "APPROVED", "created_by": users["ADMIN"][0]})
        item, _ = PurchaseOrderItem.objects.update_or_create(purchase_order=po, item_code="JASA-CABLE", defaults={"description": "Penarikan Kabel 48 Core", "unit": "meter", "qty": Decimal("86011"), "unit_price": Decimal("2000")})
        ProjectBudgetLine.objects.update_or_create(project=project, segment=segment, line_code="JASA-CABLE", version=1, defaults={"po_item": item, "description": item.description, "cost_category": "SERVICE", "unit": "meter", "planned_qty": item.qty, "unit_cost": item.unit_price, "status": "APPROVED"})
        self.stdout.write(self.style.SUCCESS("ERP siap. Login superadmin/admin.erp/mandor.erp/karyawan.erp, password demo123"))
