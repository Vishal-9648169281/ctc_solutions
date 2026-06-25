#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

echo "==> Creating admin user..."
python manage.py shell -c "
from django.contrib.auth.models import User
from masters.models import UserProfile
if not User.objects.filter(username='admin').exists():
    u = User.objects.create_superuser('admin', 'admin@ctcsolution.in', '1234')
    UserProfile.objects.get_or_create(user=u, defaults={'role': 'admin'})
    print('Admin created: admin / 1234')
else:
    u = User.objects.get(username='admin')
    u.set_password('1234')
    u.save()
    print('Admin password updated to: 1234')
"

echo "==> Loading master data..."
python manage.py loaddata fixtures/initial_data.json
echo "==> Data load complete"

python manage.py shell -c "
from masters.models import Customer, Vendor, Product
print('Customers:', Customer.objects.count())
print('Vendors:', Vendor.objects.count())
print('Products:', Product.objects.count())
"