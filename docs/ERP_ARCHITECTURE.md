# Arsitektur ERP Proyek SSM

## Tujuan

App `erp` menggantikan lembar kerja operasional dengan transaksi terstruktur. App `portal` lama tetap tersedia agar fitur lama dan akun pengguna tidak rusak selama transisi.

## Struktur kode

- `erp/models.py`: struktur database dan invariant lintas relasi.
- `erp/selectors.py`: pembatasan data berdasarkan perusahaan, proyek, segmen, dan role.
- `erp/forms.py`: validasi input header-detail.
- `erp/services.py`: penomoran, kalkulasi total, approval, pencairan, pembayaran, dan ledger.
- `erp/views.py`: alur HTTP; tidak menyimpan formula bisnis.
- `erp/management/commands/import_erp_excel.py`: staging sumber Excel yang idempoten.
- `templates/erp`: shell global, workspace proyek, dan halaman modul.

## Domain data

1. Organisasi: Company, Employee, Role, UserOrganization.
2. Partner dan proyek: BusinessPartner, Project, ProjectSegment, ProjectMember.
3. Kontrak dan RAB: CustomerPurchaseOrder, PurchaseOrderItem, ProjectBudgetLine.
4. Lapangan: DailyReport, DailyReportItem, MaterialUsage, Attendance.
5. Keuangan: FundRequest/Item, Disbursement, ExpenseReport/Item, Invoice/Item, Payment, CashTransaction.
6. Kontrol dokumen: Approval, Attachment.
7. Import: ImportBatch, ImportRow.

Semua nilai uang menggunakan Decimal 18,2 dan kuantitas menggunakan empat desimal. Transaksi penting memakai `PROTECT`; detail dokumen memakai `CASCADE` hanya saat header masih dapat dihapus. Constraint dan index berada di migration `erp/0001_initial.py`.

## Anti-bentrok dan integritas

- Nomor dokumen dibuat server-side di `transaction.atomic()` dan `select_for_update()`.
- Header dan detail disimpan dalam satu transaksi.
- Nomor dokumen memiliki unique constraint.
- Relasi project/segment/PO/budget line divalidasi sebelum save.
- Dokumen setelah submit tidak boleh diperlakukan sebagai draft; revisi memakai status/version baru.
- Pencairan dan pembayaran mengunci dokumen sumber sebelum menghitung saldo.
- Cash flow dibentuk dari dokumen sumber dan unik per referensi, bukan input manual ganda.
- Import memakai SHA-256 file dan fingerprint baris; run kedua tidak membuat staging duplikat.

## Menjalankan lokal

```sh
source .venv_django/bin/activate
DB_ENGINE=sqlite python manage.py migrate
DB_ENGINE=sqlite python manage.py seed_erp
DB_ENGINE=sqlite python manage.py runserver 127.0.0.1:8000
```

Produksi MySQL memakai `DB_ENGINE=mysql` serta environment `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, dan `DB_PORT`.

## Import Excel

```sh
DB_ENGINE=sqlite python manage.py import_erp_excel \
  --directory "/Users/mac/Downloads/Excel SSM"
```

Importer hanya mengisi staging. Sheet batal/cancel/revisi dan formula rusak ditandai untuk resolusi manual sebelum posting ke transaksi utama. Ini mencegah histori invoice dan angka rusak masuk sebagai transaksi sah.

## Pengujian

```sh
DB_ENGINE=sqlite python manage.py test portal erp
DB_ENGINE=sqlite python manage.py check
DB_ENGINE=sqlite python manage.py makemigrations --check --dry-run
```

## Role

- SUPERADMIN: seluruh perusahaan/proyek dan approval.
- ADMIN: perusahaan sendiri, master data, dokumen keuangan, approval.
- MANDOR: proyek/segmen yang ditugaskan, pengajuan dan laporan lapangan.
- LAPANGAN: proyek/segmen yang ditugaskan dan input operasional.
