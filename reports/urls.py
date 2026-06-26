from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_home, name='reports_home'),
    path('sales/', views.sales_report, name='sales_report'),
    path('purchase/', views.purchase_report, name='purchase_report'),
    path('stock/', views.stock_report, name='stock_report'),
    path('payments/', views.payment_report, name='payment_report'),
    path('service/', views.service_report, name='service_report'),
    path('credit-note-statement/', views.credit_note_statement, name='credit_note_statement'),
    path('excel/<str:report_type>/', views.export_excel, name='export_excel'),
]
