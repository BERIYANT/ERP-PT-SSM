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


def navigation(request):
    return {"global_navigation": GLOBAL_NAVIGATION}
