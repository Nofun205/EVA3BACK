from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.http import HttpResponse
import csv

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

# Personalización del Panel Django Admin
admin.site.site_header = "BuildCorp | Gestión de Herramientas y Alquileres"
admin.site.site_title = "BuildCorp Portal Admin"
admin.site.index_title = "Panel de Control Operativo - BuildCorp"


def exportar_a_csv(modeladmin, request, queryset):
    """Acción administrativa para exportar registros seleccionados a CSV compatible con Microsoft Excel."""
    opts = modeladmin.model._meta
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename=BuildCorp_{opts.verbose_name_plural}.csv'
    response.write(u'\ufeff'.encode('utf8')) # BOM para que Excel reconozca tildes y caracteres en español
    writer = csv.writer(response, delimiter=';')

    fields = [field for field in opts.get_fields() if not field.many_to_many and not field.one_to_many]
    writer.writerow([field.verbose_name.title() if hasattr(field, 'verbose_name') else field.name for field in fields])
    for obj in queryset:
        row = []
        for field in fields:
            val = getattr(obj, field.name, '')
            if callable(val):
                val = val()
            row.append(str(val) if val is not None else '')
        writer.writerow(row)
    return response

exportar_a_csv.short_description = "📥 Exportar registros seleccionados a CSV / Excel"


class HistorialEstadoHerramientaInline(admin.TabularInline):
    model = HistorialEstadoHerramienta
    extra = 0
    readonly_fields = ('estado_anterior', 'estado_nuevo', 'usuario', 'motivo', 'fecha_cambio')
    can_delete = False
    ordering = ('-fecha_cambio',)


class DetalleAlquilerInline(admin.TabularInline):
    model = DetalleAlquiler
    extra = 1
    autocomplete_fields = ('herramienta',)


@admin.register(CategoriaHerramienta)
class CategoriaHerramientaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'total_herramientas')
    search_fields = ('nombre', 'descripcion')
    actions = [exportar_a_csv]

    def total_herramientas(self, obj):
        return obj.herramientas.count()
    total_herramientas.short_description = "N° Herramientas"


@admin.register(Herramienta)
class HerramientaAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'nombre',
        'categoria',
        'marca',
        'modelo',
        'tarifa_diaria_fmt',
        'horas_uso_acumuladas',
        'estado_badge',
        'mantenimiento_status'
    )
    list_filter = ('estado', 'categoria', 'marca', 'ubicacion_bodega')
    search_fields = ('codigo', 'nombre', 'marca', 'modelo', 'numero_serie')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    inlines = [HistorialEstadoHerramientaInline]
    actions = ['marcar_como_en_mantenimiento', 'marcar_como_disponible', exportar_a_csv]

    def tarifa_diaria_fmt(self, obj):
        return f"${obj.tarifa_diaria:,.0f} CLP"
    tarifa_diaria_fmt.short_description = "Tarifa Diaria"

    def estado_badge(self, obj):
        colores = {
            'DISPONIBLE': '#10b981',      # Emerald
            'EN_USO': '#3b82f6',          # Blue
            'MANTENIMIENTO': '#f59e0b',   # Amber
            'DADO_DE_BAJA': '#ef4444',    # Rose
        }
        color = colores.get(obj.estado, '#6c757d')
        texto_color = '#ffffff'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 11px; display: inline-block;">{}</span>',
            color,
            texto_color,
            obj.get_estado_display()
        )
    estado_badge.short_description = "Estado"

    def mantenimiento_status(self, obj):
        if obj.requiere_mantenimiento_preventivo:
            return mark_safe('<span style="color: #ef4444; font-weight: 800; background: #fee2e2; padding: 3px 8px; border-radius: 12px; font-size: 11px;">⚠️ Requiere Mantención</span>')
        return mark_safe('<span style="color: #10b981; font-weight: 700; font-size: 11px;"><i class="fa-solid fa-check"></i> Al Día</span>')
    mantenimiento_status.short_description = "Alerta Mantención"

    @admin.action(description="🛠️ Marcar herramientas seleccionadas en Mantenimiento")
    def marcar_como_en_mantenimiento(self, request, queryset):
        for tool in queryset:
            tool.cambiar_estado('MANTENIMIENTO', usuario=request.user, motivo="Envío manual a mantención desde Django Admin")
        self.message_user(request, f"{queryset.count()} herramientas pasadas a Mantenimiento.")

    @admin.action(description="✅ Marcar herramientas seleccionadas como Disponibles")
    def marcar_como_disponible(self, request, queryset):
        for tool in queryset:
            tool.cambiar_estado('DISPONIBLE', usuario=request.user, motivo="Habilitación manual desde Django Admin")
        self.message_user(request, f"{queryset.count()} herramientas marcadas como Disponibles.")


