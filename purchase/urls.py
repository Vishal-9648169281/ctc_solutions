from django.urls import path
from . import views

app_name = 'purchase'

urlpatterns = [
    path('bills/', views.bill_list, name='bill_list'),
    path('bills/add/', views.bill_add, name='bill_add'),
    path('bills/<int:pk>/', views.bill_detail, name='bill_detail'),
    path('bills/delete/<int:pk>/', views.bill_delete, name='bill_delete'),
]
