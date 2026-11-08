from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid


class CategoriaHerramienta(models.Model):
    """Categoría a la que pertenece una herramienta o activo de construcción."""
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de Categoría")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Categoría de Herramienta"
        verbose_name_plural = "Categorías de Herramientas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Herramienta(models.Model):
    """Catálogo de activos y herramientas con trazabilidad de estado."""
    ESTADO_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('EN_USO', 'En Uso'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
        ('DADO_DE_BAJA', 'Dado de Baja'),
    ]

    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código Interno")
    nombre = models.CharField(max_length=150, verbose_name="Nombre / Descripción")
    categoria = models.ForeignKey(
        CategoriaHerramienta,
        on_delete=models.PROTECT,
        related_name='herramientas',
        verbose_name="Categoría"
    )
    marca = models.CharField(max_length=100, verbose_name="Marca")
    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    numero_serie = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° de Serie")
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='DISPONIBLE',
        verbose_name="Estado Operativo"
    )

    tarifa_diaria = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Tarifa Diaria de Alquiler ($CLP)"
    )
    valor_reposicion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.0,
        verbose_name="Valor de Reposición ($CLP)"
    )

    horas_uso_acumuladas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.0'),
        verbose_name="Horas de Uso Acumuladas"
    )
    umbral_horas_mantenimiento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('100.0'),
        verbose_name="Umbral para Mantención (Horas)"
    )

    fecha_adquisicion = models.DateField(null=True, blank=True, verbose_name="Fecha Adquisición")
    fecha_ultimo_mantenimiento = models.DateField(null=True, blank=True, verbose_name="Último Mantenimiento")
    fecha_proximo_mantenimiento = models.DateField(null=True, blank=True, verbose_name="Próximo Mantenimiento Programado")

    ubicacion_bodega = models.CharField(
        max_length=100,
        default="Bodega Central BuildCorp",
        verbose_name="Ubicación en Bodega"
    )
    imagen = models.ImageField(upload_to='herramientas/', blank=True, null=True, verbose_name="Foto / Imagen")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones Técnicas")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Herramienta / Activo"
        verbose_name_plural = "Herramientas y Activos"
        ordering = ['codigo']

    def __str__(self):
        return f"[{self.codigo}] {self.nombre} - {self.get_estado_display()}"

    def clean(self):
        if self.tarifa_diaria < 0:
            raise ValidationError({'tarifa_diaria': 'La tarifa diaria no puede ser negativa.'})
        if self.horas_uso_acumuladas < 0:
            raise ValidationError({'horas_uso_acumuladas': 'Las horas de uso no pueden ser negativas.'})

    @property
    def requiere_mantenimiento_preventivo(self):
        """Indica si la herramienta ha superado el umbral de horas o fecha límite."""
        if self.estado == 'DADO_DE_BAJA':
            return False
        supera_horas = self.horas_uso_acumuladas >= self.umbral_horas_mantenimiento
        fecha_vencida = False
        if self.fecha_proximo_mantenimiento:
            fecha_vencida = self.fecha_proximo_mantenimiento <= timezone.now().date()
        return supera_horas or fecha_vencida

    def cambiar_estado(self, nuevo_estado, usuario=None, motivo=""):
        """Permite cambiar de estado dejando trazabilidad en el historial."""
        if self.estado != nuevo_estado:
            estado_anterior = self.estado
            self.estado = nuevo_estado
            self.save(update_fields=['estado', 'fecha_actualizacion'])
            HistorialEstadoHerramienta.objects.create(
                herramienta=self,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado,
                usuario=usuario,
                motivo=motivo or f"Cambio de estado a {nuevo_estado}"
            )


class HistorialEstadoHerramienta(models.Model):
    """Trazabilidad completa de auditoría de cada cambio de estado de una herramienta."""
    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.CASCADE,
        related_name='historial_estados',
        verbose_name="Herramienta"
    )
    estado_anterior = models.CharField(max_length=20, verbose_name="Estado Anterior")
    estado_nuevo = models.CharField(max_length=20, verbose_name="Estado Nuevo")
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuario Responsable"
    )
    motivo = models.TextField(verbose_name="Motivo / Justificación")
    fecha_cambio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora de Cambio")

    class Meta:
        verbose_name = "Historial de Estado"
        verbose_name_plural = "Historial de Estados (Trazabilidad)"
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"{self.herramienta.codigo}: {self.estado_anterior} -> {self.estado_nuevo} ({self.fecha_cambio.strftime('%d/%m/%Y %H:%M')})"


