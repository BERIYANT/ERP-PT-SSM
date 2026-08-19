GLOBAL_NAVIGATION = [
    ("dashboard", "Beranda Workbook", "erp:dashboard"),
    ("projects", "Pilih Proyek", "erp:project-list"),
    ("purchase_orders", "PO & Cash In", "erp:po-list"),
    ("progress", "Progress Mandor", "erp:progress-list"),
    ("funds", "Pengajuan Dana", "erp:fund-list"),
    ("expenses", "Expense / Lap Keu", "erp:expense-list"),
    ("invoices", "Invoice", "erp:invoice-list"),
    ("cash_flow", "Cash Flow", "erp:cash-flow"),
    ("daily", "Laporan Harian", "erp:daily-list"),
    ("attendance", "Absensi", "erp:attendance-list"),
    ("reports", "Rekap Proyek", "erp:report-index"),
]


from .selectors import user_role


def navigation(request):
    menu = list(GLOBAL_NAVIGATION)
    role = user_role(request.user)
    if role in {"admin", "superadmin"}:
        menu.append(("office_overheads", "Overhead Kantor", "erp:office-overheads"))
    return {"global_navigation": menu}
