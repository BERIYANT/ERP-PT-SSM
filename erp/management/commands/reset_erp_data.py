from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Mengosongkan seluruh data ERP tanpa menghapus akun login portal."

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Konfirmasi penghapusan seluruh data ERP.")

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["yes"]:
            raise CommandError("Tambahkan --yes untuk mengonfirmasi penghapusan data ERP.")
        tables = [model._meta.db_table for model in apps.get_app_config("erp").get_models()]
        with connection.cursor() as cursor:
            if connection.vendor == "mysql":
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            try:
                for table in reversed(tables):
                    cursor.execute(f"DELETE FROM {connection.ops.quote_name(table)}")
                if connection.vendor == "sqlite" and tables:
                    placeholders = ",".join(["%s"] * len(tables))
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})", tables)
            finally:
                if connection.vendor == "mysql":
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        self.stdout.write(self.style.SUCCESS(f"Data ERP dikosongkan dari {len(tables)} tabel; akun portal dipertahankan."))