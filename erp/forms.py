from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory

from .models import (
    Attendance,
    BusinessPartner,
    CustomerPurchaseOrder,
    DailyReport,
    DailyReportItem,
    Employee,
    ExpenseItem,
    ExpenseReport,
    FundRequest,
    FundRequestItem,
    Invoice,
    InvoiceItem,
    MaterialUsage,
    MaterialMovement,
    OfficeOverhead,
    ProgressItem,
    ProgressReport,
    Project,
    ProjectBudgetLine,
    ProjectMember,
    ProjectSegment,
    PurchaseOrderItem,
    Role,
    UserOrganization,
    WarehouseMaterial,
)


class StyledModelForm(forms.ModelForm):
    """Base form: applies form-control class and injects data-span from _field_spans."""

    _field_spans: dict = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            span = self._field_spans.get(name, "span-1")
            field.widget.attrs["data-span"] = span


class AdministrationUserForm(forms.Form):
    username = forms.CharField(label="Username", max_length=100)
    nama = forms.CharField(label="Nama Lengkap", max_length=150)
    email = forms.EmailField(label="Email", required=False)
    role = forms.ModelChoiceField(label="Role", queryset=Role.objects.none())
    employee = forms.ModelChoiceField(label="Pegawai", queryset=Employee.objects.none(), required=False)
    password = forms.CharField(label="Password Baru", widget=forms.PasswordInput, required=False)
    is_active = forms.BooleanField(label="Akun Aktif", required=False, initial=True)

    def __init__(self, *args, company=None, user_instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        self.user_instance = user_instance
        self.fields["role"].queryset = Role.objects.order_by("name")
        self.fields["employee"].queryset = Employee.objects.filter(company=company).order_by("name") if company else Employee.objects.none()
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        if user_instance and not self.is_bound:
            organization = UserOrganization.objects.filter(user=user_instance).first()
            self.initial.update({
                "username": user_instance.username,
                "nama": user_instance.nama,
                "email": user_instance.email or "",
                "role": organization.role_id if organization else None,
                "employee": organization.employee_id if organization else None,
                "is_active": user_instance.is_active,
            })

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        queryset = get_user_model().objects.filter(username__iexact=username)
        if self.user_instance:
            queryset = queryset.exclude(pk=self.user_instance.pk)
        if queryset.exists():
            raise forms.ValidationError("Username sudah digunakan.")
        return username

    def clean_employee(self):
        employee = self.cleaned_data.get("employee")
        if employee and UserOrganization.objects.filter(employee=employee).exclude(user=self.user_instance).exists():
            raise forms.ValidationError("Pegawai sudah terhubung ke akun lain.")
        return employee

    def clean_password(self):
        password = self.cleaned_data.get("password", "")
        if not self.user_instance and not password:
            raise forms.ValidationError("Password wajib diisi untuk akun baru.")
        if password and len(password) < 8:
            raise forms.ValidationError("Password minimal 8 karakter.")
        return password


class OfficeOverheadForm(StyledModelForm):
    class Meta:
        model = OfficeOverhead
        fields = ["expense_date", "category", "description", "amount", "attachment", "notes"]
        widgets = {"expense_date": forms.DateInput(attrs={"type": "date"}), "amount": forms.NumberInput(attrs={"min": "0", "step": "1"}), "notes": forms.Textarea(attrs={"rows": 3})}
        labels = {"expense_date": "Tanggal", "category": "Kategori", "description": "Keterangan", "amount": "Nominal", "attachment": "Upload Foto Bukti", "notes": "Catatan"}

    _field_spans = {"expense_date": "span-1", "category": "span-1", "description": "span-2", "amount": "span-1", "attachment": "span-1", "notes": "span-3"}


class WarehouseMaterialForm(StyledModelForm):
    class Meta:
        model = WarehouseMaterial
        fields = ["name", "description", "unit", "warehouse_qty", "image", "is_active"]
        labels = {"name": "Nama Material", "description": "Deskripsi", "unit": "Satuan", "warehouse_qty": "Stok Awal / Stok Gudang", "image": "Gambar Contoh Material", "is_active": "Material Aktif"}
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "warehouse_qty": forms.NumberInput(attrs={"min": "0", "step": "0.0001"}),
        }

    _field_spans = {"name": "span-2", "description": "span-3", "unit": "span-1", "warehouse_qty": "span-1", "image": "span-2", "is_active": "span-1"}


