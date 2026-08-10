from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from portal.models import User
from .models import (
    BusinessPartner,
    CashTransaction,
    Company,
    CustomerPurchaseOrder,
    Employee,
    FundRequest,
    Invoice,
    Project,
    ProjectBudgetLine,
    ProjectMember,
    ProjectSegment,
    PurchaseOrderItem,
    Role,
    UserOrganization,
)
from .selectors import projects_for_user
from .services import disburse_fund_request, record_invoice_payment


class ErpWorkflowTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Company")
        self.role_admin = Role.objects.create(code="ADMIN", name="Admin")
        self.role_worker = Role.objects.create(code="LAPANGAN", name="Lapangan")
        self.admin = User.objects.create_user("admin2", "secret12", nama="Admin", role="admin")
        self.worker = User.objects.create_user("worker2", "secret12", nama="Worker", role="lapangan")
        self.admin_employee = Employee.objects.create(company=self.company, employee_no="A1", name="Admin")
        self.worker_employee = Employee.objects.create(company=self.company, employee_no="W1", name="Worker")
        UserOrganization.objects.create(user=self.admin, company=self.company, employee=self.admin_employee, role=self.role_admin)
        UserOrganization.objects.create(user=self.worker, company=self.company, employee=self.worker_employee, role=self.role_worker)
        client = BusinessPartner.objects.create(company=self.company, partner_type="CLIENT", name="Client")
        self.project = Project.objects.create(company=self.company, client=client, project_code="P1", name="Project")
        self.segment = ProjectSegment.objects.create(project=self.project, segment_code="S1", segment_name="Segment")
        ProjectMember.objects.create(project=self.project, segment=self.segment, employee=self.worker_employee, assignment_role="LAPANGAN", assigned_at=date.today())
        self.po = CustomerPurchaseOrder.objects.create(project=self.project, po_number="PO1", po_date=date.today(), contract_value=1000, status="APPROVED", created_by=self.admin)
        self.po_item = PurchaseOrderItem.objects.create(purchase_order=self.po, item_code="I1", description="Work", unit="m", qty=10, unit_price=100)
        self.budget = ProjectBudgetLine.objects.create(project=self.project, segment=self.segment, po_item=self.po_item, line_code="B1", description="Work", cost_category="SERVICE", unit="m", planned_qty=10, unit_cost=80, status="APPROVED")

    def test_role_scoping_and_pages(self):
        self.assertEqual(list(projects_for_user(self.worker)), [self.project])
        client = Client(); client.force_login(self.worker)
        self.assertEqual(client.get("/erp/").status_code, 200)
        self.assertContains(client.get(f"/erp/projects/{self.project.id}/"), "Dashboard Proyek")

    def test_disbursement_and_payment_create_cash_ledger(self):
        request = FundRequest.objects.create(project=self.project, requested_by=self.admin, request_number="PD1", request_date=date.today(), total_requested=500, status="APPROVED")
        disburse_fund_request(request, Decimal("500"), "TRANSFER", "OUT-1", self.admin)
        invoice = Invoice.objects.create(project=self.project, purchase_order=self.po, invoice_number="INV1", invoice_date=date.today(), subtotal=1000, tax=0, total=1000, status="SENT", created_by=self.admin)
        record_invoice_payment(invoice, Decimal("400"), date.today(), "IN-1", "TRANSFER", self.admin)
        self.assertEqual(CashTransaction.objects.filter(direction="OUT").count(), 1)
        self.assertEqual(CashTransaction.objects.filter(direction="IN").count(), 1)

    def test_cross_project_segment_is_rejected(self):
        other = Project.objects.create(company=self.company, client=self.project.client, project_code="P2", name="Other")
        line = ProjectBudgetLine(project=other, segment=self.segment, line_code="X", description="X", cost_category="SERVICE", unit="m", planned_qty=1, unit_cost=1)
        with self.assertRaises(ValidationError):
            line.full_clean()
