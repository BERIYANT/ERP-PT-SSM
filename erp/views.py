from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError

from django.db import models, transaction
from django.db.models import Count, Sum
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    AttendanceForm,
    DailyReportForm,
    DailyReportItemFormSet,
    ExpenseItemFormSet,
    ExpenseReportForm,
    FundRequestForm,
    FundRequestItemFormSet,
    InvoiceForm,
    InvoiceItemFormSet,
    MaterialUsageFormSet,
    ProgressItemFormSet,
    ProgressReportForm,
    ProjectForm,
    ProjectBudgetLineForm,
    ProjectMemberForm,
    ProjectSegmentForm,
    PurchaseOrderForm,
    PurchaseOrderItemFormSet,
)
from .models import (
    Approval,
    Attendance,
    CashTransaction,
    CustomerPurchaseOrder,
    DailyReport,
    DailyReportItem,
    Disbursement,
    DocumentStatus,
    ExpenseReport,
    FundRequest,
    ImportBatch,
    Invoice,
    MaterialUsage,
    Employee,
    Project,
    ProjectBudgetLine,
    ProjectMember,
    ProjectSegment,
    PurchaseOrderItem,
    ProgressReport,
    Role,
    UserOrganization,
)
from .selectors import may_approve, may_manage_master, project_for_user, projects_for_user, user_role
from .services import (
    disburse_fund_request,
    next_document_number,
    record_approval,
    record_invoice_payment,
    sync_expense_total,
    sync_fund_request_total,
    sync_invoice_total,
    validate_budget_availability,
    validate_progress_quantity,
)


def _base_context(active, title, **extra):
    return {"active_global_nav": active, "page_title": title, **extra}


def _project_context(project, active, title, **extra):
    return _base_context("projects", title, project=project, active_project_nav=active, **extra)


@login_required
def dashboard(request):
    projects = projects_for_user(request.user)
    cash_in = CashTransaction.objects.filter(project__in=projects, direction="IN").aggregate(value=Sum("amount"))["value"] or 0
    cash_out = CashTransaction.objects.filter(project__in=projects, direction="OUT").aggregate(value=Sum("amount"))["value"] or 0
    context = _base_context(
        "dashboard",
        "Dashboard ERP",
        projects=projects[:8],
        project_count=projects.count(),
        po_value=CustomerPurchaseOrder.objects.filter(project__in=projects).aggregate(value=Sum("contract_value"))["value"] or 0,
        cash_in=cash_in,
        cash_out=cash_out,
        balance=cash_in - cash_out,
        pending_funds=FundRequest.objects.filter(project__in=projects, status=DocumentStatus.SUBMITTED)[:8],
        pending_progress=ProgressReport.objects.filter(project__in=projects, status=DocumentStatus.SUBMITTED)[:8],
    )
    return render(request, "erp/pages/dashboard.html", context)


@login_required
def project_list(request):
    projects = projects_for_user(request.user)
    tab = request.GET.get("tab", "register")
    if tab not in {"register", "segments", "members"}:
        raise Http404
    context = _base_context(
        "projects",
        "Daftar Proyek",
        projects=projects,
        project_tab=tab,
        segments=ProjectSegment.objects.filter(project__in=projects).select_related("project").order_by("project__project_code", "segment_code") if tab == "segments" else (),
        project_members=ProjectMember.objects.filter(project__in=projects).select_related("project", "segment", "employee").order_by("project__project_code", "employee__name") if tab == "members" else (),
    )
    return render(request, "erp/pages/projects/list.html", context)


@login_required
@transaction.atomic
def project_form(request, project_id=None):
    if not may_manage_master(request.user):
        raise PermissionDenied
    instance = project_for_user(request.user, project_id) if project_id else None
    form = ProjectForm(request.POST or None, instance=instance)
    if form.is_valid():
        project = form.save(commit=False)
        project.full_clean()
        project.save()
        messages.success(request, "Proyek berhasil disimpan.")
        return redirect("erp:project-dashboard", project_id=project.pk)
    return render(request, "erp/pages/form.html", _base_context("projects", "Form Proyek", form=form, formset=None))


