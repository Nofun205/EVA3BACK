from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from django.utils import timezone
from django.core.files.base import ContentFile
from decimal import Decimal
import base64
import uuid

from .models import (
    CategoriaHerramienta,
    Herramienta,
    Contratista,
    Obra,
    AlquilerPrestamo,
    DetalleAlquiler,
    RegistroEntrega,
    RegistroDevolucion,
    Mantenimiento,
    AlertaMorosidad
)
from .serializers import (
    CategoriaHerramientaSerializer,
    HerramientaSerializer,
    ContratistaSerializer,
    ObraSerializer,
    AlquilerPrestamoSerializer,
    DetalleAlquilerSerializer,
    RegistroEntregaSerializer,
    RegistroDevolucionSerializer,
    MantenimientoSerializer,
    AlertaMorosidadSerializer
)


def guardar_firma_base64(base64_str, prefijo="firma"):
    """Convierte una cadena data:image/png;base64,... en un ContentFile para almacenar."""
    if not base64_str:
        return None
    if "base64," in base64_str:
        header, base64_str = base64_str.split("base64,")
    decoded_file = base64.b64decode(base64_str)
    file_name = f"{prefijo}_{uuid.uuid4().hex[:8]}.png"
    return ContentFile(decoded_file, name=file_name)


class CategoriaHerramientaViewSet(viewsets.ModelViewSet):
    queryset = CategoriaHerramienta.objects.all()
    serializer_class = CategoriaHerramientaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class HerramientaViewSet(viewsets.ModelViewSet):
    queryset = Herramienta.objects.select_related('categoria').prefetch_related('historial_estados').all()
    serializer_class = HerramientaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['estado', 'categoria', 'marca']
    search_fields = ['codigo', 'nombre', 'marca', 'modelo', 'numero_serie']

    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """Retorna únicamente herramientas en estado DISPONIBLE."""
        herramientas = self.queryset.filter(estado='DISPONIBLE')
        serializer = self.get_serializer(herramientas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def requieren_mantenimiento(self, request):
        """Retorna herramientas que superaron el umbral de horas o fecha límite."""
        herramientas = [h for h in self.queryset.all() if h.requiere_mantenimiento_preventivo]
        serializer = self.get_serializer(herramientas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """Cambia el estado operativo de una herramienta dejando trazabilidad de auditoría."""
        herramienta = self.get_object()
        nuevo_estado = request.data.get('estado')
        motivo = request.data.get('motivo', 'Cambio vía API REST')

        valid_states = [s[0] for s in Herramienta.ESTADO_CHOICES]
        if nuevo_estado not in valid_states:
            return Response(
                {'error': f'Estado inválido. Opciones válidas: {valid_states}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario = request.user if request.user.is_authenticated else None
        herramienta.cambiar_estado(nuevo_estado, usuario=usuario, motivo=motivo)

        return Response({
            'mensaje': f'Estado cambiado exitosamente a {herramienta.get_estado_display()}',
            'herramienta': self.get_serializer(herramienta).data
        })


class ContratistaViewSet(viewsets.ModelViewSet):
    queryset = Contratista.objects.prefetch_related('obras').all()
    serializer_class = ContratistaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ['rut_empresa', 'razon_social', 'contacto_nombre', 'contacto_email']

    @action(detail=True, methods=['post'])
    def bloquear(self, request, pk=None):
        """Bloquea manualmente a un contratista para impedir nuevos arriendos."""
        contratista = self.get_object()
        motivo = request.data.get('motivo', 'Bloqueo manual administrativo')
        contratista.bloquear(motivo)
        return Response({
            'mensaje': f'Contratista {contratista.razon_social} bloqueado.',
            'contratista': self.get_serializer(contratista).data
        })

    @action(detail=True, methods=['post'])
    def desbloquear(self, request, pk=None):
        """Desbloquea a un contratista tras regularización."""
        contratista = self.get_object()
        contratista.desbloquear()
        return Response({
            'mensaje': f'Contratista {contratista.razon_social} desbloqueado exitosamente.',
            'contratista': self.get_serializer(contratista).data
        })


class ObraViewSet(viewsets.ModelViewSet):
    queryset = Obra.objects.select_related('contratista').all()
    serializer_class = ObraSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ['codigo', 'nombre', 'encargado_obra']


class AlquilerPrestamoViewSet(viewsets.ModelViewSet):
    queryset = AlquilerPrestamo.objects.select_related(
        'contratista', 'obra', 'usuario_creador', 'entrega', 'devolucion'
    ).prefetch_related('detalles__herramienta').all()
    serializer_class = AlquilerPrestamoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['post'])
    def verificar_morosidades(self, request):
        """Gatilla la verificación global de préstamos vencidos y bloqueo automático de contratistas."""
        hoy = timezone.now().date()
        alquileres_activos = AlquilerPrestamo.objects.filter(estado__in=['ACTIVO', 'SOLICITADO'])
        bloqueados_count = 0
        alquileres_afectados = []

        for alq in alquileres_activos:
            if alq.fecha_fin_estimada < hoy:
                if alq.verificar_morosidad():
                    bloqueados_count += 1
                    alquileres_afectados.append({
                        'codigo': alq.codigo,
                        'contratista': alq.contratista.razon_social,
                        'dias_retraso': alq.dias_retraso,
                        'multa': alq.recargo_mora
                    })

        return Response({
            'mensaje': 'Verificación de morosidad ejecutada.',
            'total_contratistas_bloqueados': bloqueados_count,
            'alquileres_afectados': alquileres_afectados
        })

    @action(detail=True, methods=['post'])
    def registrar_entrega(self, request, pk=None):
        """Registra la entrega física de herramientas con firma digital del responsable."""
        alquiler = self.get_object()
        if hasattr(alquiler, 'entrega'):
            return Response({'error': 'La entrega de este alquiler ya fue registrada previamente.'}, status=status.HTTP_400_BAD_REQUEST)

        responsable_nombre = request.data.get('responsable_obra_nombre')
        responsable_rut = request.data.get('responsable_obra_rut')
        firma_base64 = request.data.get('firma_digital_base64')
        observaciones = request.data.get('observaciones_entrega', '')

        if not responsable_nombre or not responsable_rut:
            return Response({'error': 'Se requiere el nombre y RUT del responsable que recibe.'}, status=status.HTTP_400_BAD_REQUEST)

        firma_archivo = guardar_firma_base64(firma_base64, prefijo=f"entrega_{alquiler.codigo}")

        registro = RegistroEntrega.objects.create(
            alquiler=alquiler,
            despachador_bodega=request.user if request.user.is_authenticated else None,
            responsable_obra_nombre=responsable_nombre,
            responsable_obra_rut=responsable_rut,
            firma_digital=firma_archivo,
            observaciones_entrega=observaciones
        )

        # Actualizar estado de alquiler a ACTIVO
        alquiler.estado = 'ACTIVO'
        alquiler.save(update_fields=['estado'])

        # Cambiar estado de herramientas a EN_USO
        for det in alquiler.detalles.all():
            det.herramienta.cambiar_estado(
                'EN_USO',
                usuario=request.user if request.user.is_authenticated else None,
                motivo=f"Entregada en Alquiler {alquiler.codigo} a la obra {alquiler.obra.nombre}"
            )

        return Response({
            'mensaje': 'Entrega registrada y herramientas marcadas EN USO con firma digital.',
            'entrega': RegistroEntregaSerializer(registro).data
        })

    @action(detail=True, methods=['post'])
    def registrar_devolucion(self, request, pk=None):
        """Registra la devolución de herramientas con firma digital, horómetro y cálculo de morosidad."""
        alquiler = self.get_object()
        if hasattr(alquiler, 'devolucion'):
            return Response({'error': 'La devolución ya fue registrada previamente.'}, status=status.HTTP_400_BAD_REQUEST)

        responsable_nombre = request.data.get('responsable_obra_nombre')
        responsable_rut = request.data.get('responsable_obra_rut')
        firma_base64 = request.data.get('firma_digital_base64')
        estado_general = request.data.get('estado_general_equipos', 'Operativo')
        observaciones = request.data.get('observaciones_devolucion', '')

        # Lista opcional de horómetros finales por herramienta: [{"herramienta_id": 1, "horas_finales": 120.5, "dano": 0}]
        herramientas_data = request.data.get('herramientas_data', [])

        firma_archivo = guardar_firma_base64(firma_base64, prefijo=f"devolucion_{alquiler.codigo}")

        registro = RegistroDevolucion.objects.create(
            alquiler=alquiler,
            receptor_bodega=request.user if request.user.is_authenticated else None,
            responsable_obra_nombre=responsable_nombre,
            responsable_obra_rut=responsable_rut,
            firma_digital=firma_archivo,
            estado_general_equipos=estado_general,
            observaciones_devolucion=observaciones
        )

        hoy = timezone.now().date()
        alquiler.fecha_devolucion_real = hoy

        # Calcular días de retraso si devolvió después de la fecha pactada
        total_danios = Decimal('0.0')
        if hoy > alquiler.fecha_fin_estimada:
            alquiler.dias_retraso = (hoy - alquiler.fecha_fin_estimada).days
            total_diario = sum(d.tarifa_diaria_pactada for d in alquiler.detalles.all())
            alquiler.recargo_mora = total_diario * Decimal(alquiler.dias_retraso) * Decimal('1.5')
        else:
            alquiler.dias_retraso = 0
            alquiler.recargo_mora = Decimal('0.0')

        # Procesar herramientas devueltas
        for det in alquiler.detalles.all():
            tool = det.herramienta
            # Buscar si se enviaron horas finales
            for h_info in herramientas_data:
                if h_info.get('herramienta_id') == tool.id:
                    horas_f = Decimal(str(h_info.get('horas_finales', tool.horas_uso_acumuladas)))
                    dano_costo = Decimal(str(h_info.get('costo_reparacion_dano', '0.0')))
                    det.horas_finales = horas_f
                    det.costo_reparacion_dano = dano_costo
                    det.estado_herramienta_devolucion = h_info.get('estado_herramienta', 'Buena')
                    det.save()
                    total_danios += dano_costo

                    # Actualizar horas en la herramienta
                    if horas_f > tool.horas_uso_acumuladas:
                        tool.horas_uso_acumuladas = horas_f

            # Evaluar si la herramienta pasa a MANTENIMIENTO o DISPONIBLE
            if tool.requiere_mantenimiento_preventivo:
                nuevo_estado = 'MANTENIMIENTO'
                motivo = f"Devuelta en Alquiler {alquiler.codigo}. Superó umbral de {tool.umbral_horas_mantenimiento} horas de uso."
            else:
                nuevo_estado = 'DISPONIBLE'
                motivo = f"Devuelta en Alquiler {alquiler.codigo} en buen estado operativo."

            tool.cambiar_estado(
                nuevo_estado,
                usuario=request.user if request.user.is_authenticated else None,
                motivo=motivo
            )

        # Costo final total
        alquiler.costo_final = alquiler.costo_estimado + alquiler.recargo_mora + total_danios
        alquiler.estado = 'DEVUELTO'
        alquiler.save()

        # Si el contratista estaba bloqueado por este alquiler, resolver alerta
        alertas = AlertaMorosidad.objects.filter(alquiler=alquiler, resuelta=False)
        for a in alertas:
            a.resolver(usuario=request.user, motivo="Herramientas devueltas satisfactoriamente.")

        return Response({
            'mensaje': 'Devolución procesada con éxito y firma digital almacenada.',
            'alquiler': AlquilerPrestamoSerializer(alquiler).data,
            'devolucion': RegistroDevolucionSerializer(registro).data
        })


class MantenimientoViewSet(viewsets.ModelViewSet):
    queryset = Mantenimiento.objects.select_related('herramienta').all()
    serializer_class = MantenimientoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['tipo', 'estado', 'fecha_programada']
    search_fields = ['herramienta__codigo', 'herramienta__nombre', 'tecnico_responsable']

    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        """Finaliza una mantención, registra costo y devuelve la herramienta a estado DISPONIBLE."""
        mantenimiento = self.get_object()
        costo = Decimal(str(request.data.get('costo', '0.0')))
        repuestos = request.data.get('repuestos_utilizados', 'Mantenimiento estándar')

        mantenimiento.completar_mantenimiento(costo_final=costo, repuestos=repuestos)

        return Response({
            'mensaje': f'Mantenimiento para herramienta {mantenimiento.herramienta.codigo} completado. Herramienta disponible.',
            'mantenimiento': self.get_serializer(mantenimiento).data
        })


class AlertaMorosidadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AlertaMorosidad.objects.select_related('alquiler', 'contratista').all()
    serializer_class = AlertaMorosidadSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        """Resuelve manualmente una alerta de morosidad y desbloquea al contratista."""
        alerta = self.get_object()
        motivo = request.data.get('motivo', 'Regularización confirmada por administración')
        alerta.resolver(usuario=request.user, motivo=motivo)
        return Response({
            'mensaje': f'Alerta resuelta. El contratista {alerta.contratista.razon_social} ha sido evaluado para desbloqueo.',
            'alerta': self.get_serializer(alerta).data
        })

