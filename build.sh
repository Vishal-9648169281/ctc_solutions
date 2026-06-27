#!/usr/bin/env bash
set -o errexit

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Running migrations..."
python manage.py migrate --no-input

echo "==> Ensuring admin user exists..."
python manage.py shell -c "
from django.contrib.auth.models import User
from masters.models import UserProfile
if not User.objects.filter(username='admin').exists():
    u = User.objects.create_superuser('admin', 'admin@ctcsolution.in', '1234')
    UserProfile.objects.get_or_create(user=u, defaults={'role': 'admin'})
    print('Admin created: admin / 1234')
else:
    print('Admin already exists — skipping.')
"

echo "==> Loading master data (only if tables are empty)..."
python manage.py shell -c "
from masters.models import Customer
if Customer.objects.count() == 0:
    import subprocess, sys
    result = subprocess.run([sys.executable, 'manage.py', 'loaddata', 'fixtures/initial_data.json'], capture_output=True, text=True)
    print(result.stdout or 'Fixture loaded.')
    if result.returncode != 0:
        print('Warning: fixture load failed:', result.stderr[:200])
else:
    print('Data already exists (' + str(Customer.objects.count()) + ' customers) — skipping fixture load.')
"

echo "==> Build complete. App is ready."