class Contratista(models.Model):
    """Subcontratista o empresa que alquila herramientas para obras."""
    rut_empresa = models.CharField(max_length=20, unique=True, verbose_name="RUT Empresa / Subcontratista")
    razon_social = models.CharField(max_length=200, verbose_name="Razón Social")
    nombre_fantasia = models.CharField(max_length=150, blank=True, verbose_name="Nombre de Fantasía")
    contacto_nombre = models.CharField(max_length=150, verbose_name="Nombre Encargado / Contacto")
    contacto_telefono = models.CharField(max_length=30, verbose_name="Teléfono")
    contacto_email = models.EmailField(verbose_name="Correo Electrónico")
    direccion = models.CharField(max_length=255, blank=True, verbose_name="Dirección Comercial")

    bloqueado = models.BooleanField(
        default=False,
        verbose_name="Bloqueado para Alquileres",
        help_text="Si está marcado, no podrá solicitar nuevos alquileres de herramientas."
    )
    motivo_bloqueo = models.TextField(blank=True, null=True, verbose_name="Motivo del Bloqueo")
    fecha_bloqueo = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Bloqueo")

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contratista / Subcontratista"
        verbose_name_plural = "Contratistas y Subcontratistas"
        ordering = ['razon_social']

    def __str__(self):
        estado_txt = " [BLOQUEADO]" if self.bloqueado else " [ACTIVO]"
        return f"{self.razon_social} ({self.rut_empresa}){estado_txt}"

    def bloquear(self, motivo="Morosidad automática en devolución de herramientas"):
        """Bloquea al contratista impidiendo nuevas operaciones."""
        self.bloqueado = True
        self.motivo_bloqueo = motivo
        self.fecha_bloqueo = timezone.now()
        self.save(update_fields=['bloqueado', 'motivo_bloqueo', 'fecha_bloqueo'])

    def desbloquear(self):
        """Desbloquea al contratista una vez regularizada la deuda/devolución."""
        self.bloqueado = False
        self.motivo_bloqueo = ""
        self.fecha_bloqueo = None
        self.save(update_fields=['bloqueado', 'motivo_bloqueo', 'fecha_bloqueo'])


class Obra(models.Model):
    """Faena u obra de construcción donde se utilizarán las herramientas."""
    codigo = models.CharField(max_length=30, unique=True, verbose_name="Código Obra")
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Obra")
    direccion = models.CharField(max_length=255, verbose_name="Dirección de la Faena")
    comuna_ciudad = models.CharField(max_length=100, default="Santiago", verbose_name="Comuna / Ciudad")
    encargado_obra = models.CharField(max_length=150, verbose_name="Responsable en Terreno")
    telefono_encargado = models.CharField(max_length=30, blank=True, verbose_name="Teléfono Responsable")
    contratista = models.ForeignKey(
        Contratista,
        on_delete=models.CASCADE,
        related_name='obras',
        verbose_name="Contratista Asignado"
    )
    activa = models.BooleanField(default=True, verbose_name="Obra Activa")

    class Meta:
        verbose_name = "Obra / Faena"
        verbose_name_plural = "Obras y Faenas"
        ordering = ['nombre']

    def __str__(self):
        return f"[{self.codigo}] {self.nombre} ({self.contratista.razon_social})"


