from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DocumentStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Diajukan"
    REVIEWED = "REVIEWED", "Diperiksa"
    APPROVED = "APPROVED", "Disetujui"
    REVISION = "REVISION", "Perlu Revisi"
    REJECTED = "REJECTED", "Ditolak"
    DISBURSED = "DISBURSED", "Dicairkan"
    VERIFIED = "VERIFIED", "Diverifikasi"
    SETTLED = "SETTLED", "Diselesaikan"
    CLOSED = "CLOSED", "Ditutup"
    SENT = "SENT", "Dikirim"
    PARTIALLY_PAID = "PARTIALLY_PAID", "Dibayar Sebagian"
    PAID = "PAID", "Lunas"
    OVERDUE = "OVERDUE", "Jatuh Tempo"
    CANCELLED = "CANCELLED", "Dibatalkan"


class Company(TimeStampedModel):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "companies"
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name


class Employee(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="employees")
    employee_no = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    position = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "employees"
        constraints = [models.UniqueConstraint(fields=["company", "employee_no"], name="uq_employee_company_no")]

    def __str__(self):
        return f"{self.employee_no} - {self.name}"


class Role(TimeStampedModel):
    class Code(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Superadmin"
        ADMIN = "ADMIN", "Admin"
        MANDOR = "MANDOR", "Mandor"
        LAPANGAN = "LAPANGAN", "Karyawan Lapangan"

    code = models.CharField(max_length=20, choices=Code.choices, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.name


class UserOrganization(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organization")
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="user_organizations")
    employee = models.OneToOneField(Employee, on_delete=models.PROTECT, null=True, blank=True, related_name="user_organization")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="user_organizations")

    class Meta:
        db_table = "user_organizations"


class BusinessPartner(TimeStampedModel):
    class PartnerType(models.TextChoices):
        CLIENT = "CLIENT", "Pelanggan"
        VENDOR = "VENDOR", "Vendor"
        SUBCONTRACTOR = "SUBCONTRACTOR", "Subkontraktor"

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="business_partners")
    partner_type = models.CharField(max_length=20, choices=PartnerType.choices)
    name = models.CharField(max_length=200)
    tax_no = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    contact = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "business_partners"
        indexes = [models.Index(fields=["company", "partner_type", "name"])]

    def __str__(self):
        return self.name


class Project(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="erp_projects")
    client = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, related_name="projects")
    project_code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default="ACTIVE")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "erp_projects"
        constraints = [models.UniqueConstraint(fields=["company", "project_code"], name="uq_project_company_code")]
        indexes = [models.Index(fields=["company", "status"])]

    def clean(self):
        if self.client_id and self.company_id and self.client.company_id != self.company_id:
            raise ValidationError("Pelanggan harus berasal dari perusahaan yang sama.")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("Tanggal selesai tidak boleh sebelum tanggal mulai.")

    def __str__(self):
        return f"{self.project_code} - {self.name}"


class ProjectSegment(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="segments")
    segment_code = models.CharField(max_length=50)
    segment_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "erp_project_segments"
        constraints = [models.UniqueConstraint(fields=["project", "segment_code"], name="uq_erp_project_segment")]

    def __str__(self):
        return self.segment_name


class ProjectMember(TimeStampedModel):
    class AssignmentRole(models.TextChoices):
        ADMIN = "ADMIN", "Admin Proyek"
        MANDOR = "MANDOR", "Mandor"
        LAPANGAN = "LAPANGAN", "Karyawan Lapangan"

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="members")
    segment = models.ForeignKey(ProjectSegment, on_delete=models.PROTECT, null=True, blank=True, related_name="members")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="project_memberships")
    assignment_role = models.CharField(max_length=20, choices=AssignmentRole.choices)
    assigned_at = models.DateField()
    ended_at = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "erp_project_members"
        constraints = [models.UniqueConstraint(fields=["project", "segment", "employee", "assigned_at"], name="uq_project_member_period")]

    def clean(self):
        if self.segment_id and self.project_id and self.segment.project_id != self.project_id:
            raise ValidationError("Segmen tidak berada pada proyek yang dipilih.")
        if self.employee_id and self.project_id:
            try:
                if self.employee.company_id != self.project.company_id:
                    raise ValidationError("Pegawai tidak berada pada perusahaan proyek.")
            except Project.DoesNotExist:
                pass


