from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('projects/', include('projects.urls')),
    path('', include('masters.urls')),
    path('purchase/', include('purchase.urls')),
    path('sales/', include('sales.urls')),
    path('credit-note/', include('credit_note.urls')),
    path('service/', include('service_call.urls')),
    path('payments/', include('payments.urls')),
    path('reports/', include('reports.urls')),
    path('accounts/', include('accounts.urls')),
    path('utilities/', include('accounts.urls')),
    path('projects/', include('projects.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
