from django import forms
from django.forms import inlineformset_factory

from .models import (
    Attendance,
    CustomerPurchaseOrder,
    DailyReport,
    DailyReportItem,
    ExpenseItem,
    ExpenseReport,
    FundRequest,
    FundRequestItem,
    Invoice,
    InvoiceItem,
    MaterialUsage,
    ProgressItem,
    ProgressReport,
    Project,
    ProjectBudgetLine,
    ProjectMember,
    ProjectSegment,
    PurchaseOrderItem,
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
    class Meta:
        model = ProjectBudgetLine
        fields = ["segment", "po_item", "line_code", "description", "unit", "planned_qty", "unit_cost", "version", "status"]

    _field_spans = {
        "segment":     "span-1",
        "po_item":     "span-1",
        "line_code":   "span-1",
        "description": "span-3",
        "unit":        "span-1",
        "planned_qty": "span-1",
        "unit_cost":   "span-1",
        "version":     "span-1",
        "status":      "span-1",
    }


class PurchaseOrderForm(StyledModelForm):
    class Meta:
        model = CustomerPurchaseOrder
        fields = ["project", "po_number", "po_date", "contract_value", "tax_percent", "status"]
        widgets = {
            "po_date": forms.DateInput(attrs={"type": "date"}),
        }

    _field_spans = {
        "project":        "span-3",  # full row
        "po_number":      "span-1",
        "po_date":        "span-1",
        "contract_value": "span-1",
        "tax_percent":    "span-1",
        "status":         "span-1",
    }


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
        fields = ["project", "purchase_order", "invoice_date", "due_date", "tax"]
        widgets = {
            "invoice_date": forms.DateInput(attrs={"type": "date"}),
            "due_date":     forms.DateInput(attrs={"type": "date"}),
        }

    _field_spans = {
        "project":        "span-1",
        "purchase_order": "span-2",
        "invoice_date":   "span-1",
        "due_date":       "span-1",
        "tax":            "span-1",
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
    fields=["material_name", "qty", "unit", "unit_cost"],
    extra=1, can_delete=True,
)
