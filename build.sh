#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py shell -c "
from django.contrib.auth.models import User
from masters.models import UserProfile
if not User.objects.filter(username='admin').exists():
    u = User.objects.create_superuser('admin', 'admin@ctcsolution.in', '1234')
    UserProfile.objects.get_or_create(user=u, defaults={'role': 'admin'})
    print('Admin created')
else:
    u = User.objects.get(username='admin')
    u.set_password('1234')
    u.save()
    print('Admin password updated')
"
python manage.py shell -c "
from masters.models import Customer, Vendor, Product
if Customer.objects.count() == 0:
    import subprocess, sys
    result = subprocess.run([sys.executable, 'manage.py', 'loaddata', 'fixtures/initial_data.json'], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    print('Customers loaded:', Customer.objects.count())
    print('Vendors loaded:', Vendor.objects.count())
    print('Products loaded:', Product.objects.count())
else:
    print('Data already exists, skipping fixture load')
    print('Customers:', Customer.objects.count())
"