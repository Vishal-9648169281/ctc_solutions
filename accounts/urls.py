from django.urls import path
from . import views

urlpatterns = [
    path('', views.accounts_home, name='accounts_home'),
    path('customer-ledger/', views.customer_ledger, name='customer_ledger'),
    path('vendor-ledger/', views.vendor_ledger, name='vendor_ledger'),
]
