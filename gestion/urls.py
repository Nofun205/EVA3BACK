from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

# Router de Django REST Framework (DRF)
router = DefaultRouter()
router.register(r'herramientas', api_views.HerramientaViewSet, basename='api-herramienta')
router.register(r'categorias', api_views.CategoriaHerramientaViewSet, basename='api-categoria')
router.register(r'contratistas', api_views.ContratistaViewSet, basename='api-contratista')
router.register(r'obras', api_views.ObraViewSet, basename='api-obra')
router.register(r'alquileres', api_views.AlquilerPrestamoViewSet, basename='api-alquiler')
router.register(r'mantenimientos', api_views.MantenimientoViewSet, basename='api-mantenimiento')
router.register(r'alertas', api_views.AlertaMorosidadViewSet, basename='api-alerta')

urlpatterns = [
    # Autenticación y Dashboard
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Herramientas / Activos
    path('herramientas/', views.herramientas_list, name='herramientas_list'),
    path('herramientas/nueva/', views.herramienta_create, name='herramienta_create'),
    path('herramientas/<int:pk>/', views.herramienta_detail, name='herramienta_detail'),
    path('herramientas/<int:pk>/editar/', views.herramienta_update, name='herramienta_update'),
    path('herramientas/<int:pk>/cambiar-estado/', views.herramienta_cambiar_estado, name='herramienta_cambiar_estado'),

    # Contratistas y Obras
    path('contratistas/', views.contratistas_list, name='contratistas_list'),
    path('contratistas/nuevo/', views.contratista_create, name='contratista_create'),
    path('contratistas/<int:pk>/', views.contratista_detail, name='contratista_detail'),
    path('contratistas/<int:pk>/editar/', views.contratista_update, name='contratista_update'),
    path('contratistas/<int:pk>/toggle-bloqueo/', views.contratista_toggle_bloqueo, name='contratista_toggle_bloqueo'),
    path('obras/', views.obras_list, name='obras_list'),
    path('obras/nueva/', views.obra_create, name='obra_create'),

    # Alquileres, Entrega y Devolución con Firma Digital
    path('alquileres/', views.alquileres_list, name='alquileres_list'),
    path('alquileres/nuevo/', views.alquiler_create, name='alquiler_create'),
    path('alquileres/<int:pk>/', views.alquiler_detail, name='alquiler_detail'),
    path('alquileres/<int:pk>/entrega/', views.alquiler_entrega, name='alquiler_entrega'),
    path('alquileres/<int:pk>/devolucion/', views.alquiler_devolucion, name='alquiler_devolucion'),

    # Mantenimientos Preventivos y Correctivos
    path('mantenimientos/', views.mantenimientos_list, name='mantenimientos_list'),
    path('mantenimientos/programar/', views.mantenimiento_create, name='mantenimiento_create'),
    path('mantenimientos/<int:pk>/completar/', views.mantenimiento_completar, name='mantenimiento_completar'),

    # Alertas de Morosidad y Verificación Global
    path('alertas/', views.alertas_list, name='alertas_list'),
    path('alertas/<int:pk>/resolver/', views.alerta_resolver, name='alerta_resolver'),
    path('verificar-morosidad/', views.ejecutar_verificacion_morosidad_view, name='verificar_morosidad_global'),

    # Endpoints de API REST (DRF)
    path('api/', include(router.urls)),
]
