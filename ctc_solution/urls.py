from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
import datetime

def health_check(request):
    """Render uses this URL to verify the app is alive. Returns 200 = healthy."""
    try:
        from django.db import connection
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    status = 200 if db_ok else 503
    return JsonResponse({
        'status': 'ok' if db_ok else 'db_error',
        'time': datetime.datetime.now().isoformat(),
        'db': 'connected' if db_ok else 'failed',
    }, status=status)

urlpatterns = [
    path('health/', health_check, name='health_check'),
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