@login_required
def project_dashboard(request, project_id):
    project = project_for_user(request.user, project_id)
    sheet = request.GET.get("sheet", "control")
    if sheet not in {"control", "po-rab", "actual-cost", "invoice"}:
        raise Http404
    budgets = project.budget_lines.aggregate(value=Sum("planned_cost"))["value"] or 0
    progress = project.progress_reports.filter(status=DocumentStatus.APPROVED).count()
    context = _project_context(
        project,
        "dashboard",
        "Dashboard Proyek",
        budget_total=budgets,
        po_total=project.purchase_orders.aggregate(value=Sum("contract_value"))["value"] or 0,
        progress_count=progress,
        fund_total=project.fund_requests.aggregate(value=Sum("total_requested"))["value"] or 0,
        active_sheet=sheet,
        purchase_orders=project.purchase_orders.order_by("-po_date"),
        budget_lines=project.budget_lines.select_related("segment").order_by("cost_category", "line_code"),
        expenses=project.expense_reports.prefetch_related("items").order_by("-report_date"),
        invoices=project.invoices.prefetch_related("payments").order_by("-invoice_date"),
    )
    return render(request, "erp/pages/project/dashboard.html", context)


@login_required
def project_budget(request, project_id, category):
    project = project_for_user(request.user, project_id)
    category_map = {"services": "SERVICE", "materials": "MATERIAL", "overhead": "OVERHEAD", "petty-cash": "PETTY_CASH"}
    if category not in category_map:
        raise Http404
    tab = request.GET.get("tab", "worksheet")
    if tab not in {"worksheet", "segments", "variance"}:
        raise Http404
    lines = project.budget_lines.filter(cost_category=category_map[category]).select_related("segment", "po_item")
    title_map = {"services": "Jasa", "materials": "Material", "overhead": "Overhead Progress", "petty-cash": "Petty Cash"}
    segment_summary = lines.values("segment__segment_code", "segment__segment_name").annotate(total=Sum("planned_cost"), item_count=Count("id")).order_by("segment__segment_code") if tab == "segments" else ()
    return render(request, "erp/pages/project/budget.html", _project_context(project, category, title_map[category], budget_lines=lines, category=category, budget_tab=tab, segment_summary=segment_summary))


@login_required
@transaction.atomic
def project_budget_form(request, project_id, category, pk=None):
    project = project_for_user(request.user, project_id)
    category_map = {"services": "SERVICE", "materials": "MATERIAL", "overhead": "OVERHEAD", "petty-cash": "PETTY_CASH"}
    if category not in category_map:
        raise Http404
    if not may_manage_master(request.user):
        raise PermissionDenied
    instance = get_object_or_404(ProjectBudgetLine, pk=pk, project=project, cost_category=category_map[category]) if pk else None
    form = ProjectBudgetLineForm(request.POST or None, instance=instance)
    form.fields["segment"].queryset = project.segments.all()
    form.fields["po_item"].queryset = PurchaseOrderItem.objects.filter(purchase_order__project=project)
    if form.is_valid():
        line = form.save(commit=False)
        line.project = project
        line.cost_category = category_map[category]
        line.full_clean()
        line.save()
        messages.success(request, "Baris RAB berhasil disimpan.")
        return redirect(f"erp:project-{category}", project_id=project.id)
    return render(request, "erp/pages/form.html", _project_context(project, category, "Form RAB", form=form, formset=None))


@login_required
@require_POST
def project_budget_delete(request, project_id, category, pk):
    project = project_for_user(request.user, project_id)
    if not may_manage_master(request.user):
        raise PermissionDenied
    line = get_object_or_404(ProjectBudgetLine, pk=pk, project=project)
    try:
        line.delete()
        messages.success(request, "Baris RAB berhasil dihapus.")
    except ProtectedError:
        messages.error(request, "Baris RAB sudah dipakai transaksi dan tidak dapat dihapus.")
    return redirect(f"erp:project-{category}", project_id=project.id)


@login_required
def segment_form(request, project_id, pk=None):
    project = project_for_user(request.user, project_id)
    if not may_manage_master(request.user):
        raise PermissionDenied
    instance = get_object_or_404(ProjectSegment, pk=pk, project=project) if pk else None
    form = ProjectSegmentForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        segment = form.save(commit=False)
        segment.project = project
        segment.full_clean()
        segment.save()
        messages.success(request, "Segment berhasil disimpan.")
        return redirect(f"erp:project-dashboard", project_id=project.id)
    return render(request, "erp/pages/form.html", _project_context(project, "segments", "Form Segment", form=form, formset=None))