class AlquilerPrestamo(models.Model):
    """Registro de préstamo y alquiler de herramientas con control de fechas y estado."""
    ESTADO_CHOICES = [
        ('SOLICITADO', 'Solicitado / Pendiente de Entrega'),
        ('ACTIVO', 'Activo en Obra'),
        ('DEVUELTO', 'Devuelto / Finalizado'),
        ('VENCIDO', 'Vencido / En Morosidad'),
        ('CANCELADO', 'Cancelado'),
    ]

    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código Alquiler")
    contratista = models.ForeignKey(
        Contratista,
        on_delete=models.PROTECT,
        related_name='alquileres',
        verbose_name="Contratista"
    )
    obra = models.ForeignKey(
        Obra,
        on_delete=models.PROTECT,
        related_name='alquileres',
        verbose_name="Obra Destino"
    )
    usuario_creador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alquileres_creados',
        verbose_name="Registrado por"
    )

    fecha_inicio = models.DateField(verbose_name="Fecha Inicio Alquiler")
    fecha_fin_estimada = models.DateField(verbose_name="Fecha Devolución Pactada")
    fecha_devolucion_real = models.DateField(null=True, blank=True, verbose_name="Fecha Devolución Real")

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='SOLICITADO',
        verbose_name="Estado del Alquiler"
    )

    costo_estimado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.0'),
        verbose_name="Costo Estimado ($CLP)"
    )
    costo_final = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.0'),
        verbose_name="Costo Total Facturado ($CLP)"
    )
    dias_retraso = models.IntegerField(default=0, verbose_name="Días de Retraso")
    recargo_mora = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.0'),
        verbose_name="Recargo por Morosidad ($CLP)"
    )

    observaciones = models.TextField(blank=True, verbose_name="Observaciones / Términos")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Alquiler / Préstamo"
        verbose_name_plural = "Alquileres y Préstamos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"[{self.codigo}] {self.contratista.razon_social} - {self.get_estado_display()}"

    def clean(self):
        # Regla de negocio clave: Bloqueo de contratistas morosos
        contratista = None
        try:
            contratista = self.contratista
        except Exception:
            contratista = None

        if self.pk is None and contratista and contratista.bloqueado:
            raise ValidationError(
                f"El contratista {contratista.razon_social} se encuentra BLOQUEADO "
                f"debido a: '{contratista.motivo_bloqueo}'. No puede solicitar nuevos alquileres."
            )
        if self.fecha_inicio and self.fecha_fin_estimada:
            if self.fecha_fin_estimada < self.fecha_inicio:
                raise ValidationError({
                    'fecha_fin_estimada': 'La fecha de devolución pactada debe ser posterior o igual a la fecha de inicio.'
                })

    @property
    def dias_duracion_pactada(self):
        if self.fecha_inicio and self.fecha_fin_estimada:
            dias = (self.fecha_fin_estimada - self.fecha_inicio).days
            return max(dias, 1)
        return 1

    def calcular_costo_estimado(self):
        """Calcula el costo total proyectado según las tarifas de las herramientas."""
        total_diario = sum(detalle.tarifa_diaria_pactada for detalle in self.detalles.all())
        dias = self.dias_duracion_pactada
        self.costo_estimado = total_diario * Decimal(dias)
        self.save(update_fields=['costo_estimado'])
        return self.costo_estimado

    def verificar_morosidad(self):
        """Verifica si el préstamo está vencido respecto al día de hoy y gatilla bloqueo si aplica."""
        hoy = timezone.now().date()
        if self.estado in ['ACTIVO', 'SOLICITADO'] and self.fecha_fin_estimada < hoy:
            dias = (hoy - self.fecha_fin_estimada).days
            self.dias_retraso = dias
            self.estado = 'VENCIDO'
            # Cálculo de multa: 50% de recargo sobre tarifa diaria por cada día de mora
            total_diario = sum(detalle.tarifa_diaria_pactada for detalle in self.detalles.all())
            self.recargo_mora = total_diario * Decimal(dias) * Decimal('1.5')
            self.save(update_fields=['estado', 'dias_retraso', 'recargo_mora'])

            # Bloqueo automático del contratista
            motivo = f"Morosidad automática por vencimiento del Alquiler {self.codigo} con {dias} días de atraso."
            self.contratista.bloquear(motivo)

            # Crear o actualizar alerta de morosidad
            alerta, _ = AlertaMorosidad.objects.get_or_create(
                alquiler=self,
                contratista=self.contratista,
                defaults={
                    'dias_vencido': dias,
                    'monto_multa_calculada': self.recargo_mora,
                    'bloqueo_aplicado': True
                }
            )
            if not alerta.resuelta:
                alerta.dias_vencido = dias
                alerta.monto_multa_calculada = self.recargo_mora
                alerta.save(update_fields=['dias_vencido', 'monto_multa_calculada'])
            return True
        return False


