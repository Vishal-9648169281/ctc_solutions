from django.urls import path
from . import views

urlpatterns = [
    path('', views.call_list, name='call_list'),
    path('add/', views.call_add, name='call_add'),
    path('edit/<int:pk>/', views.call_edit, name='call_edit'),
    path('detail/<int:pk>/', views.call_detail, name='call_detail'),
    path('delete/<int:pk>/', views.call_delete, name='call_delete'),
]