@admin.register(HistorialEstadoHerramienta)
class HistorialEstadoHerramientaAdmin(admin.ModelAdmin):
    list_display = ('herramienta', 'estado_anterior', 'estado_nuevo', 'usuario', 'fecha_cambio', 'motivo')
    list_filter = ('estado_nuevo', 'fecha_cambio')
    search_fields = ('herramienta__codigo', 'herramienta__nombre', 'motivo')
    date_hierarchy = 'fecha_cambio'
    readonly_fields = ('herramienta', 'estado_anterior', 'estado_nuevo', 'usuario', 'motivo', 'fecha_cambio')
    actions = [exportar_a_csv]


@admin.register(Contratista)
class ContratistaAdmin(admin.ModelAdmin):
    list_display = (
        'rut_empresa',
        'razon_social',
        'contacto_nombre',
        'contacto_telefono',
        'contacto_email',
        'estado_bloqueo_badge'
    )
    list_filter = ('bloqueado',)
    search_fields = ('rut_empresa', 'razon_social', 'nombre_fantasia', 'contacto_nombre', 'contacto_email')
    date_hierarchy = 'fecha_creacion'
    actions = ['bloquear_contratistas', 'desbloquear_contratistas', exportar_a_csv]

    def estado_bloqueo_badge(self, obj):
        if obj.bloqueado:
            return mark_safe(
                '<span style="background-color: #ef4444; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 11px;">⛔ BLOQUEADO</span>'
            )
        return mark_safe(
            '<span style="background-color: #10b981; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 11px;">✔ HABILITADO</span>'
        )
    estado_bloqueo_badge.short_description = "Estado Comercial"

    @admin.action(description="⛔ Bloquear contratistas seleccionados")
    def bloquear_contratistas(self, request, queryset):
        for c in queryset:
            c.bloquear("Bloqueo manual administrativo desde Django Admin")
        self.message_user(request, f"{queryset.count()} contratistas bloqueados exitosamente.")

    @admin.action(description="🔓 Desbloquear contratistas seleccionados")
    def desbloquear_contratistas(self, request, queryset):
        for c in queryset:
            c.desbloquear()
        self.message_user(request, f"{queryset.count()} contratistas desbloqueados.")


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'contratista', 'comuna_ciudad', 'encargado_obra', 'activa')
    list_filter = ('activa', 'comuna_ciudad')
    search_fields = ('codigo', 'nombre', 'direccion', 'encargado_obra', 'contratista__razon_social')
    actions = [exportar_a_csv]