class DetalleAlquiler(models.Model):
    """Herramientas individuales incluidas en una solicitud de alquiler."""
    alquiler = models.ForeignKey(
        AlquilerPrestamo,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Alquiler"
    )
    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.PROTECT,
        related_name='detalles_alquiler',
        verbose_name="Herramienta"
    )
    tarifa_diaria_pactada = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Tarifa Diaria Pactada ($CLP)"
    )
    horas_iniciales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.0'),
        verbose_name="Horómetro Inicial"
    )
    horas_finales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Horómetro Final al Devolver"
    )
    estado_herramienta_devolucion = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Estado Físico en Devolución"
    )
    costo_reparacion_dano = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.0'),
        verbose_name="Cobro por Daños ($CLP)"
    )

    class Meta:
        verbose_name = "Detalle de Alquiler"
        verbose_name_plural = "Detalles de Alquiler"
        unique_together = ('alquiler', 'herramienta')

    def __str__(self):
        return f"{self.alquiler.codigo} - {self.herramienta.nombre}"

    def save(self, *args, **kwargs):
        if not self.tarifa_diaria_pactada and self.herramienta:
            self.tarifa_diaria_pactada = self.herramienta.tarifa_diaria
        if self.horas_iniciales == Decimal('0.0') and self.herramienta:
            self.horas_iniciales = self.herramienta.horas_uso_acumuladas
        super().save(*args, **kwargs)


class RegistroEntrega(models.Model):
    """Módulo de entrega física de herramientas con firma digital del responsable de obra."""
    alquiler = models.OneToOneField(
        AlquilerPrestamo,
        on_delete=models.CASCADE,
        related_name='entrega',
        verbose_name="Alquiler Asociado"
    )
    fecha_hora_entrega = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora de Entrega")
    despachador_bodega = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entregas_despachadas',
        verbose_name="Despachador de Bodega"
    )
    responsable_obra_nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre Responsable de Obra Receptor"
    )
    responsable_obra_rut = models.CharField(
        max_length=20,
        verbose_name="RUT Responsable Receptor"
    )
    firma_digital = models.ImageField(
        upload_to='firmas/entregas/',
        blank=True,
        null=True,
        verbose_name="Firma Digital en Canvas (PNG)"
    )
    observaciones_entrega = models.TextField(blank=True, verbose_name="Observaciones de Entrega")

    class Meta:
        verbose_name = "Registro de Entrega (Firma Digital)"
        verbose_name_plural = "Registros de Entregas (Firmas Digitales)"

    def __str__(self):
        return f"Entrega {self.alquiler.codigo} - Receptor: {self.responsable_obra_nombre}"


class RegistroDevolucion(models.Model):
    """Módulo de devolución física de herramientas con firma digital del responsable de obra."""
    alquiler = models.OneToOneField(
        AlquilerPrestamo,
        on_delete=models.CASCADE,
        related_name='devolucion',
        verbose_name="Alquiler Asociado"
    )
    fecha_hora_devolucion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora de Devolución")
    receptor_bodega = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='devoluciones_recibidas',
        verbose_name="Bodeguero Receptor"
    )
    responsable_obra_nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre Responsable de Obra que Entrega"
    )
    responsable_obra_rut = models.CharField(
        max_length=20,
        verbose_name="RUT Responsable"
    )
    firma_digital = models.ImageField(
        upload_to='firmas/devoluciones/',
        blank=True,
        null=True,
        verbose_name="Firma Digital en Canvas (PNG)"
    )
    estado_general_equipos = models.CharField(
        max_length=100,
        default="Operativo en óptimas condiciones",
        verbose_name="Estado General de los Equipos"
    )
    observaciones_devolucion = models.TextField(blank=True, verbose_name="Observaciones de Devolución")

    class Meta:
        verbose_name = "Registro de Devolución (Firma Digital)"
        verbose_name_plural = "Registros de Devoluciones (Firmas Digitales)"

    def __str__(self):
        return f"Devolución {self.alquiler.codigo} - Entregado por: {self.responsable_obra_nombre}"


