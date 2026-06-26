from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', lambda req: redirect('invoice_list'), name='sales_home'),
    path('export/invoice/', views.export_invoice, name='export_invoice'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/add/', views.invoice_add, name='invoice_add'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('invoices/delete/<int:pk>/', views.invoice_delete, name='invoice_delete'),
    path('invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/public/<str:token>/pdf/', views.invoice_public_pdf, name='invoice_public_pdf'),
    path('invoices/<int:pk>/whatsapp/', views.invoice_whatsapp, name='invoice_whatsapp'),
    path('invoices/<int:pk>/send-email/', views.invoice_send_email, name='invoice_send_email'),
    path('proforma/', views.invoice_list, name='proforma_list'),
    path('proforma/add/', views.invoice_add, name='proforma_add'),
    path('export/', views.invoice_list, name='export_list'),
    path('export/add/', views.invoice_add, name='export_add'),
]