@login_required
@require_POST
def segment_delete(request, project_id, pk):
    project = project_for_user(request.user, project_id)
    if not may_manage_master(request.user):
        raise PermissionDenied
    segment = get_object_or_404(ProjectSegment, pk=pk, project=project)
    try:
        segment.delete()
        messages.success(request, "Segment berhasil dihapus.")
    except ProtectedError:
        messages.error(request, "Segment masih dipakai data lain dan tidak dapat dihapus.")
    return redirect(f"erp:project-dashboard", project_id=project.id)


@login_required
def member_form(request, project_id, pk=None):
    project = project_for_user(request.user, project_id)
    if not may_manage_master(request.user):
        raise PermissionDenied
    instance = get_object_or_404(ProjectMember, pk=pk, project=project) if pk else None
    form = ProjectMemberForm(request.POST or None, instance=instance)
    form.fields["segment"].queryset = project.segments.all()
    form.fields["employee"].queryset = Employee.objects.filter(company=project.company)
    if request.method == "POST" and form.is_valid():
        member = form.save(commit=False)
        member.project = project
        member.full_clean()
        member.save()
        messages.success(request, "Anggota proyek berhasil disimpan.")
        return redirect(f"erp:project-dashboard", project_id=project.id)
    return render(request, "erp/pages/form.html", _project_context(project, "members", "Form Anggota", form=form, formset=None))


@login_required
@require_POST
def member_delete(request, project_id, pk):
    project = project_for_user(request.user, project_id)
    if not may_manage_master(request.user):
        raise PermissionDenied
    member = get_object_or_404(ProjectMember, pk=pk, project=project)
    try:
        member.delete()
        messages.success(request, "Anggota proyek berhasil dihapus.")
    except ProtectedError:
        messages.error(request, "Anggota proyek masih dipakai data lain dan tidak dapat dihapus.")
    return redirect(f"erp:project-dashboard", project_id=project.id)


@login_required
def project_foreman_advances(request, project_id):
    project = project_for_user(request.user, project_id)
    funds = project.fund_requests.select_related("requested_by").prefetch_related("disbursements")
    return render(request, "erp/pages/project/foreman_advances.html", _project_context(project, "foreman_advances", "Kasbon Mandor", funds=funds))


def _document_list(request, model, active, title, template, select=(), document_type=None, edit_url_name=None):
    projects = projects_for_user(request.user)
    rows = model.objects.filter(project__in=projects)
    if select:
        rows = rows.select_related(*select)
    project_id = request.GET.get("project")
    status = request.GET.get("status")
    tab = request.GET.get("tab", "all")
    tab_statuses = {
        "all": None,
        "draft": [DocumentStatus.DRAFT],
        "approval": [DocumentStatus.SUBMITTED, DocumentStatus.REVIEWED, DocumentStatus.REVISION],
        "archive": [DocumentStatus.APPROVED, DocumentStatus.REJECTED, DocumentStatus.DISBURSED, DocumentStatus.VERIFIED, DocumentStatus.SETTLED, DocumentStatus.CLOSED, DocumentStatus.SENT, DocumentStatus.PARTIALLY_PAID, DocumentStatus.PAID, DocumentStatus.OVERDUE, DocumentStatus.CANCELLED],
    }
    if tab not in tab_statuses:
        raise Http404
    if project_id:
        rows = rows.filter(project_id=project_id)
    if status:
        rows = rows.filter(status=status)
    elif tab_statuses[tab]:
        rows = rows.filter(status__in=tab_statuses[tab])
    rows = list(rows.order_by("-created_at")[:200])
    display_fields = {
        CustomerPurchaseOrder: ("po_number", "po_date", "contract_value"),
        FundRequest: ("request_number", "request_date", "total_requested"),
        ExpenseReport: ("report_number", "report_date", "total_actual"),
        ProgressReport: ("report_number", "period_end", None),
        Invoice: ("invoice_number", "invoice_date", "total"),
    }
    number_field, date_field, value_field = display_fields[model]
    for row in rows:
        row.display_number = getattr(row, number_field)
        row.display_date = getattr(row, date_field)
        row.display_value = getattr(row, value_field) if value_field else Decimal("0")
    return render(
        request,
        template,
        _base_context(
            active,
            title,
            rows=rows,
            projects=projects,
            statuses=DocumentStatus.choices,
            document_type=document_type,
            document_tab=tab,
            selected_project=project_id or "",
            selected_status=status or "",
            edit_url_name=edit_url_name,
        ),
    )


