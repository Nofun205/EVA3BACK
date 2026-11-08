from rest_framework import serializers
from .models import (
    CategoriaHerramienta,
    Herramienta,
    HistorialEstadoHerramienta,
    Contratista,
    Obra,
    AlquilerPrestamo,
    DetalleAlquiler,
    RegistroEntrega,
    RegistroDevolucion,
    Mantenimiento,
    AlertaMorosidad
)


class CategoriaHerramientaSerializer(serializers.ModelSerializer):
    total_herramientas = serializers.IntegerField(source='herramientas.count', read_only=True)

    class Meta:
        model = CategoriaHerramienta
        fields = ['id', 'nombre', 'descripcion', 'total_herramientas']


class HistorialEstadoHerramientaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = HistorialEstadoHerramienta
        fields = ['id', 'estado_anterior', 'estado_nuevo', 'usuario_nombre', 'motivo', 'fecha_cambio']


class HerramientaSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    requiere_mantenimiento = serializers.BooleanField(source='requiere_mantenimiento_preventivo', read_only=True)
    historial_estados = HistorialEstadoHerramientaSerializer(many=True, read_only=True)

    class Meta:
        model = Herramienta
        fields = [
            'id',
            'codigo',
            'nombre',
            'categoria',
            'categoria_nombre',
            'marca',
            'modelo',
            'numero_serie',
            'estado',
            'estado_display',
            'tarifa_diaria',
            'valor_reposicion',
            'horas_uso_acumuladas',
            'umbral_horas_mantenimiento',
            'fecha_adquisicion',
            'fecha_ultimo_mantenimiento',
            'fecha_proximo_mantenimiento',
            'ubicacion_bodega',
            'imagen',
            'observaciones',
            'requiere_mantenimiento',
            'historial_estados',
            'fecha_creacion',
            'fecha_actualizacion'
        ]


class ObraSerializer(serializers.ModelSerializer):
    contratista_nombre = serializers.CharField(source='contratista.razon_social', read_only=True)

    class Meta:
        model = Obra
        fields = [
            'id',
            'codigo',
            'nombre',
            'direccion',
            'comuna_ciudad',
            'encargado_obra',
            'telefono_encargado',
            'contratista',
            'contratista_nombre',
            'activa'
        ]


class ContratistaSerializer(serializers.ModelSerializer):
    obras = ObraSerializer(many=True, read_only=True)

    class Meta:
        model = Contratista
        fields = [
            'id',
            'rut_empresa',
            'razon_social',
            'nombre_fantasia',
            'contacto_nombre',
            'contacto_telefono',
            'contacto_email',
            'direccion',
            'bloqueado',
            'motivo_bloqueo',
            'fecha_bloqueo',
            'obras',
            'fecha_creacion'
        ]


class DetalleAlquilerSerializer(serializers.ModelSerializer):
    herramienta_codigo = serializers.CharField(source='herramienta.codigo', read_only=True)
    herramienta_nombre = serializers.CharField(source='herramienta.nombre', read_only=True)

    class Meta:
        model = DetalleAlquiler
        fields = [
            'id',
            'herramienta',
            'herramienta_codigo',
            'herramienta_nombre',
            'tarifa_diaria_pactada',
            'horas_iniciales',
            'horas_finales',
            'estado_herramienta_devolucion',
            'costo_reparacion_dano'
        ]


class RegistroEntregaSerializer(serializers.ModelSerializer):
    despachador_nombre = serializers.CharField(source='despachador_bodega.username', read_only=True)

    class Meta:
        model = RegistroEntrega
        fields = [
            'id',
            'alquiler',
            'fecha_hora_entrega',
            'despachador_nombre',
            'responsable_obra_nombre',
            'responsable_obra_rut',
            'firma_digital',
            'observaciones_entrega'
        ]


class RegistroDevolucionSerializer(serializers.ModelSerializer):
    receptor_nombre = serializers.CharField(source='receptor_bodega.username', read_only=True)

    class Meta:
        model = RegistroDevolucion
        fields = [
            'id',
            'alquiler',
            'fecha_hora_devolucion',
            'receptor_nombre',
            'responsable_obra_nombre',
            'responsable_obra_rut',
            'firma_digital',
            'estado_general_equipos',
            'observaciones_devolucion'
        ]


class AlquilerPrestamoSerializer(serializers.ModelSerializer):
    contratista_nombre = serializers.CharField(source='contratista.razon_social', read_only=True)
    obra_nombre = serializers.CharField(source='obra.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    detalles = DetalleAlquilerSerializer(many=True, read_only=True)
    entrega = RegistroEntregaSerializer(read_only=True)
    devolucion = RegistroDevolucionSerializer(read_only=True)

    class Meta:
        model = AlquilerPrestamo
        fields = [
            'id',
            'codigo',
            'contratista',
            'contratista_nombre',
            'obra',
            'obra_nombre',
            'usuario_creador',
            'fecha_inicio',
            'fecha_fin_estimada',
            'fecha_devolucion_real',
            'estado',
            'estado_display',
            'costo_estimado',
            'costo_final',
            'dias_retraso',
            'recargo_mora',
            'observaciones',
            'detalles',
            'entrega',
            'devolucion',
            'fecha_creacion'
        ]

    def validate(self, attrs):
        contratista = attrs.get('contratista')
        if not self.instance and contratista and contratista.bloqueado:
            raise serializers.ValidationError({
                'contratista': f"El contratista {contratista.razon_social} se encuentra BLOQUEADO. Motivo: {contratista.motivo_bloqueo}"
            })
        return attrs


class MantenimientoSerializer(serializers.ModelSerializer):
    herramienta_codigo = serializers.CharField(source='herramienta.codigo', read_only=True)
    herramienta_nombre = serializers.CharField(source='herramienta.nombre', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Mantenimiento
        fields = [
            'id',
            'herramienta',
            'herramienta_codigo',
            'herramienta_nombre',
            'tipo',
            'tipo_display',
            'fecha_programada',
            'fecha_ejecucion',
            'horas_uso_al_programar',
            'horas_limite',
            'tecnico_responsable',
            'costo',
            'estado',
            'estado_display',
            'descripcion_trabajo',
            'repuestos_utilizados',
            'fecha_creacion'
        ]


class AlertaMorosidadSerializer(serializers.ModelSerializer):
    alquiler_codigo = serializers.CharField(source='alquiler.codigo', read_only=True)
    contratista_nombre = serializers.CharField(source='contratista.razon_social', read_only=True)

    class Meta:
        model = AlertaMorosidad
        fields = [
            'id',
            'alquiler',
            'alquiler_codigo',
            'contratista',
            'contratista_nombre',
            'fecha_deteccion',
            'dias_vencido',
            'monto_multa_calculada',
            'bloqueo_aplicado',
            'resuelta',
            'fecha_resolucion',
            'motivo_resolucion'
        ]
