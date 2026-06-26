from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/edit/<int:pk>/', views.user_edit, name='user_edit'),
    path('users/delete/<int:pk>/', views.user_delete, name='user_delete'),
    path('users/block/<int:pk>/', views.user_block, name='user_block'),
    path('users/unblock/<int:pk>/', views.user_unblock, name='user_unblock'),

    # Category
    path('masters/categories/', views.category_list, name='category_list'),
    path('masters/categories/add/', views.category_add, name='category_add'),
    path('masters/categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('masters/categories/delete/<int:pk>/', views.category_delete, name='category_delete'),

    # Unit
    path('masters/units/', views.unit_list, name='unit_list'),
    path('masters/units/add/', views.unit_add, name='unit_add'),
    path('masters/units/edit/<int:pk>/', views.unit_edit, name='unit_edit'),
    path('masters/units/delete/<int:pk>/', views.unit_delete, name='unit_delete'),

    # Customer
    path('masters/customers/', views.customer_list, name='customer_list'),
    path('masters/customers/add/', views.customer_add, name='customer_add'),
    path('masters/customers/edit/<int:pk>/', views.customer_edit, name='customer_edit'),
    path('masters/customers/delete/<int:pk>/', views.customer_delete, name='customer_delete'),

    # Vendor
    path('masters/vendors/', views.vendor_list, name='vendor_list'),
    path('masters/vendors/add/', views.vendor_add, name='vendor_add'),
    path('masters/vendors/edit/<int:pk>/', views.vendor_edit, name='vendor_edit'),
    path('masters/vendors/delete/<int:pk>/', views.vendor_delete, name='vendor_delete'),

    # Product
    path('masters/products/', views.product_list, name='product_list'),
    path('masters/products/add/', views.product_add, name='product_add'),
    path('masters/products/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('masters/products/delete/<int:pk>/', views.product_delete, name='product_delete'),

    # Company Master
    path('masters/company/', views.company_list, name='company_list'),
    path('masters/company/save/', views.company_save, name='company_save'),
    path('masters/company/delete/<int:pk>/', views.company_delete, name='company_delete'),

    # Salesmen Master
    path('masters/salesman/', views.salesman_list, name='salesman_list'),
    path('masters/salesman/save/', views.salesman_save, name='salesman_save'),
    path('masters/salesman/delete/<int:pk>/', views.salesman_delete, name='salesman_delete'),

    # Area Master
    path('masters/area/', views.area_list, name='area_list'),
    path('masters/area/save/', views.area_save, name='area_save'),
    path('masters/area/delete/<int:pk>/', views.area_delete, name='area_delete'),

    # GST State Master
    path('masters/gststate/', views.gststate_list, name='gststate_list'),
    path('masters/gststate/save/', views.gststate_save, name='gststate_save'),
    path('masters/gststate/delete/<int:pk>/', views.gststate_delete, name='gststate_delete'),

    # GST Master
    path('masters/gstmaster/', views.gstmaster_list, name='gstmaster_list'),
    path('masters/gstmaster/save/', views.gstmaster_save, name='gstmaster_save'),
    path('masters/gstmaster/delete/<int:pk>/', views.gstmaster_delete, name='gstmaster_delete'),

    # General Ledger Master
    path('masters/ledger/', views.ledger_list, name='ledger_list'),
    path('masters/ledger/save/', views.ledger_save, name='ledger_save'),
    path('masters/ledger/delete/<int:pk>/', views.ledger_delete, name='ledger_delete'),

    # Rate Modification
    path('masters/rate-modification/', views.rate_modification, name='rate_modification'),

    # Quick-Add AJAX (used inline from invoice/bill forms)
    path('masters/quick-add/customer/', views.quick_add_customer, name='quick_add_customer'),
    path('masters/quick-add/vendor/', views.quick_add_vendor, name='quick_add_vendor'),
    path('masters/quick-add/product/', views.quick_add_product, name='quick_add_product'),

    # Party Master
    path('masters/party/', views.party_list, name='party_list'),
    path('masters/party/add/', views.party_add, name='party_add'),
    path('masters/party/edit/<int:pk>/', views.party_edit, name='party_edit'),
    path('masters/party/delete/<int:pk>/', views.party_delete, name='party_delete'),
]