@login_required
def po_list(request):
    return _document_list(request, CustomerPurchaseOrder, "purchase_orders", "Purchase Order", "erp/pages/documents/list.html", ("project",), "po", "erp:po-edit")


@login_required
def fund_list(request):
    return _document_list(request, FundRequest, "funds", "Pengajuan Dana", "erp/pages/documents/list.html", ("project", "requested_by"), "fund", "erp:fund-edit")


@login_required
def expense_list(request):
    return _document_list(request, ExpenseReport, "expenses", "Expense Report", "erp/pages/documents/list.html", ("project", "submitted_by"), "expense", "erp:expense-edit")


@login_required
def progress_list(request):
    return _document_list(request, ProgressReport, "progress", "Progres & Opname", "erp/pages/documents/list.html", ("project", "segment", "submitted_by"), "progress", "erp:progress-edit")


@login_required
def daily_list(request):
    projects = projects_for_user(request.user)
    tab = request.GET.get("tab", "reports")
    if tab not in {"reports", "items", "materials"}:
        raise Http404
    rows = DailyReport.objects.filter(project__in=projects).select_related("project", "segment", "submitted_by").order_by("-report_date", "-id")
    work_items = DailyReportItem.objects.filter(daily_report__project__in=projects).select_related("daily_report__project", "daily_report__segment", "budget_line").order_by("-daily_report__report_date", "-id") if tab == "items" else ()
    material_usages = MaterialUsage.objects.filter(daily_report__project__in=projects).select_related("daily_report__project", "daily_report__segment").order_by("-daily_report__report_date", "-id") if tab == "materials" else ()
    return render(request, "erp/pages/daily/list.html", _base_context("daily", "Laporan Harian", rows=rows[:300], projects=projects, daily_tab=tab, work_items=work_items[:300] if tab == "items" else (), material_usages=material_usages[:300] if tab == "materials" else ()))


@login_required
def attendance_list(request):
    projects = projects_for_user(request.user)
    tab = request.GET.get("tab", "register")
    if tab not in {"register", "project", "employee"}:
        raise Http404
    rows = Attendance.objects.filter(project__in=projects).select_related("project", "employee").order_by("-work_date", "employee__name")
    by_project = rows.values("project__project_code", "project__name").annotate(total=Count("id")).order_by("project__project_code") if tab == "project" else ()
    by_employee = rows.values("employee__employee_no", "employee__name").annotate(total=Count("id")).order_by("employee__name") if tab == "employee" else ()
    return render(request, "erp/pages/attendance/list.html", _base_context("attendance", "Absensi", rows=rows[:300], projects=projects, attendance_tab=tab, by_project=by_project, by_employee=by_employee))


@login_required
def invoice_list(request):
    return _document_list(request, Invoice, "invoices", "Invoice", "erp/pages/documents/list.html", ("project", "purchase_order"), "invoice", "erp:invoice-edit")


def _save_header_detail(request, form_class, formset_class, instance, active, title, prepare):
    form = form_class(request.POST or None, instance=instance)
    formset = formset_class(request.POST or None, instance=instance, prefix="items")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            document = form.save(commit=False)
            prepare(document)
            document.full_clean()
            document.save()
            formset.instance = document
            children = formset.save(commit=False)
            for deleted in formset.deleted_objects:
                deleted.delete()
            for child in children:
                child.full_clean()
                child.save()
            formset.save_m2m()
            return document
    return render(request, "erp/pages/form.html", _base_context(active, title, form=form, formset=formset))


@login_required
def po_form(request, pk=None):
    if not may_manage_master(request.user):
        raise PermissionDenied
    instance = get_object_or_404(CustomerPurchaseOrder, pk=pk, project__in=projects_for_user(request.user)) if pk else CustomerPurchaseOrder()
    result = _save_header_detail(request, PurchaseOrderForm, PurchaseOrderItemFormSet, instance, "purchase_orders", "Form Purchase Order", lambda obj: setattr(obj, "created_by", request.user))
    if isinstance(result, CustomerPurchaseOrder):
        messages.success(request, "Purchase Order berhasil disimpan.")
        return redirect("erp:po-list")
    return result


