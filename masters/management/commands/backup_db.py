"""
Usage:
  python manage.py backup_db           → saves backup to backups/backup_YYYY-MM-DD.json
  python manage.py backup_db --restore backups/backup_2026-06-27.json
"""
import os, json, datetime
from django.core.management.base import BaseCommand
from django.core import serializers
from django.apps import apps


class Command(BaseCommand):
    help = 'Backup or restore all app data as JSON'

    def add_arguments(self, parser):
        parser.add_argument('--restore', type=str, help='Path to backup file to restore from')
        parser.add_argument('--out', type=str, help='Output file path (default: backups/backup_DATE.json)')

    def handle(self, *args, **options):
        if options.get('restore'):
            self._restore(options['restore'])
        else:
            self._backup(options.get('out'))

    def _backup(self, out_path=None):
        os.makedirs('backups', exist_ok=True)
        date_str = datetime.date.today().isoformat()
        out_path = out_path or f'backups/backup_{date_str}.json'

        # Collect all models from our apps (not Django built-in admin logs etc.)
        our_apps = ['masters', 'sales', 'purchase', 'credit_note', 'service_call', 'payments', 'accounts', 'projects']
        objects = []
        total = 0
        for app_label in our_apps:
            try:
                app_config = apps.get_app_config(app_label)
                for model in app_config.get_models():
                    qs = model.objects.all()
                    count = qs.count()
                    if count:
                        objects.extend(list(qs))
                        total += count
                        self.stdout.write(f'  {app_label}.{model.__name__}: {count} records')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Skipped {app_label}: {e}'))

        # Also backup auth users
        from django.contrib.auth.models import User
        users = list(User.objects.all())
        objects.extend(users)
        total += len(users)

        data = serializers.serialize('json', objects, indent=2)
        with open(out_path, 'w') as f:
            f.write(data)

        size_kb = os.path.getsize(out_path) // 1024
        self.stdout.write(self.style.SUCCESS(
            f'\nBackup complete: {out_path} ({total} records, {size_kb} KB)'
        ))

    def _restore(self, file_path):
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        self.stdout.write(f'Restoring from {file_path}...')
        from django.core.management import call_command
        call_command('loaddata', file_path, verbosity=1)
        self.stdout.write(self.style.SUCCESS('Restore complete.'))
