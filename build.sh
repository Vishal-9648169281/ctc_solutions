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
python manage.py loaddata fixtures/initial_data.json && echo "Data loaded" || echo "Data load skipped (already exists)"