class Mantenimiento(models.Model):
    """Programación y registro de mantenimientos preventivos y correctivos."""
    TIPO_CHOICES = [
        ('PREVENTIVO', 'Mantenimiento Preventivo (Horómetro / Fecha)'),
        ('CORRECTIVO', 'Mantenimiento Correctivo (Reparación de Falla)'),
        ('CALIBRACION', 'Calibración / Certificación de Seguridad'),
    ]

    ESTADO_CHOICES = [
        ('PROGRAMADO', 'Programado'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]

    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.CASCADE,
        related_name='mantenimientos',
        verbose_name="Herramienta"
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='PREVENTIVO', verbose_name="Tipo de Mantenimiento")
    fecha_programada = models.DateField(verbose_name="Fecha Programada")
    fecha_ejecucion = models.DateField(null=True, blank=True, verbose_name="Fecha de Ejecución")

    horas_uso_al_programar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.0'),
        verbose_name="Horómetro al Programar"
    )
    horas_limite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Horómetro Límite para Ejecución"
    )

    tecnico_responsable = models.CharField(
        max_length=150,
        default="Taller Central BuildCorp",
        verbose_name="Técnico / Taller Responsable"
    )
    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.0'),
        verbose_name="Costo de Mantención ($CLP)"
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PROGRAMADO',
        verbose_name="Estado de Mantención"
    )

    descripcion_trabajo = models.TextField(verbose_name="Descripción de Trabajos a Realizar")
    repuestos_utilizados = models.TextField(blank=True, verbose_name="Repuestos e Insumos Utilizados")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mantenimiento de Herramienta"
        verbose_name_plural = "Mantenimientos Preventivos y Correctivos"
        ordering = ['fecha_programada']

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.herramienta.codigo} - {self.get_estado_display()}"

    def completar_mantenimiento(self, costo_final, repuestos="", fecha=None):
        """Finaliza el mantenimiento, actualiza el estado de la herramienta y reprograma el ciclo."""
        self.estado = 'COMPLETADO'
        self.costo = costo_final
        self.repuestos_utilizados = repuestos
        self.fecha_ejecucion = fecha or timezone.now().date()
        self.save()

        # Actualizar herramienta asociada
        herramienta = self.herramienta
        herramienta.fecha_ultimo_mantenimiento = self.fecha_ejecucion
        # Reprogramar próximo mantenimiento para dentro de 90 días o nuevo ciclo de horas
        herramienta.fecha_proximo_mantenimiento = self.fecha_ejecucion + timezone.timedelta(days=90)
        # Cambiar estado a DISPONIBLE si estaba en mantenimiento
        if herramienta.estado == 'MANTENIMIENTO':
            herramienta.cambiar_estado(
                'DISPONIBLE',
                usuario=None,
                motivo=f"Mantenimiento #{self.pk} completado con éxito."
            )
        else:
            herramienta.save()


class AlertaMorosidad(models.Model):
    """Sistema de alertas por morosidad en devoluciones y bloqueo automático."""
    alquiler = models.ForeignKey(
        AlquilerPrestamo,
        on_delete=models.CASCADE,
        related_name='alertas',
        verbose_name="Alquiler Vencido"
    )
    contratista = models.ForeignKey(
        Contratista,
        on_delete=models.CASCADE,
        related_name='alertas_morosidad',
        verbose_name="Contratista Moroso"
    )
    fecha_deteccion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Detección")
    dias_vencido = models.IntegerField(default=1, verbose_name="Días Vencido")
    monto_multa_calculada = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.0'),
        verbose_name="Multa Calculada ($CLP)"
    )
    bloqueo_aplicado = models.BooleanField(default=True, verbose_name="Bloqueo Automático Aplicado")
    resuelta = models.BooleanField(default=False, verbose_name="Alerta Resuelta / Regularizada")
    fecha_resolucion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Resolución")
    motivo_resolucion = models.TextField(blank=True, verbose_name="Motivo de Regularización")

    class Meta:
        verbose_name = "Alerta de Morosidad"
        verbose_name_plural = "Alertas de Morosidad y Bloqueos"
        ordering = ['-fecha_deteccion']

    def __str__(self):
        estado_str = "RESUELTA" if self.resuelta else "PENDIENTE"
        return f"Alerta {self.alquiler.codigo} - {self.contratista.razon_social} ({self.dias_vencido} días mora) [{estado_str}]"

    def resolver(self, usuario=None, motivo="Herramientas devueltas y multas regularizadas"):
        """Marca la alerta como resuelta y evalúa desbloquear al contratista si no tiene más deudas."""
        self.resuelta = True
        self.fecha_resolucion = timezone.now()
        self.motivo_resolucion = motivo
        self.save(update_fields=['resuelta', 'fecha_resolucion', 'motivo_resolucion'])

        # Verificar si tiene otras alertas pendientes
        alertas_pendientes = AlertaMorosidad.objects.filter(
            contratista=self.contratista,
            resuelta=False
        ).exists()

        if not alertas_pendientes:
            self.contratista.desbloquear()