class MaterialMovementForm(StyledModelForm):
    class Meta:
        model = MaterialMovement
        fields = ["material", "project", "quantity", "movement_date", "notes"]
        labels = {"material": "Material", "project": "Proyek Tujuan", "quantity": "Jumlah", "movement_date": "Tanggal", "notes": "Keterangan"}
        widgets = {
            "quantity": forms.NumberInput(attrs={"min": "0.0001", "step": "0.0001"}),
            "movement_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    _field_spans = {"material": "span-1", "project": "span-1", "quantity": "span-1", "movement_date": "span-1", "notes": "span-3"}

    def __init__(self, *args, company=None, projects=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["material"].queryset = WarehouseMaterial.objects.filter(company=company, is_active=True).order_by("name") if company else WarehouseMaterial.objects.none()
        self.fields["project"].queryset = projects if projects is not None else Project.objects.none()


class ProjectForm(StyledModelForm):
    class Meta:
        model = Project
        fields = ["company", "client", "project_code", "name", "start_date", "end_date", "status"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date":   forms.DateInput(attrs={"type": "date"}),
        }

    _field_spans = {
        "company":      "span-1",
        "client":       "span-1",
        "project_code": "span-1",
        "name":         "span-3",  # full row
        "start_date":   "span-1",
        "end_date":     "span-1",
        "status":       "span-1",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project_code"].label = "Segmen"
        self.fields["name"].label = "Nama Proyek"

    def clean(self):
        cleaned_data = super().clean()
        company = cleaned_data.get("company")
        project_code = cleaned_data.get("project_code")
        if company and project_code:
            existing = Project.objects.filter(
                company=company,
                project_code__iexact=project_code.strip(),
            ).exclude(pk=self.instance.pk if self.instance else None).first()
            if existing:
                self.add_error(
                    "project_code",
                    "Data Ini Sudah Ada",
                )
        return cleaned_data


class ClientForm(StyledModelForm):
    class Meta:
        model = BusinessPartner
        fields = ["company", "name", "address"]
        labels = {"name": "Nama Client", "address": "Alamat"}


class ProjectSegmentForm(StyledModelForm):
    class Meta:
        model = ProjectSegment
        fields = ["segment_code", "segment_name", "location", "is_active"]

    _field_spans = {
        "segment_code":  "span-1",
        "segment_name":  "span-2",
        "location":      "span-2",
        "is_active":     "span-1",
    }


class ProjectMemberForm(StyledModelForm):
    class Meta:
        model = ProjectMember
        fields = ["segment", "employee", "assignment_role", "assigned_at", "ended_at", "is_active"]
        widgets = {
            "assigned_at": forms.DateInput(attrs={"type": "date"}),
            "ended_at":    forms.DateInput(attrs={"type": "date"}),
        }

    _field_spans = {
        "segment":         "span-1",
        "employee":        "span-1",
        "assignment_role": "span-1",
        "assigned_at":     "span-1",
        "ended_at":        "span-1",
        "is_active":       "span-1",
    }


class ProjectBudgetLineForm(StyledModelForm):
    segment_name = forms.ChoiceField(label="Segmen")
    total_rab = forms.DecimalField(label="Total RAB", required=False, disabled=True)

    class Meta:
        model = ProjectBudgetLine
        fields = ["segment_name", "line_code", "foreman_name", "worker_count", "span", "description", "expense_purpose", "unit", "planned_qty", "unit_cost", "total_rab", "status"]

    _field_spans = {
        "segment_name":"span-1",
        "line_code":   "span-1",
        "description": "span-3",
        "unit":        "span-1",
        "planned_qty": "span-1",
        "unit_cost":   "span-1",
        "status":      "span-1",
    }

    def __init__(self, *args, category="materials", project=None, **kwargs):
        super().__init__(*args, **kwargs)
        segments = project.segments.order_by("segment_name") if project else ProjectSegment.objects.none()
        self.fields["segment_name"].choices = [(item.segment_name, item.segment_name) for item in segments]
        if self.instance and self.instance.segment_id:
            self.fields["segment_name"].initial = self.instance.segment.segment_name
        self.fields["total_rab"].initial = self.instance.planned_cost if self.instance and self.instance.pk else 0
        self.fields["planned_qty"].widget.attrs["step"] = "1"
        if category == "materials":
            self.fields["line_code"].label = "Nama Item"
            self.fields["unit"].label = "Satuan"
            self.fields["unit"].widget = forms.Select(choices=[("Meter", "Meter"), ("Pcs", "Pcs"), ("Roll", "Roll"), ("Set", "Set")])
            self.fields["planned_qty"].label = "Volume"
            self.fields.pop("foreman_name")
            self.fields.pop("expense_purpose")
            for name in ("worker_count", "span", "total_rab"):
                self.fields.pop(name)
        elif category == "services":
            self.fields["foreman_name"].label = "Nama Mandor"
            self.fields["line_code"].label = "Jenis Pekerjaan"
            self.fields["unit"].widget = forms.HiddenInput()
            self.fields["unit"].initial = "Meter"
            self.fields["planned_qty"].label = "Panjang Kabel (Meter)"
            self.fields["unit_cost"].label = "Harga per Meter"
            self.fields.pop("expense_purpose")
            self.fields.pop("worker_count")
            self.fields.pop("span")
        elif category == "petty-cash":
            self.fields["foreman_name"].label = "Nama Mandor"
            self.fields["description"].label = "Deskripsi"
            self.fields["expense_purpose"].label = "Tujuan Pengeluaran"
            self.fields["unit_cost"].label = "Nominal"
            for name in ("line_code", "unit", "planned_qty"):
                self.fields.pop(name)
            for name in ("worker_count", "span", "total_rab"):
                self.fields.pop(name)
        else:
            self.fields["foreman_name"].label = "Nama Mandor"
            self.fields["worker_count"].label = "Jumlah Pekerja"
            self.fields["span"].label = "Span"
            self.fields["line_code"].label = "Item Pekerjaan"
            self.fields["description"].label = "Keterangan"
            self.fields["planned_qty"].label = "Volume Progress"
            self.fields["unit_cost"].label = "Harga Satuan"
            self.fields["total_rab"].label = "Nilai Opname"
            self.fields.pop("expense_purpose")


class PurchaseOrderForm(StyledModelForm):
    class Meta:
        model = CustomerPurchaseOrder
        fields = ["project", "po_number", "po_date", "contract_value", "tax_percent", "status"]
        widgets = {
            "po_date": forms.DateInput(attrs={"type": "date"}),
            "contract_value": forms.NumberInput(attrs={"step": "any", "placeholder": "0"}),
            "tax_percent": forms.NumberInput(attrs={"step": "any", "placeholder": "11"}),
        }
        labels = {
            "project": "Project",
            "po_number": "No PO",
            "po_date": "Tanggal PO",
            "contract_value": "Nilai PO (Tanpa PPN)",
            "tax_percent": "PPN (%)",
            "status": "Status",
        }
        help_texts = {
            "contract_value": "Nilai PO dasar tanpa PPN.",
            "tax_percent": "Persentase PPN (misal 11%).",
        }

    _field_spans = {
        "project":        "span-3",  # full row
        "po_number":      "span-1",
        "po_date":        "span-1",
        "contract_value": "span-1",
        "tax_percent":    "span-1",
        "status":         "span-1",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and "tax_percent" in self.fields and self.initial.get("tax_percent") is None:
            self.fields["tax_percent"].initial = 11
        self.fields["contract_value"].label = "Nilai PO (Tanpa PPN)"
        self.fields["tax_percent"].label = "PPN (%)"



class FundRequestForm(StyledModelForm):
    class Meta:
        model = FundRequest
        fields = ["project", "request_date", "purpose"]
        widgets = {
            "request_date": forms.DateInput(attrs={"type": "date"}),
        }

    _field_spans = {
        "project":      "span-2",
        "request_date": "span-1",
        "purpose":      "span-3",  # full row / textarea
    }


class ExpenseReportForm(StyledModelForm):
    class Meta:
        model = ExpenseReport
        fields = ["project", "fund_request", "report_date"]
        widgets = {
            "report_date": forms.DateInput(attrs={"type": "date"}),
        }

    _field_spans = {
        "project":      "span-1",
        "fund_request": "span-1",
        "report_date":  "span-1",
    }


class ProgressReportForm(StyledModelForm):
    class Meta:
        model = ProgressReport
        fields = ["project", "segment", "period_start", "period_end"]
        widgets = {
            "period_start": forms.DateInput(attrs={"type": "date"}),
            "period_end":   forms.DateInput(attrs={"type": "date"}),
        }

    _field_spans = {
        "project":      "span-1",
        "segment":      "span-1",
        "period_start": "span-1",
        "period_end":   "span-1",
    }


class InvoiceForm(StyledModelForm):
    class Meta:
        model = Invoice
        fields = ["project", "purchase_order", "invoice_date", "due_date", "status"]
        widgets = {
            "invoice_date": forms.DateInput(attrs={"type": "date"}),
            "due_date":     forms.DateInput(attrs={"type": "date"}),
        }

    _field_spans = {
        "project":        "span-1",
        "purchase_order": "span-2",
        "invoice_date":   "span-1",
        "due_date":       "span-1",
        "status":         "span-1",
    }


class AttendanceForm(StyledModelForm):
    class Meta:
        model = Attendance
        fields = ["project", "work_date", "check_in", "check_out", "latitude", "longitude"]
        widgets = {
            "work_date": forms.DateInput(attrs={"type": "date"}),
            "check_in":  forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "check_out": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    _field_spans = {
        "project":   "span-3",  # full row
        "work_date": "span-1",
        "check_in":  "span-1",
        "check_out": "span-1",
        "latitude":  "span-1",
        "longitude": "span-1",
    }


class DailyReportForm(StyledModelForm):
    class Meta:
        model = DailyReport
        fields = ["project", "segment", "report_date", "weather", "notes"]
        widgets = {
            "report_date": forms.DateInput(attrs={"type": "date"}),
        }

    _field_spans = {
        "project":     "span-1",
        "segment":     "span-1",
        "report_date": "span-1",
        "weather":     "span-1",
        "notes":       "span-3",  # full row / textarea
    }


# ── Inline formsets ────────────────────────────────────────────────────────────

PurchaseOrderItemFormSet = inlineformset_factory(
    CustomerPurchaseOrder, PurchaseOrderItem,
    fields=["item_code", "description", "unit", "qty", "unit_price"],
    extra=1, can_delete=True,
)

FundRequestItemFormSet = inlineformset_factory(
    FundRequest, FundRequestItem,
    fields=["budget_line", "description", "qty", "unit_price"],
    extra=1, can_delete=True,
)

ExpenseItemFormSet = inlineformset_factory(
    ExpenseReport, ExpenseItem,
    fields=["budget_line", "expense_date", "category", "description", "amount"],
    widgets={"expense_date": forms.DateInput(attrs={"type": "date"})},
    extra=1, can_delete=True,
)

ProgressItemFormSet = inlineformset_factory(
    ProgressReport, ProgressItem,
    fields=["budget_line", "previous_qty", "current_qty", "approved_qty"],
    extra=1, can_delete=True,
)

InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem,
    fields=["progress_item", "description", "qty", "unit_price", "item_type"],
    extra=1, can_delete=True,
)

DailyReportItemFormSet = inlineformset_factory(
    DailyReport, DailyReportItem,
    fields=["budget_line", "work_description", "qty_done", "unit"],
    extra=1, can_delete=True,
)

MaterialUsageFormSet = inlineformset_factory(
    DailyReport, MaterialUsage,
    fields=["material_name", "qty", "unit"],
    extra=1, can_delete=True,
)