@login_required
def fund_form(request, pk=None):
    instance = get_object_or_404(FundRequest, pk=pk, project__in=projects_for_user(request.user)) if pk else FundRequest()
    def prepare(obj):
        obj.requested_by = request.user
        obj.request_number = obj.request_number or next_document_number("PD", FundRequest, obj.project, obj.request_date, "request_number")
    result = _save_header_detail(request, FundRequestForm, FundRequestItemFormSet, instance, "funds", "Form Pengajuan Dana", prepare)
    if isinstance(result, FundRequest):
        for item in result.items.select_related("budget_line"):
            validate_budget_availability(item.budget_line, item.amount, result)
        sync_fund_request_total(result)
        messages.success(request, "Pengajuan dana berhasil disimpan.")
        return redirect("erp:fund-list")
    return result


@login_required
def expense_form(request, pk=None):
    instance = get_object_or_404(ExpenseReport, pk=pk, project__in=projects_for_user(request.user)) if pk else ExpenseReport()
    def prepare(obj):
        obj.submitted_by = request.user
        obj.report_number = obj.report_number or next_document_number("ER", ExpenseReport, obj.project, obj.report_date, "report_number")
    result = _save_header_detail(request, ExpenseReportForm, ExpenseItemFormSet, instance, "expenses", "Form Expense Report", prepare)
    if isinstance(result, ExpenseReport):
        sync_expense_total(result)
        messages.success(request, "Expense Report berhasil disimpan.")
        return redirect("erp:expense-list")
    return result


@login_required
def progress_form(request, pk=None):
    instance = get_object_or_404(ProgressReport, pk=pk, project__in=projects_for_user(request.user)) if pk else ProgressReport()
    def prepare(obj):
        obj.submitted_by = request.user
        obj.report_number = obj.report_number or next_document_number("OP", ProgressReport, obj.project, obj.period_end, "report_number")
    result = _save_header_detail(request, ProgressReportForm, ProgressItemFormSet, instance, "progress", "Form Progres & Opname", prepare)
    if isinstance(result, ProgressReport):
        for item in result.items.select_related("budget_line"):
            validate_progress_quantity(item.budget_line, item.current_qty, item)
        messages.success(request, "Progres berhasil disimpan.")
        return redirect("erp:progress-list")
    return result


@login_required
@transaction.atomic
def attendance_form(request, pk=None):
    organization = UserOrganization.objects.filter(user=request.user).select_related("employee").first()
    employee = organization.employee if organization else None
    if not employee:
        raise PermissionDenied("Akun belum terhubung ke data pegawai.")
    instance = get_object_or_404(Attendance, pk=pk, project__in=projects_for_user(request.user)) if pk else None
    if instance and instance.employee_id != employee.id and not may_manage_master(request.user):
        raise PermissionDenied
    form = AttendanceForm(request.POST or None, instance=instance)
    form.fields["project"].queryset = projects_for_user(request.user)
    if form.is_valid():
        attendance = form.save(commit=False)
        attendance.employee = employee
        attendance.full_clean()
        attendance.save()
        messages.success(request, "Absensi berhasil disimpan.")
        return redirect("erp:attendance-list")
    return render(request, "erp/pages/form.html", _base_context("attendance", "Form Absensi", form=form, formset=None))


@login_required
@transaction.atomic
def daily_form(request, pk=None):
    instance = get_object_or_404(DailyReport, pk=pk, project__in=projects_for_user(request.user)) if pk else DailyReport()
    form = DailyReportForm(request.POST or None, instance=instance)
    work_items = DailyReportItemFormSet(request.POST or None, instance=instance, prefix="items")
    materials = MaterialUsageFormSet(request.POST or None, instance=instance, prefix="materials")
    form.fields["project"].queryset = projects_for_user(request.user)
    if request.method == "POST" and form.is_valid() and work_items.is_valid() and materials.is_valid():
        report = form.save(commit=False)
        report.submitted_by = request.user
        report.report_number = report.report_number or next_document_number("LH", DailyReport, report.project, report.report_date, "report_number")
        if report.segment.project_id != report.project_id:
            raise ValidationError("Segmen tidak berasal dari proyek yang dipilih.")
        report.full_clean()
        report.save()
        for formset in (work_items, materials):
            formset.instance = report
            children = formset.save(commit=False)
            for deleted in formset.deleted_objects:
                deleted.delete()
            for child in children:
                child.full_clean()
                child.save()
            formset.save_m2m()
        messages.success(request, "Laporan harian berhasil disimpan.")
        return redirect("erp:daily-list")
    return render(request, "erp/pages/daily/form.html", _base_context("daily", "Form Laporan Harian", form=form, work_items=work_items, materials=materials))