class CustomerPurchaseOrder(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="purchase_orders")
    po_number = models.CharField(max_length=80)
    po_date = models.DateField()
    contract_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_customer_pos")

    class Meta:
        db_table = "erp_customer_purchase_orders"
        constraints = [models.UniqueConstraint(fields=["project", "po_number"], name="uq_project_po_number")]
        indexes = [models.Index(fields=["project", "status", "po_date"])]

    def __str__(self):
        return self.po_number


class PurchaseOrderItem(TimeStampedModel):
    purchase_order = models.ForeignKey(CustomerPurchaseOrder, on_delete=models.CASCADE, related_name="items")
    item_code = models.CharField(max_length=80)
    description = models.TextField()
    unit = models.CharField(max_length=30)
    qty = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        db_table = "erp_purchase_order_items"
        constraints = [models.UniqueConstraint(fields=["purchase_order", "item_code"], name="uq_po_item_code")]

    def save(self, *args, **kwargs):
        self.amount = self.qty * self.unit_price
        super().save(*args, **kwargs)


class ProjectBudgetLine(TimeStampedModel):
    class CostCategory(models.TextChoices):
        SERVICE = "SERVICE", "Jasa"
        MATERIAL = "MATERIAL", "Material"
        OVERHEAD = "OVERHEAD", "Overhead"
        PETTY_CASH = "PETTY_CASH", "Petty Cash"
        OTHER = "OTHER", "Lain-lain"

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="budget_lines")
    segment = models.ForeignKey(ProjectSegment, on_delete=models.PROTECT, null=True, blank=True, related_name="budget_lines")
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.PROTECT, null=True, blank=True, related_name="budget_lines")
    line_code = models.CharField(max_length=80)
    description = models.TextField()
    foreman_name = models.CharField(max_length=200, blank=True)
    expense_purpose = models.TextField(blank=True)
    cost_category = models.CharField(max_length=20, choices=CostCategory.choices)
    unit = models.CharField(max_length=30)
    planned_qty = models.DecimalField(max_digits=18, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2)
    planned_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)

    class Meta:
        db_table = "erp_project_budget_lines"
        constraints = [models.UniqueConstraint(fields=["project", "segment", "line_code", "version"], name="uq_budget_line_version")]
        indexes = [models.Index(fields=["project", "segment", "cost_category"])]

    def clean(self):
        if self.segment_id and self.segment.project_id != self.project_id:
            raise ValidationError("Segmen anggaran tidak berada pada proyek ini.")
        if self.po_item_id and self.po_item.purchase_order.project_id != self.project_id:
            raise ValidationError("Item PO tidak berada pada proyek ini.")

    def save(self, *args, **kwargs):
        self.planned_cost = self.planned_qty * self.unit_cost
        super().save(*args, **kwargs)


class FundRequest(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="fund_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="erp_fund_requests")
    request_number = models.CharField(max_length=80)
    request_date = models.DateField()
    total_requested = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    purpose = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "erp_fund_requests"
        constraints = [models.UniqueConstraint(fields=["project", "request_number"], name="uq_fund_request_number")]
        indexes = [models.Index(fields=["project", "status", "request_date"])]


class FundRequestItem(TimeStampedModel):
    fund_request = models.ForeignKey(FundRequest, on_delete=models.CASCADE, related_name="items")
    budget_line = models.ForeignKey(ProjectBudgetLine, on_delete=models.PROTECT, related_name="fund_request_items")
    description = models.TextField()
    qty = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        db_table = "erp_fund_request_items"

    def clean(self):
        if self.budget_line_id and self.fund_request_id and self.budget_line.project_id != self.fund_request.project_id:
            raise ValidationError("Baris anggaran tidak berada pada proyek pengajuan.")

    def save(self, *args, **kwargs):
        self.amount = self.qty * self.unit_price
        super().save(*args, **kwargs)


class Disbursement(TimeStampedModel):
    fund_request = models.ForeignKey(FundRequest, on_delete=models.PROTECT, related_name="disbursements")
    disbursement_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    method = models.CharField(max_length=30)
    reference_number = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="erp_disbursements")

    class Meta:
        db_table = "erp_disbursements"


class ExpenseReport(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="expense_reports")
    fund_request = models.ForeignKey(FundRequest, on_delete=models.PROTECT, null=True, blank=True, related_name="expense_reports")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="erp_expense_reports")
    report_number = models.CharField(max_length=80)
    report_date = models.DateField()
    total_actual = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "erp_expense_reports"
        constraints = [models.UniqueConstraint(fields=["project", "report_number"], name="uq_expense_report_number")]
        indexes = [models.Index(fields=["project", "status", "report_date"])]