@admin.register(AlquilerPrestamo)
class AlquilerPrestamoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'contratista',
        'obra',
        'fecha_inicio',
        'fecha_fin_estimada',
        'estado_badge',
        'dias_retraso',
        'costo_estimado_fmt',
        'recargo_mora_fmt'
    )
    list_filter = ('estado', 'fecha_inicio', 'fecha_fin_estimada')
    search_fields = ('codigo', 'contratista__razon_social', 'obra__nombre')
    date_hierarchy = 'fecha_inicio'
    inlines = [DetalleAlquilerInline]
    actions = ['verificar_morosidad_lote', exportar_a_csv]

    def costo_estimado_fmt(self, obj):
        return f"${obj.costo_estimado:,.0f} CLP"
    costo_estimado_fmt.short_description = "Costo Proyectado"

    def recargo_mora_fmt(self, obj):
        if obj.recargo_mora > 0:
            return format_html('<span style="color: #ef4444; font-weight: 800; background: #fee2e2; padding: 3px 8px; border-radius: 12px;">+${:,.0f} CLP</span>', obj.recargo_mora)
        return "$0 CLP"
    recargo_mora_fmt.short_description = "Recargo Mora"

    def estado_badge(self, obj):
        colores = {
            'SOLICITADO': '#64748b',
            'ACTIVO': '#3b82f6',
            'DEVUELTO': '#10b981',
            'VENCIDO': '#ef4444',
            'CANCELADO': '#0f172a',
        }
        color = colores.get(obj.estado, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 11px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = "Estado Alquiler"

    @admin.action(description="⚡ Ejecutar verificación de morosidad y bloqueo automático")
    def verificar_morosidad_lote(self, request, queryset):
        bloqueados = 0
        for alq in queryset:
            if alq.verificar_morosidad():
                bloqueados += 1
        self.message_user(request, f"Verificación completada: {bloqueados} contratos pasaron a VENCIDO y sus contratistas fueron bloqueados.")


@admin.register(RegistroEntrega)
class RegistroEntregaAdmin(admin.ModelAdmin):
    list_display = ('alquiler', 'fecha_hora_entrega', 'responsable_obra_nombre', 'responsable_obra_rut', 'firma_preview')
    search_fields = ('alquiler__codigo', 'responsable_obra_nombre', 'responsable_obra_rut')
    date_hierarchy = 'fecha_hora_entrega'
    actions = [exportar_a_csv]

    def firma_preview(self, obj):
        if obj.firma_digital:
            return format_html('<img src="{}" style="max-height: 40px; border: 1px solid #cbd5e1; border-radius: 4px; background: #fff;" />', obj.firma_digital.url)
        return "Sin Firma"
    firma_preview.short_description = "Firma Digital"


@admin.register(RegistroDevolucion)
class RegistroDevolucionAdmin(admin.ModelAdmin):
    list_display = ('alquiler', 'fecha_hora_devolucion', 'responsable_obra_nombre', 'estado_general_equipos', 'firma_preview')
    search_fields = ('alquiler__codigo', 'responsable_obra_nombre', 'responsable_obra_rut')
    date_hierarchy = 'fecha_hora_devolucion'
    actions = [exportar_a_csv]

    def firma_preview(self, obj):
        if obj.firma_digital:
            return format_html('<img src="{}" style="max-height: 40px; border: 1px solid #cbd5e1; border-radius: 4px; background: #fff;" />', obj.firma_digital.url)
        return "Sin Firma"
    firma_preview.short_description = "Firma Digital"


@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = (
        'herramienta',
        'tipo',
        'fecha_programada',
        'horas_limite',
        'tecnico_responsable',
        'costo_fmt',
        'estado_badge'
    )
    list_filter = ('tipo', 'estado', 'fecha_programada')
    search_fields = ('herramienta__codigo', 'herramienta__nombre', 'tecnico_responsable', 'descripcion_trabajo')
    date_hierarchy = 'fecha_programada'
    actions = ['marcar_completado', exportar_a_csv]

    def costo_fmt(self, obj):
        return f"${obj.costo:,.0f} CLP"
    costo_fmt.short_description = "Costo"

    def estado_badge(self, obj):
        colores = {
            'PROGRAMADO': '#f59e0b',
            'EN_PROCESO': '#3b82f6',
            'COMPLETADO': '#10b981',
            'CANCELADO': '#ef4444',
        }
        color = colores.get(obj.estado, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 11px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = "Estado Mantenimiento"

    @admin.action(description="✔ Finalizar y completar mantenimientos seleccionados")
    def marcar_completado(self, request, queryset):
        for m in queryset:
            m.completar_mantenimiento(costo_final=m.costo or 0, repuestos="Finalizado desde admin")
        self.message_user(request, f"{queryset.count()} mantenimientos completados.")


@admin.register(AlertaMorosidad)
class AlertaMorosidadAdmin(admin.ModelAdmin):
    list_display = (
        'alquiler',
        'contratista',
        'fecha_deteccion',
        'dias_vencido',
        'multa_fmt',
        'bloqueo_badge',
        'estado_alerta_badge'
    )
    list_filter = ('resuelta', 'bloqueo_aplicado', 'fecha_deteccion')
    search_fields = ('alquiler__codigo', 'contratista__razon_social')
    date_hierarchy = 'fecha_deteccion'
    actions = ['resolver_alertas_seleccionadas', exportar_a_csv]

    def multa_fmt(self, obj):
        return f"${obj.monto_multa_calculada:,.0f} CLP"
    multa_fmt.short_description = "Multa Calculada"

    def bloqueo_badge(self, obj):
        if obj.bloqueo_aplicado:
            return mark_safe('<span style="color: #ef4444; font-weight: 800;">⛔ Sancionado</span>')
        return "No"
    bloqueo_badge.short_description = "Bloqueo"

    def estado_alerta_badge(self, obj):
        if obj.resuelta:
            return mark_safe('<span style="background-color: #10b981; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 11px;">RESUELTA</span>')
        return mark_safe('<span style="background-color: #ef4444; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 11px;">PENDIENTE</span>')
    estado_alerta_badge.short_description = "Estado"

    @admin.action(description="✔ Regularizar y resolver alertas seleccionadas (desbloquea contratistas)")
    def resolver_alertas_seleccionadas(self, request, queryset):
        for a in queryset:
            a.resolver(usuario=request.user, motivo="Regularizado desde acción administrativa")
        self.message_user(request, f"{queryset.count()} alertas resueltas y contratistas regularizados.")
