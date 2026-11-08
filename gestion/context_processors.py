from .models import AlertaMorosidad, Herramienta, Contratista, AlquilerPrestamo
from django.utils import timezone


def alertas_globales(request):
    """Context processor que provee contadores en tiempo real para la barra de navegación y el dashboard."""
    if not request.user.is_authenticated:
        return {}

    try:
        alertas_mora_count = AlertaMorosidad.objects.filter(resuelta=False).count()
        contratistas_bloqueados_count = Contratista.objects.filter(bloqueado=True).count()
        herramientas_mantenimiento_count = Herramienta.objects.filter(estado='MANTENIMIENTO').count()
        alquileres_activos_count = AlquilerPrestamo.objects.filter(estado='ACTIVO').count()
        alquileres_vencidos_count = AlquilerPrestamo.objects.filter(estado='VENCIDO').count()

        return {
            'GLOBAL_ALERTAS_MORA': alertas_mora_count,
            'GLOBAL_CONTRATISTAS_BLOQUEADOS': contratistas_bloqueados_count,
            'GLOBAL_HERRAMIENTAS_MANT': herramientas_mantenimiento_count,
            'GLOBAL_ALQUILERES_ACTIVOS': alquileres_activos_count,
            'GLOBAL_ALQUILERES_VENCIDOS': alquileres_vencidos_count,
        }
    except Exception:
        # En caso de migraciones pendientes o base no lista
        return {}

