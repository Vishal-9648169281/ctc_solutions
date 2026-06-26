from django.urls import path
from . import views

urlpatterns = [
    path('', views.note_list, name='note_list'),
    path('add/', views.note_add, name='note_add'),
    path('<int:pk>/', views.note_detail, name='note_detail'),
    path('delete/<int:pk>/', views.note_delete, name='note_delete'),
    path('approve/<int:pk>/', views.note_approve, name='note_approve'),
]
