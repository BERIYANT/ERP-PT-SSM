from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import (
    Approval,
    CashTransaction,
    Disbursement,
    DocumentStatus,
    ExpenseReport,
    FundRequest,
    Invoice,
    Payment,
    ProgressItem,
)


def next_document_number(prefix, model, project, date_value=None, field_name=None):
    """Generate a project-scoped number while holding a database lock."""
    date_value = date_value or date.today()
    field_name = field_name or {
        FundRequest: "request_number",
        ExpenseReport: "report_number",
        Invoice: "invoice_number",
    }.get(model, "report_number")
    number_prefix = f"{prefix}/{project.project_code}/{date_value:%Y%m}/"
    with transaction.atomic():
        latest = (
            model.objects.select_for_update()
            .filter(project=project, **{f"{field_name}__startswith": number_prefix})
            .order_by(f"-{field_name}")
            .values_list(field_name, flat=True)
            .first()
        )
        sequence = int(latest.rsplit("/", 1)[-1]) + 1 if latest else 1
        return f"{number_prefix}{sequence:05d}"


def sync_fund_request_total(fund_request):
    total = fund_request.items.aggregate(value=Sum("amount"))["value"] or Decimal("0")
    fund_request.total_requested = total
    fund_request.save(update_fields=["total_requested", "updated_at"])
    return total


def sync_expense_total(expense_report):
    total = expense_report.items.aggregate(value=Sum("amount"))["value"] or Decimal("0")
    expense_report.total_actual = total
    expense_report.save(update_fields=["total_actual", "updated_at"])
    return total


def sync_invoice_total(invoice):
    subtotal = invoice.items.aggregate(value=Sum("amount"))["value"] or Decimal("0")
    invoice.subtotal = subtotal
    invoice.total = subtotal + invoice.tax
    invoice.save(update_fields=["subtotal", "total", "updated_at"])
    return invoice.total


def validate_budget_availability(budget_line, requested_amount, excluding_request=None):
    used = budget_line.fund_request_items.exclude(
        fund_request__status__in=[DocumentStatus.DRAFT, DocumentStatus.REJECTED, DocumentStatus.CANCELLED]
    )
    if excluding_request:
        used = used.exclude(fund_request=excluding_request)
    committed = used.aggregate(value=Sum("amount"))["value"] or Decimal("0")
    if committed + requested_amount > budget_line.planned_cost:
        raise ValidationError("Nilai pengajuan melebihi sisa anggaran RAB.")


def validate_progress_quantity(budget_line, current_qty, excluding_item=None):
    items = ProgressItem.objects.filter(
        budget_line=budget_line,
        progress_report__status=DocumentStatus.APPROVED,
    )
    if excluding_item:
        items = items.exclude(pk=excluding_item.pk)
    approved = items.aggregate(value=Sum("approved_qty"))["value"] or Decimal("0")
    if approved + current_qty > budget_line.planned_qty:
        raise ValidationError("Progres kumulatif melebihi volume RAB/PO.")


def record_approval(document, document_type, approver, decision, notes="", step_no=1):
    allowed = {choice for choice, _ in Approval.Decision.choices}
    if decision not in allowed:
        raise ValidationError("Keputusan persetujuan tidak valid.")
    return Approval.objects.update_or_create(
        document_type=document_type,
        document_id=document.pk,
        step_no=step_no,
        defaults={
            "approver": approver,
            "decision": decision,
            "notes": notes,
            "decided_at": timezone.now(),
        },
    )[0]


@transaction.atomic
def disburse_fund_request(fund_request, amount, method, reference_number, actor):
    locked = FundRequest.objects.select_for_update().get(pk=fund_request.pk)
    if locked.status != DocumentStatus.APPROVED:
        raise ValidationError("Dana hanya dapat dicairkan setelah pengajuan disetujui.")
    disbursed = locked.disbursements.aggregate(value=Sum("amount"))["value"] or Decimal("0")
    if amount <= 0 or disbursed + amount > locked.total_requested:
        raise ValidationError("Nominal pencairan tidak valid atau melebihi pengajuan.")
    disbursement = Disbursement.objects.create(
        fund_request=locked,
        disbursement_date=date.today(),
        amount=amount,
        method=method,
        reference_number=reference_number,
        created_by=actor,
    )
    CashTransaction.objects.create(
        project=locked.project,
        transaction_date=disbursement.disbursement_date,
        direction=CashTransaction.Direction.OUT,
        category="PENCAIRAN_DANA",
        amount=amount,
        source_type="DISBURSEMENT",
        source_id=disbursement.pk,
        reference_number=reference_number,
    )
    if disbursed + amount == locked.total_requested:
        locked.status = DocumentStatus.DISBURSED
        locked.save(update_fields=["status", "updated_at"])
    return disbursement


@transaction.atomic
def record_invoice_payment(invoice, amount, payment_date, reference_number, method, actor):
    locked = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if locked.status in {DocumentStatus.DRAFT, DocumentStatus.CANCELLED}:
        raise ValidationError("Invoice belum dapat menerima pembayaran.")
    paid = locked.payments.aggregate(value=Sum("amount"))["value"] or Decimal("0")
    if amount <= 0 or paid + amount > locked.total:
        raise ValidationError("Pembayaran tidak valid atau melebihi sisa piutang.")
    payment = Payment.objects.create(
        invoice=locked,
        payment_date=payment_date,
        amount=amount,
        reference_number=reference_number,
        method=method,
        created_by=actor,
    )
    CashTransaction.objects.create(
        project=locked.project,
        transaction_date=payment_date,
        direction=CashTransaction.Direction.IN,
        category="PEMBAYARAN_INVOICE",
        amount=amount,
        source_type="PAYMENT",
        source_id=payment.pk,
        reference_number=reference_number,
    )
    locked.status = DocumentStatus.PAID if paid + amount == locked.total else DocumentStatus.PARTIALLY_PAID
    locked.save(update_fields=["status", "updated_at"])
    return payment