class ExpenseItem(TimeStampedModel):
    expense_report = models.ForeignKey(ExpenseReport, on_delete=models.CASCADE, related_name="items")
    budget_line = models.ForeignKey(ProjectBudgetLine, on_delete=models.PROTECT, related_name="expense_items")
    expense_date = models.DateField()
    category = models.CharField(max_length=30)
    description = models.TextField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        db_table = "erp_expense_items"


class Attendance(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="attendances")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="attendances")
    work_date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    class Meta:
        db_table = "erp_attendances"
        constraints = [models.UniqueConstraint(fields=["project", "employee", "work_date"], name="uq_attendance_day")]
        indexes = [models.Index(fields=["project", "work_date", "employee"])]


class DailyReport(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="daily_reports")
    segment = models.ForeignKey(ProjectSegment, on_delete=models.PROTECT, related_name="daily_reports")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="erp_daily_reports")
    report_number = models.CharField(max_length=80)
    report_date = models.DateField()
    weather = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "erp_daily_reports"
        constraints = [models.UniqueConstraint(fields=["project", "report_number"], name="uq_daily_report_number")]
        indexes = [models.Index(fields=["project", "segment", "report_date", "status"])]


class DailyReportItem(TimeStampedModel):
    daily_report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name="items")
    budget_line = models.ForeignKey(ProjectBudgetLine, on_delete=models.PROTECT, related_name="daily_report_items")
    work_description = models.TextField()
    qty_done = models.DecimalField(max_digits=18, decimal_places=4)
    unit = models.CharField(max_length=30)

    class Meta:
        db_table = "erp_daily_report_items"


class MaterialUsage(TimeStampedModel):
    daily_report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name="material_usages")
    material_name = models.CharField(max_length=255)
    qty = models.DecimalField(max_digits=18, decimal_places=4)
    unit = models.CharField(max_length=30)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        db_table = "erp_material_usages"

    def save(self, *args, **kwargs):
        self.total_cost = self.qty * self.unit_cost
        super().save(*args, **kwargs)


class ProgressReport(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="progress_reports")
    segment = models.ForeignKey(ProjectSegment, on_delete=models.PROTECT, related_name="progress_reports")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="erp_progress_reports")
    report_number = models.CharField(max_length=80)
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "erp_progress_reports"
        constraints = [models.UniqueConstraint(fields=["project", "report_number"], name="uq_progress_report_number")]
        indexes = [models.Index(fields=["project", "segment", "period_start", "status"])]


class ProgressItem(TimeStampedModel):
    progress_report = models.ForeignKey(ProgressReport, on_delete=models.CASCADE, related_name="items")
    budget_line = models.ForeignKey(ProjectBudgetLine, on_delete=models.PROTECT, related_name="progress_items")
    previous_qty = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    current_qty = models.DecimalField(max_digits=18, decimal_places=4)
    approved_qty = models.DecimalField(max_digits=18, decimal_places=4, default=0)

    class Meta:
        db_table = "erp_progress_items"


class Invoice(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="invoices")
    purchase_order = models.ForeignKey(CustomerPurchaseOrder, on_delete=models.PROTECT, related_name="invoices")
    invoice_number = models.CharField(max_length=80)
    invoice_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    revision = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="erp_invoices")

    class Meta:
        db_table = "erp_sales_invoices"
        constraints = [models.UniqueConstraint(fields=["project", "invoice_number", "revision"], name="uq_invoice_revision")]
        indexes = [models.Index(fields=["project", "status", "invoice_date"])]

    def save(self, *args, **kwargs):
        self.total = self.subtotal + self.tax
        super().save(*args, **kwargs)