@login_required
def invoice_form(request, pk=None):
    if not may_manage_master(request.user):
        raise PermissionDenied
    instance = get_object_or_404(Invoice, pk=pk, project__in=projects_for_user(request.user)) if pk else Invoice()
    def prepare(obj):
        obj.created_by = request.user
        obj.invoice_number = obj.invoice_number or next_document_number("INV", Invoice, obj.project, obj.invoice_date, "invoice_number")
    result = _save_header_detail(request, InvoiceForm, InvoiceItemFormSet, instance, "invoices", "Form Invoice", prepare)
    if isinstance(result, Invoice):
        sync_invoice_total(result)
        messages.success(request, "Invoice berhasil disimpan.")
        return redirect("erp:invoice-list")
    return result


@login_required
@require_POST
@transaction.atomic
def document_action(request, document_type, pk, action):
    mapping = {
        "po": CustomerPurchaseOrder,
        "fund": FundRequest,
        "expense": ExpenseReport,
        "progress": ProgressReport,
        "invoice": Invoice,
    }
    if document_type not in mapping or action not in {"submit", "approve", "revision", "reject"}:
        raise Http404
    document = get_object_or_404(mapping[document_type].objects.select_for_update(), pk=pk, project__in=projects_for_user(request.user))
    if action == "submit":
        if document.status not in {DocumentStatus.DRAFT, DocumentStatus.REVISION}:
            raise ValidationError("Dokumen tidak dapat diajukan dari status ini.")
        document.status = DocumentStatus.SUBMITTED
    else:
        if not may_approve(request.user):
            raise PermissionDenied
        status_map = {"approve": DocumentStatus.APPROVED, "revision": DocumentStatus.REVISION, "reject": DocumentStatus.REJECTED}
        document.status = status_map[action]
        record_approval(document, document_type.upper(), request.user, status_map[action], request.POST.get("notes", ""))
    document.save(update_fields=["status", "updated_at"])
    messages.success(request, "Status dokumen berhasil diperbarui.")
    return redirect(f"erp:{document_type}-list")


@login_required
@require_POST
@transaction.atomic
def document_delete(request, document_type, pk):
    mapping = {
        "po": (CustomerPurchaseOrder, "erp:po-list"),
        "fund": (FundRequest, "erp:fund-list"),
        "expense": (ExpenseReport, "erp:expense-list"),
        "progress": (ProgressReport, "erp:progress-list"),
        "invoice": (Invoice, "erp:invoice-list"),
        "daily": (DailyReport, "erp:daily-list"),
        "attendance": (Attendance, "erp:attendance-list"),
    }
    if document_type not in mapping:
        raise Http404
    model, redirect_name = mapping[document_type]
    obj = get_object_or_404(model, pk=pk, project__in=projects_for_user(request.user))
    if hasattr(obj, "status") and obj.status not in {DocumentStatus.DRAFT, DocumentStatus.REVISION}:
        messages.error(request, "Hanya data Draft atau Perlu Revisi yang dapat dihapus.")
        return redirect(redirect_name)
    try:
        obj.delete()
        messages.success(request, "Data berhasil dihapus.")
    except ProtectedError:
        messages.error(request, "Data tidak dapat dihapus karena sudah digunakan transaksi lain.")
    return redirect(redirect_name)


@login_required
@require_POST
def project_delete(request, project_id):
    if not may_manage_master(request.user):
        raise PermissionDenied
    project = project_for_user(request.user, project_id)
    try:
        project.delete()
        messages.success(request, "Proyek berhasil dihapus.")
    except ProtectedError:
        messages.error(request, "Proyek ini masih dipakai data lain dan tidak dapat dihapus.")
    return redirect("erp:project-list")


