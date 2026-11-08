"""
URL configuration for buildcorp project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Panel Administrativo Personalizado de Django
    path('admin/', admin.site.urls),

    # Autenticación para API Navegable de DRF
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Aplicación Principal BuildCorp (Web + API REST)
    path('', include('gestion.urls')),
]

# Servir archivos estáticos y media durante desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