class InvoiceItem(TimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    progress_item = models.ForeignKey(ProgressItem, on_delete=models.PROTECT, null=True, blank=True, related_name="invoice_items")
    description = models.TextField()
    qty = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    item_type = models.CharField(max_length=30, default="PROGRESS")

    class Meta:
        db_table = "erp_invoice_items"

    def save(self, *args, **kwargs):
        self.amount = self.qty * self.unit_price
        super().save(*args, **kwargs)


class Payment(TimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    reference_number = models.CharField(max_length=100, unique=True)
    method = models.CharField(max_length=30, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="erp_payments")

    class Meta:
        db_table = "erp_payments"


class CashTransaction(TimeStampedModel):
    class Direction(models.TextChoices):
        IN = "IN", "Masuk"
        OUT = "OUT", "Keluar"

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="cash_transactions")
    transaction_date = models.DateField()
    direction = models.CharField(max_length=3, choices=Direction.choices)
    category = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    source_type = models.CharField(max_length=40)
    source_id = models.PositiveBigIntegerField()
    reference_number = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "erp_cash_transactions"
        indexes = [models.Index(fields=["project", "transaction_date"]), models.Index(fields=["source_type", "source_id"])]


class OfficeOverhead(TimeStampedModel):
    class Category(models.TextChoices):
        ELECTRICITY = "ELECTRICITY", "Listrik"
        SALARY = "SALARY", "Gaji Karyawan"
        MEALS = "MEALS", "Uang Makan"
        PETTY_CASH = "PETTY_CASH", "Petty Cash"
        INTERNET = "INTERNET", "Internet & Telepon"
        RENT = "RENT", "Sewa Kantor"
        TRANSPORT = "TRANSPORT", "Transportasi"
        SUPPLIES = "SUPPLIES", "ATK & Perlengkapan"
        OTHER = "OTHER", "Lain-lain"

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="office_overheads")
    expense_date = models.DateField()
    category = models.CharField(max_length=30, choices=Category.choices)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    attachment = models.FileField(upload_to="erp/attachments/overhead/%Y/%m/", blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="approved_office_overheads")
    approved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="office_overheads")

    class Meta:
        db_table = "erp_office_overheads"
        indexes = [models.Index(fields=["company", "expense_date", "category"])]
        ordering = ["-expense_date", "-id"]

    @property
    def is_approved(self):
        return bool(self.approved_by_id and self.approved_at)


class Approval(TimeStampedModel):
    class Decision(models.TextChoices):
        PENDING = "PENDING", "Menunggu"
        APPROVED = "APPROVED", "Disetujui"
        REVISION = "REVISION", "Revisi"
        REJECTED = "REJECTED", "Ditolak"

    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="erp_approvals")
    document_type = models.CharField(max_length=40)
    document_id = models.PositiveBigIntegerField()
    step_no = models.PositiveSmallIntegerField(default=1)
    decision = models.CharField(max_length=20, choices=Decision.choices, default=Decision.PENDING)
    notes = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "erp_approvals"
        constraints = [models.UniqueConstraint(fields=["document_type", "document_id", "step_no"], name="uq_document_approval_step")]
        indexes = [models.Index(fields=["document_type", "document_id", "step_no"])]


class Attachment(TimeStampedModel):
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="erp_attachments")
    document_type = models.CharField(max_length=40)
    document_id = models.PositiveBigIntegerField()
    file = models.FileField(upload_to="erp/attachments/%Y/%m/")
    original_name = models.CharField(max_length=255)

    class Meta:
        db_table = "erp_attachments"
        indexes = [models.Index(fields=["document_type", "document_id"])]


class ImportBatch(TimeStampedModel):
    class Status(models.TextChoices):
        UPLOADED = "UPLOADED", "Diunggah"
        VALIDATED = "VALIDATED", "Tervalidasi"
        POSTED = "POSTED", "Diposting"
        FAILED = "FAILED", "Gagal"

    file_name = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, unique=True)
    source_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADED)
    imported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="erp_import_batches")
    summary = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "erp_import_batches"


class ImportRow(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Menunggu"
        VALID = "VALID", "Valid"
        DUPLICATE = "DUPLICATE", "Duplikat"
        CONFLICT = "CONFLICT", "Konflik"
        INVALID = "INVALID", "Tidak Valid"
        POSTED = "POSTED", "Diposting"

    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="rows")
    sheet_name = models.CharField(max_length=255)
    row_number = models.PositiveIntegerField()
    business_key = models.CharField(max_length=255, blank=True)
    fingerprint = models.CharField(max_length=64)
    raw_payload = models.JSONField(default=dict)
    validation_errors = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        db_table = "erp_import_rows"
        constraints = [models.UniqueConstraint(fields=["batch", "sheet_name", "row_number"], name="uq_import_source_row")]
        indexes = [models.Index(fields=["business_key", "fingerprint"])]