@login_required
@require_POST
def project_deactivate(request, project_id):
    if not may_manage_master(request.user):
        raise PermissionDenied
    project = project_for_user(request.user, project_id)
    project.is_active = False
    project.status = "INACTIVE"
    project.save(update_fields=["is_active", "status", "updated_at"])
    messages.success(request, "Proyek berhasil dinonaktifkan.")
    return redirect("erp:project-list")


@login_required
def cash_flow(request):
    projects = projects_for_user(request.user)
    transactions = CashTransaction.objects.filter(project__in=projects).select_related("project").order_by("-transaction_date", "-id")
    project_id = request.GET.get("project")
    tab = request.GET.get("tab", "all")
    if tab not in {"all", "in", "out", "project"}:
        raise Http404
    if project_id:
        transactions = transactions.filter(project_id=project_id)
    if tab == "in":
        transactions = transactions.filter(direction=CashTransaction.Direction.IN)
    elif tab == "out":
        transactions = transactions.filter(direction=CashTransaction.Direction.OUT)
    cash_in = transactions.filter(direction="IN").aggregate(value=Sum("amount"))["value"] or 0
    cash_out = transactions.filter(direction="OUT").aggregate(value=Sum("amount"))["value"] or 0
    project_summary = transactions.values("project__project_code", "project__name").annotate(
        cash_in=Sum("amount", filter=models.Q(direction=CashTransaction.Direction.IN)),
        cash_out=Sum("amount", filter=models.Q(direction=CashTransaction.Direction.OUT)),
    ).order_by("project__project_code") if tab == "project" else ()
    return render(request, "erp/pages/cash_flow/index.html", _base_context("cash_flow", "Cash Flow", transactions=transactions[:300], projects=projects, cash_in=cash_in, cash_out=cash_out, balance=cash_in-cash_out, cash_tab=tab, selected_project=project_id or "", project_summary=project_summary))


@login_required
def reports(request):
    projects = projects_for_user(request.user)
    tab = request.GET.get("tab", "profitability")
    if tab not in {"profitability", "budget", "progress", "aging"}:
        raise Http404
    rows = []
    for project in projects:
        po = project.purchase_orders.aggregate(value=Sum("contract_value"))["value"] or 0
        budget = project.budget_lines.aggregate(value=Sum("planned_cost"))["value"] or 0
        actual = project.expense_reports.filter(status__in=[DocumentStatus.VERIFIED, DocumentStatus.SETTLED, DocumentStatus.CLOSED]).aggregate(value=Sum("total_actual"))["value"] or 0
        rows.append({"project": project, "po": po, "budget": budget, "actual": actual, "margin": po-actual})
    aging_rows = Invoice.objects.filter(project__in=projects).select_related("project").order_by("due_date", "invoice_date") if tab == "aging" else ()
    return render(request, "erp/pages/reports/index.html", _base_context("reports", "Laporan Proyek", report_rows=rows, report_tab=tab, aging_rows=aging_rows))


@login_required
def profile(request):
    organization = UserOrganization.objects.filter(user=request.user).select_related("company", "employee", "role").first()
    return render(request, "erp/pages/account/profile.html", _base_context("", "Profil Pengguna", organization=organization))


@login_required
def administration(request):
    if not may_manage_master(request.user):
        raise PermissionDenied
    try:
        company = request.user.organization.company
    except (AttributeError, request.user.__class__.organization.RelatedObjectDoesNotExist):
        company = None
    employees = Employee.objects.filter(company=company).order_by("name") if company else Employee.objects.none()
    accounts = UserOrganization.objects.filter(company=company).select_related("user", "employee", "role") if company else UserOrganization.objects.none()
    return render(request, "erp/pages/administration/index.html", _base_context("", "Administrasi Sistem", company=company, employees=employees, accounts=accounts, roles=Role.objects.all()))


@login_required
def audit(request):
    approvals = Approval.objects.select_related("approver").order_by("-decided_at")[:200]
    imports = ImportBatch.objects.select_related("imported_by").order_by("-created_at")[:50]
    return render(request, "erp/pages/audit/index.html", _base_context("audit", "Audit Aktivitas", approvals=approvals, imports=imports))
