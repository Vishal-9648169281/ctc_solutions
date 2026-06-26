from django.urls import path
from . import views

urlpatterns = [
    path('receive/', views.receive_list, name='receive_list'),
    path('receive/add/', views.receive_add, name='receive_add'),
    path('receipt/', views.receipt_list, name='receipt_list'),
    path('receipt/add/', views.receipt_add, name='receipt_add'),
]
