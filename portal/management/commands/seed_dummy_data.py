from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from portal.models import (
    Absen,
    AbsenDetail,
    Customer,
    Invoice,
    Kasbon,
    LogAktivitas,
    Material,
    OverheadKantor,
    PettyCash,
    PettyCashBudget,
    Project,
    ProjectAssignment,
    ProjectJasaSlip,
    ProjectOverheadKasbonMandor,
    ProjectOverheadOpname,
    ProjectRAB,
    ProjectTimeline,
    Setting,
    SupervisiLaporan,
    SupervisiLaporanItem,
    User,
)


class Command(BaseCommand):
    help = "Menambahkan data dummy SSM Portal secara idempoten."

    @transaction.atomic
    def handle(self, *args, **options):
        today = date.today()
        admin = self._user("admin", "Super Admin", "admin", "Administrator")
        mandor = self._user("mandor.demo", "Budi Santoso", "mandor", "Mandor Lapangan")
        supervisi = self._user("supervisi.demo", "Siti Rahma", "supervisi", "Site Supervisor")
        staff = self._user("staff.demo", "Andi Pratama", "user", "Staf Keuangan")

        customers = [
            self._customer("PT Nusantara Konstruksi", "procurement@nusantara.co.id", "081234567801", "Jakarta Selatan"),
            self._customer("CV Bima Properti", "admin@bimaproperti.co.id", "081234567802", "Kota Bima"),
            self._customer("PT Samudra Infrastruktur", "info@samudrainfra.co.id", "081234567803", "Surabaya"),
        ]

        projects = [
            self._project(customers[0], admin, "Renovasi Gedung Kantor Pusat", "po", "PO-SSM-2026-001", today - timedelta(days=75), Decimal("850000000")),
            self._project(customers[1], admin, "Pembangunan Perumahan Tahap 1", "po", "PO-SSM-2026-002", today - timedelta(days=45), Decimal("1250000000")),
            self._project(customers[2], admin, "Perbaikan Drainase Kawasan", "non_po", None, today - timedelta(days=20), Decimal("425000000")),
        ]

        for project in projects:
            ProjectAssignment.objects.get_or_create(user=mandor, project=project)
            ProjectAssignment.objects.get_or_create(user=supervisi, project=project)

        categories = [
            ("jasa", "Upah tenaga kerja", "OH", Decimal("100"), Decimal("1250000")),
            ("material", "Material utama proyek", "LS", Decimal("1"), Decimal("350000000")),
            ("overhead", "Operasional dan pengawasan", "LS", Decimal("1"), Decimal("75000000")),
            ("patty_cash", "Dana petty cash proyek", "LS", Decimal("1"), Decimal("25000000")),
        ]
        for project in projects:
            for kategori, deskripsi, satuan, volume, harga in categories:
                ProjectRAB.objects.update_or_create(
                    project=project,
                    kategori=kategori,
                    deskripsi=deskripsi,
                    defaults={"satuan": satuan, "volume": volume, "harga_satuan": harga, "total": volume * harga},
                )
            for number, task, offset, status in [
                (1, "Persiapan dan mobilisasi", -30, "completed"),
                (2, "Pekerjaan struktur", 0, "in_progress"),
                (3, "Finishing dan serah terima", 45, "planned"),
            ]:
                ProjectTimeline.objects.update_or_create(
                    project=project,
                    number=number,
                    defaults={"task_name": task, "tanggal": today + timedelta(days=offset), "status": status},
                )

        for index, project in enumerate(projects, start=1):
            Invoice.objects.update_or_create(
                po_number=project.po_number or f"NON-PO-{index:03d}",
                description=f"Termin pertama {project.project_name}",
                defaults={
                    "customer_name": project.customer.name,
                    "po_date": project.po_date,
                    "amount": project.amount * Decimal("0.30"),
                    "paid_date": today - timedelta(days=5) if index == 1 else None,
                    "project": project,
                    "created_by": staff,
                },
            )
            Material.objects.update_or_create(
                project=project,
                name=f"Semen dan material {project.project_name}",
                defaults={"price": Decimal("42500000") + index * Decimal("5000000"), "source": "lapangan", "used": True, "created_by": admin},
            )
            Material.objects.update_or_create(
                project=None,
                name=f"Stok Besi Beton Paket {index}",
                defaults={"price": Decimal("18000000") + index * Decimal("2000000"), "source": "gudang", "used": False, "created_by": admin},
            )
            PettyCash.objects.update_or_create(
                project=project,
                tanggal=today - timedelta(days=index),
                kategori="Operasional Lapangan",
                defaults={"deskripsi": "Konsumsi dan transportasi tim", "jumlah": Decimal("1250000") * index, "keterangan": "Data dummy", "created_by": staff},
            )
            PettyCashBudget.objects.update_or_create(project=project, defaults={"budget": Decimal("25000000"), "updated_by": admin})
            ProjectJasaSlip.objects.update_or_create(
                project=project,
                employee_name=f"Pekerja Lapangan {index}",
                period_month=today.strftime("%Y-%m"),
                defaults={"posisi": "Tukang", "hari_kerja": 24, "jumlah_gaji": Decimal("4800000") + index * Decimal("250000"), "tanggal_bayar": today, "created_by": staff},
            )
            ProjectOverheadOpname.objects.update_or_create(
                project=project,
                item_pekerjaan="Pengawasan dan koordinasi lapangan",
                defaults={"mandor_name": mandor.nama, "jumlah_pekerja": 12 + index, "span": "Mingguan", "volume_progress": Decimal("35") + index * 10, "harga_satuan": Decimal("1500000"), "nilai_opname": (Decimal("35") + index * 10) * Decimal("1500000"), "created_by": admin},
            )
            ProjectOverheadKasbonMandor.objects.update_or_create(
                project=project,
                mandor_name=mandor.nama,
                defaults={"unit_name": f"Unit {index}", "plafon": Decimal("30000000"), "kasbon_belum_dibayar": Decimal("5000000") * index, "pembayaran_terakhir": Decimal("2500000"), "status": "saldo", "created_by": admin},
            )

            absen, _ = Absen.objects.update_or_create(
                project=project,
                tanggal=today - timedelta(days=index),
                defaults={"project_name": project.project_name, "segmen": "Pekerjaan Lapangan", "waktu_lapor": "08:00", "deskripsi": "Aktivitas proyek berjalan normal", "created_by": supervisi},
            )
            AbsenDetail.objects.update_or_create(absen=absen, kategori="Tenaga Kerja", label="Jumlah hadir", defaults={"nilai": str(15 + index), "satuan": "orang"})

            laporan, _ = SupervisiLaporan.objects.update_or_create(
                project=project,
                tanggal=today - timedelta(days=index),
                jenis="laporan",
                defaults={"project_name": project.project_name, "lokasi": project.customer.address, "waktu_lapor": "16:30", "judul": f"Laporan Harian {project.project_name}", "catatan": "Progres sesuai rencana kerja.", "created_by": supervisi},
            )
            SupervisiLaporanItem.objects.update_or_create(laporan=laporan, kategori="Progress", nama_item="Realisasi pekerjaan", defaults={"segmen": "Utama", "nilai": Decimal("45") + index * 5, "satuan": "%"})

        for index, (kategori, deskripsi, jumlah) in enumerate([
            ("Internet", "Tagihan internet kantor", "1750000"),
            ("ATK", "Pembelian alat tulis kantor", "2350000"),
            ("Transportasi", "Operasional kendaraan kantor", "4500000"),
        ]):
            OverheadKantor.objects.update_or_create(
                tanggal=today - timedelta(days=index + 2),
                kategori=kategori,
                deskripsi=deskripsi,
                defaults={"jumlah": Decimal(jumlah), "keterangan": "Data dummy", "created_by": staff},
            )

        for index, status in enumerate(("pending", "approved", "rejected")):
            Kasbon.objects.update_or_create(
                user=mandor,
                project=projects[index],
                keperluan=f"Pembelian kebutuhan lapangan proyek {index + 1}",
                defaults={
                    "tanggal_pengajuan": today - timedelta(days=index + 1),
                    "jumlah": Decimal("3000000") * (index + 1),
                    "status": status,
                    "tanggal_verifikasi": datetime.now() if status != "pending" else None,
                    "verifier": admin if status != "pending" else None,
                    "rejection_reason": "Dokumen pendukung belum lengkap" if status == "rejected" else None,
                },
            )

        for key, value, description in [
            ("company_name", "PT SSM Konstruksi Indonesia", "Nama perusahaan"),
            ("company_address", "Jl. Pembangunan No. 10, Kota Bima", "Alamat perusahaan"),
            ("company_phone", "0374-123456", "Nomor telepon perusahaan"),
        ]:
            Setting.objects.update_or_create(kunci=key, defaults={"nilai": value, "deskripsi": description})

        LogAktivitas.objects.get_or_create(user=admin, username=admin.username, aksi="SEED", modul="System", deskripsi="Data dummy aplikasi ditambahkan", defaults={"ip_address": "127.0.0.1"})

        self.stdout.write(self.style.SUCCESS("Data dummy berhasil ditambahkan/diperbarui."))
        self.stdout.write("Login demo: admin/admin123, mandor.demo/demo123, supervisi.demo/demo123, staff.demo/demo123")

    def _user(self, username, nama, role, jabatan):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"nama": nama, "role": role, "jabatan": jabatan, "email": f"{username}@example.com", "is_active": True},
        )
        if created or not user.check_password("demo123" if username != "admin" else "admin123"):
            user.set_password("demo123" if username != "admin" else "admin123")
            user.save()
        return user

    def _customer(self, name, email, phone, address):
        customer, _ = Customer.objects.update_or_create(name=name, defaults={"email": email, "phone": phone, "address": address})
        return customer

    def _project(self, customer, creator, name, project_type, po_number, po_date, amount):
        project, _ = Project.objects.update_or_create(
            project_name=name,
            defaults={
                "customer": customer,
                "project_type": project_type,
                "po_number": po_number,
                "po_date": po_date,
                "description": "Data demonstrasi SSM Portal",
                "amount": amount,
                "status": "active",
                "created_by": creator,
            },
        )
        return project
