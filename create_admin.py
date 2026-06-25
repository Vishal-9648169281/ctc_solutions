"""Run once after deploy: python create_admin.py"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctc_solution.settings')
django.setup()
from django.contrib.auth.models import User
from masters.models import UserProfile
if not User.objects.filter(username='admin').exists():
    u = User.objects.create_superuser('admin', 'admin@ctcsolution.in', 'ctc@2024')
    UserProfile.objects.get_or_create(user=u, defaults={'role': 'admin'})
    print("Admin created: admin / ctc@2024")
else:
    print("Admin already exists")
