from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.files.base import ContentFile
from decimal import Decimal
import base64
import uuid

from .models import (
    Herramienta,
    CategoriaHerramienta,
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
from .forms import (
    HerramientaForm,
    ContratistaForm,
    ObraForm,
    AlquilerPrestamoForm,
    EntregaForm,
    DevolucionForm,
    MantenimientoForm
)


def procesar_firma_base64(data_url, prefijo="firma"):
    """Convierte data:image/png;base64 en ContentFile para guardar en ImageField."""
    if not data_url or "base64," not in data_url:
        return None
    header, base64_data = data_url.split("base64,")
    decoded = base64.b64decode(base64_data)
    nombre = f"{prefijo}_{uuid.uuid4().hex[:8]}.png"
    return ContentFile(decoded, name=nombre)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"¡Bienvenido(a) a BuildCorp, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Usuario o contraseña inválidos.")
    else:
        form = AuthenticationForm()
    return render(request, 'gestion/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect('login')


@login_required
def dashboard(request):
    # Métricas generales de control
    total_herramientas = Herramienta.objects.count()
    herramientas_disponibles = Herramienta.objects.filter(estado='DISPONIBLE').count()
    herramientas_en_uso = Herramienta.objects.filter(estado='EN_USO').count()
    herramientas_mantenimiento = Herramienta.objects.filter(estado='MANTENIMIENTO').count()
    herramientas_alerta_mant = [h for h in Herramienta.objects.exclude(estado='DADO_DE_BAJA') if h.requiere_mantenimiento_preventivo]

    alquileres_activos = AlquilerPrestamo.objects.filter(estado='ACTIVO').count()
    alquileres_vencidos = AlquilerPrestamo.objects.filter(estado='VENCIDO').count()
    contratistas_bloqueados = Contratista.objects.filter(bloqueado=True).count()
    alertas_morosidad_pendientes = AlertaMorosidad.objects.filter(resuelta=False).select_related('alquiler', 'contratista')[:5]

    ultimos_alquileres = AlquilerPrestamo.objects.select_related('contratista', 'obra').order_by('-fecha_creacion')[:6]
    proximos_mantenimientos = Mantenimiento.objects.filter(estado='PROGRAMADO').select_related('herramienta').order_by('fecha_programada')[:5]

    context = {
        'total_herramientas': total_herramientas,
        'herramientas_disponibles': herramientas_disponibles,
        'herramientas_en_uso': herramientas_en_uso,
        'herramientas_mantenimiento': herramientas_mantenimiento,
        'herramientas_alerta_mant_count': len(herramientas_alerta_mant),
        'herramientas_alerta_mant': herramientas_alerta_mant[:5],
        'alquileres_activos': alquileres_activos,
        'alquileres_vencidos': alquileres_vencidos,
        'contratistas_bloqueados': contratistas_bloqueados,
        'alertas_morosidad': alertas_morosidad_pendientes,
        'ultimos_alquileres': ultimos_alquileres,
        'proximos_mantenimientos': proximos_mantenimientos,
    }
    return render(request, 'gestion/dashboard.html', context)


# ==============================================================================
# VISTAS DE HERRAMIENTAS / ACTIVOS (CATÁLOGO Y TRAZABILIDAD)
# ==============================================================================

@login_required
def herramientas_list(request):
    queryset = Herramienta.objects.select_related('categoria').all()
    estado = request.GET.get('estado')
    categoria = request.GET.get('categoria')
    q = request.GET.get('q')

    if estado:
        queryset = queryset.filter(estado=estado)
    if categoria:
        queryset = queryset.filter(categoria_id=categoria)
    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) |
            Q(nombre__icontains=q) |
            Q(marca__icontains=q) |
            Q(modelo__icontains=q)
        )

    categorias = CategoriaHerramienta.objects.all()
    return render(request, 'gestion/herramientas_list.html', {
        'herramientas': queryset,
        'categorias': categorias,
        'estado_filtro': estado,
        'categoria_filtro': categoria,
        'q': q
    })


@login_required
def herramienta_detail(request, pk):
    herramienta = get_object_or_404(Herramienta, pk=pk)
    historial = herramienta.historial_estados.select_related('usuario').order_by('-fecha_cambio')
    mantenimientos = herramienta.mantenimientos.order_by('-fecha_programada')
    alquileres_detalles = herramienta.detalles_alquiler.select_related('alquiler__contratista', 'alquiler__obra').order_by('-alquiler__fecha_creacion')[:10]

    return render(request, 'gestion/herramienta_detail.html', {
        'herramienta': herramienta,
        'historial': historial,
        'mantenimientos': mantenimientos,
        'alquileres_detalles': alquileres_detalles
    })


@login_required
def herramienta_create(request):
    if request.method == 'POST':
        form = HerramientaForm(request.POST, request.FILES)
        if form.is_valid():
            herramienta = form.save()
            HistorialEstadoHerramienta.objects.create(
                herramienta=herramienta,
                estado_anterior='NUEVO',
                estado_nuevo=herramienta.estado,
                usuario=request.user,
                motivo="Registro inicial de herramienta en el inventario BuildCorp."
            )
            messages.success(request, f"Herramienta '{herramienta.codigo} - {herramienta.nombre}' creada con éxito.")
            return redirect('herramientas_list')
    else:
        form = HerramientaForm()
    return render(request, 'gestion/herramienta_form.html', {'form': form, 'titulo': 'Registrar Nueva Herramienta'})


@login_required
def herramienta_update(request, pk):
    herramienta = get_object_or_404(Herramienta, pk=pk)
    estado_previo = herramienta.estado
    if request.method == 'POST':
        form = HerramientaForm(request.POST, request.FILES, instance=herramienta)
        if form.is_valid():
            tool = form.save()
            if tool.estado != estado_previo:
                HistorialEstadoHerramienta.objects.create(
                    herramienta=tool,
                    estado_anterior=estado_previo,
                    estado_nuevo=tool.estado,
                    usuario=request.user,
                    motivo="Actualización manual desde formulario web."
                )
            messages.success(request, f"Herramienta {tool.codigo} actualizada correctamente.")
            return redirect('herramienta_detail', pk=tool.pk)
    else:
        form = HerramientaForm(instance=herramienta)
    return render(request, 'gestion/herramienta_form.html', {'form': form, 'titulo': f'Editar Herramienta {herramienta.codigo}'})


@login_required
def herramienta_cambiar_estado(request, pk):
    herramienta = get_object_or_404(Herramienta, pk=pk)
    if request.method == 'POST':
        nuevo_estado = request.POST.get('nuevo_estado')
        motivo = request.POST.get('motivo', 'Cambio directo de estado')
        if nuevo_estado in dict(Herramienta.ESTADO_CHOICES):
            herramienta.cambiar_estado(nuevo_estado, usuario=request.user, motivo=motivo)
            messages.success(request, f"Estado de {herramienta.codigo} cambiado a {herramienta.get_estado_display()}.")
        else:
            messages.error(request, "Estado no válido.")
    return redirect('herramienta_detail', pk=pk)


# ==============================================================================
# VISTAS DE CONTRATISTAS Y OBRAS
# ==============================================================================

@login_required
def contratistas_list(request):
    queryset = Contratista.objects.annotate(total_obras=Count('obras'), total_alquileres=Count('alquileres'))
    filtro_bloqueo = request.GET.get('bloqueado')
    q = request.GET.get('q')

    if filtro_bloqueo == 'true':
        queryset = queryset.filter(bloqueado=True)
    elif filtro_bloqueo == 'false':
        queryset = queryset.filter(bloqueado=False)

    if q:
        queryset = queryset.filter(
            Q(rut_empresa__icontains=q) |
            Q(razon_social__icontains=q) |
            Q(contacto_nombre__icontains=q)
        )

    return render(request, 'gestion/contratistas_list.html', {
        'contratistas': queryset,
        'filtro_bloqueo': filtro_bloqueo,
        'q': q
    })


@login_required
def contratista_detail(request, pk):
    contratista = get_object_or_404(Contratista, pk=pk)
    obras = contratista.obras.all()
    alquileres = contratista.alquileres.order_by('-fecha_creacion')
    alertas = contratista.alertas_morosidad.order_by('-fecha_deteccion')

    return render(request, 'gestion/contratista_detail.html', {
        'contratista': contratista,
        'obras': obras,
        'alquileres': alquileres,
        'alertas': alertas
    })


@login_required
def contratista_create(request):
    if request.method == 'POST':
        form = ContratistaForm(request.POST)
        if form.is_valid():
            contratista = form.save()
            messages.success(request, f"Contratista '{contratista.razon_social}' registrado exitosamente.")
            return redirect('contratistas_list')
    else:
        form = ContratistaForm()
    return render(request, 'gestion/contratista_form.html', {'form': form, 'titulo': 'Registrar Contratista'})


@login_required
def contratista_update(request, pk):
    contratista = get_object_or_404(Contratista, pk=pk)
    if request.method == 'POST':
        form = ContratistaForm(request.POST, instance=contratista)
        if form.is_valid():
            form.save()
            messages.success(request, f"Contratista {contratista.razon_social} actualizado.")
            return redirect('contratista_detail', pk=pk)
    else:
        form = ContratistaForm(instance=contratista)
    return render(request, 'gestion/contratista_form.html', {'form': form, 'titulo': f'Editar Contratista {contratista.razon_social}'})


@login_required
def contratista_toggle_bloqueo(request, pk):
    contratista = get_object_or_404(Contratista, pk=pk)
    if request.method == 'POST':
        if contratista.bloqueado:
            contratista.desbloquear()
            # Resolver alertas abiertas
            contratista.alertas_morosidad.filter(resuelta=False).update(
                resuelta=True,
                fecha_resolucion=timezone.now(),
                motivo_resolucion="Desbloqueo manual administrativo"
            )
            messages.success(request, f"Contratista {contratista.razon_social} ha sido DESBLOQUEADO.")
        else:
            motivo = request.POST.get('motivo_bloqueo', 'Bloqueo manual por gestión administrativa')
            contratista.bloquear(motivo)
            messages.warning(request, f"Contratista {contratista.razon_social} ha sido BLOQUEADO.")
    return redirect('contratista_detail', pk=pk)


@login_required
def obras_list(request):
    obras = Obra.objects.select_related('contratista').all()
    return render(request, 'gestion/obras_list.html', {'obras': obras})


@login_required
def obra_create(request):
    if request.method == 'POST':
        form = ObraForm(request.POST)
        if form.is_valid():
            obra = form.save()
            messages.success(request, f"Obra '{obra.nombre}' registrada.")
            return redirect('obras_list')
    else:
        form = ObraForm()
    return render(request, 'gestion/obra_form.html', {'form': form, 'titulo': 'Registrar Nueva Obra'})


# ==============================================================================
# VISTAS DE ALQUILERES, ENTREGA Y DEVOLUCIÓN CON FIRMA DIGITAL
# ==============================================================================

@login_required
def alquileres_list(request):
    queryset = AlquilerPrestamo.objects.select_related('contratista', 'obra', 'entrega', 'devolucion').all()
    estado = request.GET.get('estado')
    q = request.GET.get('q')

    if estado:
        queryset = queryset.filter(estado=estado)
    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) |
            Q(contratista__razon_social__icontains=q) |
            Q(obra__nombre__icontains=q)
        )

    return render(request, 'gestion/alquileres_list.html', {
        'alquileres': queryset,
        'estado_filtro': estado,
        'q': q
    })


@login_required
def alquiler_detail(request, pk):
    alquiler = get_object_or_404(
        AlquilerPrestamo.objects.select_related('contratista', 'obra', 'entrega', 'devolucion'),
        pk=pk
    )
    detalles = alquiler.detalles.select_related('herramienta')
    alertas = alquiler.alertas.all()

    return render(request, 'gestion/alquiler_detail.html', {
        'alquiler': alquiler,
        'detalles': detalles,
        'alertas': alertas
    })


@login_required
def alquiler_create(request):
    if request.method == 'POST':
        form = AlquilerPrestamoForm(request.POST)
        if form.is_valid():
            alquiler = form.save(commit=False)
            alquiler.usuario_creador = request.user
            alquiler.save()

            # Asignar herramientas seleccionadas
            herramientas_sel = form.cleaned_data['herramientas']
            for tool in herramientas_sel:
                DetalleAlquiler.objects.create(
                    alquiler=alquiler,
                    herramienta=tool,
                    tarifa_diaria_pactada=tool.tarifa_diaria,
                    horas_iniciales=tool.horas_uso_acumuladas
                )

            # Calcular el costo total estimado
            alquiler.calcular_costo_estimado()

            messages.success(request, f"Alquiler {alquiler.codigo} creado exitosamente con {herramientas_sel.count()} herramientas asignadas.")
            return redirect('alquiler_detail', pk=alquiler.pk)
    else:
        # Generar código automático sugerido
        count_hoy = AlquilerPrestamo.objects.count() + 1
        codigo_sugerido = f"ALQ-{timezone.now().year}-{count_hoy:04d}"
        form = AlquilerPrestamoForm(initial={'codigo': codigo_sugerido, 'fecha_inicio': timezone.now().date()})

    return render(request, 'gestion/alquiler_form.html', {'form': form})


@login_required
def alquiler_entrega(request, pk):
    """Módulo de entrega física de herramientas con firma digital del receptor."""
    alquiler = get_object_or_404(AlquilerPrestamo, pk=pk)

    if hasattr(alquiler, 'entrega'):
        messages.info(request, "La entrega de este alquiler ya fue registrada previamente.")
        return redirect('alquiler_detail', pk=pk)

    if request.method == 'POST':
        form = EntregaForm(request.POST)
        if form.is_valid():
            resp_nombre = form.cleaned_data['responsable_obra_nombre']
            resp_rut = form.cleaned_data['responsable_obra_rut']
            firma_data = form.cleaned_data['firma_digital_data']
            observaciones = form.cleaned_data['observaciones']

            archivo_firma = procesar_firma_base64(firma_data, prefijo=f"entrega_{alquiler.codigo}")

            RegistroEntrega.objects.create(
                alquiler=alquiler,
                despachador_bodega=request.user,
                responsable_obra_nombre=resp_nombre,
                responsable_obra_rut=resp_rut,
                firma_digital=archivo_firma,
                observaciones_entrega=observaciones
            )

            # Cambiar estado a ACTIVO
            alquiler.estado = 'ACTIVO'
            alquiler.save(update_fields=['estado'])

            # Cambiar estado de las herramientas a EN_USO
            for det in alquiler.detalles.all():
                det.herramienta.cambiar_estado(
                    'EN_USO',
                    usuario=request.user,
                    motivo=f"Entregada para Alquiler {alquiler.codigo} a cargo de {resp_nombre}"
                )

            messages.success(request, f"¡Entrega del alquiler {alquiler.codigo} registrada con firma digital exitosamente!")
            return redirect('alquiler_detail', pk=pk)
    else:
        form = EntregaForm(initial={
            'responsable_obra_nombre': alquiler.obra.encargado_obra,
            'responsable_obra_rut': ''
        })

    return render(request, 'gestion/entrega_form.html', {
        'alquiler': alquiler,
        'form': form,
        'detalles': alquiler.detalles.select_related('herramienta')
    })


@login_required
def alquiler_devolucion(request, pk):
    """Módulo de devolución de herramientas con firma digital, horómetros y cálculo de recargo."""
    alquiler = get_object_or_404(AlquilerPrestamo, pk=pk)

    if hasattr(alquiler, 'devolucion'):
        messages.info(request, "La devolución de este alquiler ya fue registrada.")
        return redirect('alquiler_detail', pk=pk)

    detalles = alquiler.detalles.select_related('herramienta')

    if request.method == 'POST':
        form = DevolucionForm(request.POST)
        if form.is_valid():
            resp_nombre = form.cleaned_data['responsable_obra_nombre']
            resp_rut = form.cleaned_data['responsable_obra_rut']
            estado_gral = form.cleaned_data['estado_general']
            firma_data = form.cleaned_data['firma_digital_data']
            observaciones = form.cleaned_data['observaciones']

            archivo_firma = procesar_firma_base64(firma_data, prefijo=f"devolucion_{alquiler.codigo}")

            RegistroDevolucion.objects.create(
                alquiler=alquiler,
                receptor_bodega=request.user,
                responsable_obra_nombre=resp_nombre,
                responsable_obra_rut=resp_rut,
                firma_digital=archivo_firma,
                estado_general_equipos=estado_gral,
                observaciones_devolucion=observaciones
            )

            hoy = timezone.now().date()
            alquiler.fecha_devolucion_real = hoy

            # Cálculo de atraso y multa si aplica
            if hoy > alquiler.fecha_fin_estimada:
                alquiler.dias_retraso = (hoy - alquiler.fecha_fin_estimada).days
                tarifa_diaria_total = sum(d.tarifa_diaria_pactada for d in detalles)
                alquiler.recargo_mora = tarifa_diaria_total * Decimal(alquiler.dias_retraso) * Decimal('1.5')
            else:
                alquiler.dias_retraso = 0
                alquiler.recargo_mora = Decimal('0.0')

            total_costo_reparacion = Decimal('0.0')

            # Procesar cada herramienta del detalle
            for det in detalles:
                horas_input = request.POST.get(f"horas_finales_{det.id}")
                estado_tool_input = request.POST.get(f"estado_fisico_{det.id}", "Buena")
                dano_costo_input = request.POST.get(f"costo_dano_{det.id}", "0")

                try:
                    horas_finales = Decimal(horas_input) if horas_input else det.herramienta.horas_uso_acumuladas
                except Exception:
                    horas_finales = det.herramienta.horas_uso_acumuladas

                try:
                    costo_dano = Decimal(dano_costo_input)
                except Exception:
                    costo_dano = Decimal('0.0')

                det.horas_finales = horas_finales
                det.costo_reparacion_dano = costo_dano
                det.estado_herramienta_devolucion = estado_tool_input
                det.save()

                total_costo_reparacion += costo_dano

                # Actualizar horas de la herramienta si aumentaron
                tool = det.herramienta
                if horas_finales > tool.horas_uso_acumuladas:
                    tool.horas_uso_acumuladas = horas_finales

                # Evaluar necesidad de mantenimiento preventivo o correctivo
                if estado_tool_input in ['Con Daños', 'Averiada'] or tool.requiere_mantenimiento_preventivo:
                    nuevo_estado = 'MANTENIMIENTO'
                    motivo = f"Devuelta en Alquiler {alquiler.codigo}. Estado físico: {estado_tool_input}. Horas: {horas_finales}."
                else:
                    nuevo_estado = 'DISPONIBLE'
                    motivo = f"Devuelta en Alquiler {alquiler.codigo} en condiciones operativas."

                tool.cambiar_estado(nuevo_estado, usuario=request.user, motivo=motivo)

            alquiler.costo_final = alquiler.costo_estimado + alquiler.recargo_mora + total_costo_reparacion
            alquiler.estado = 'DEVUELTO'
            alquiler.save()

            # Resolver alertas de morosidad si correspondía a este alquiler
            for alerta in alquiler.alertas.filter(resuelta=False):
                alerta.resolver(usuario=request.user, motivo="Herramientas devueltas formalmente con firma.")

            messages.success(request, f"¡Devolución de alquiler {alquiler.codigo} completada exitosamente!")
            return redirect('alquiler_detail', pk=pk)
    else:
        form = DevolucionForm(initial={
            'responsable_obra_nombre': alquiler.obra.encargado_obra,
            'responsable_obra_rut': ''
        })

    return render(request, 'gestion/devolucion_form.html', {
        'alquiler': alquiler,
        'form': form,
        'detalles': detalles
    })


# ==============================================================================
# VISTAS DE MANTENIMIENTO PREVENTIVO Y CORRECTIVO
# ==============================================================================

@login_required
def mantenimientos_list(request):
    mantenimientos = Mantenimiento.objects.select_related('herramienta').all()
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')

    if estado:
        mantenimientos = mantenimientos.filter(estado=estado)
    if tipo:
        mantenimientos = mantenimientos.filter(tipo=tipo)

    # Herramientas que requieren mantención
    herramientas_en_alerta = [h for h in Herramienta.objects.exclude(estado='DADO_DE_BAJA') if h.requiere_mantenimiento_preventivo]

    return render(request, 'gestion/mantenimientos_list.html', {
        'mantenimientos': mantenimientos,
        'herramientas_en_alerta': herramientas_en_alerta,
        'estado_filtro': estado,
        'tipo_filtro': tipo
    })


@login_required
def mantenimiento_create(request):
    herramienta_id = request.GET.get('herramienta_id')
    herramienta_inicial = None
    if herramienta_id:
        herramienta_inicial = get_object_or_404(Herramienta, pk=herramienta_id)

    if request.method == 'POST':
        form = MantenimientoForm(request.POST)
        if form.is_valid():
            mantenimiento = form.save(commit=False)
            mantenimiento.horas_uso_al_programar = mantenimiento.herramienta.horas_uso_acumuladas
            mantenimiento.save()

            # Pasar herramienta a MANTENIMIENTO
            mantenimiento.herramienta.cambiar_estado(
                'MANTENIMIENTO',
                usuario=request.user,
                motivo=f"Mantenimiento programado #{mantenimiento.pk}: {mantenimiento.descripcion_trabajo}"
            )

            messages.success(request, f"Mantenimiento programado para herramienta {mantenimiento.herramienta.codigo}.")
            return redirect('mantenimientos_list')
    else:
        initial_data = {
            'fecha_programada': timezone.now().date(),
            'tecnico_responsable': 'Taller Central BuildCorp'
        }
        if herramienta_inicial:
            initial_data['herramienta'] = herramienta_inicial
            initial_data['horas_limite'] = herramienta_inicial.horas_uso_acumuladas + Decimal('10.0')

        form = MantenimientoForm(initial=initial_data)

    return render(request, 'gestion/mantenimiento_form.html', {'form': form, 'titulo': 'Programar Mantenimiento'})


@login_required
def mantenimiento_completar(request, pk):
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)
    if request.method == 'POST':
        costo_str = request.POST.get('costo', '0')
        repuestos = request.POST.get('repuestos', 'Insumos estándar')
        try:
            costo = Decimal(costo_str)
        except Exception:
            costo = Decimal('0.0')

        mantenimiento.completar_mantenimiento(costo_final=costo, repuestos=repuestos)
        messages.success(request, f"Mantenimiento de {mantenimiento.herramienta.codigo} completado. Herramienta vuelve a estar DISPONIBLE.")
    return redirect('mantenimientos_list')


# ==============================================================================
# VISTAS DE ALERTAS POR MOROSIDAD Y BLOQUEO AUTOMÁTICO
# ==============================================================================

@login_required
def alertas_list(request):
    alertas = AlertaMorosidad.objects.select_related('alquiler__contratista', 'contratista').all()
    filtro_resuelta = request.GET.get('resuelta')

    if filtro_resuelta == 'true':
        alertas = alertas.filter(resuelta=True)
    elif filtro_resuelta == 'false' or filtro_resuelta is None:
        alertas = alertas.filter(resuelta=False)

    return render(request, 'gestion/alertas_list.html', {
        'alertas': alertas,
        'filtro_resuelta': filtro_resuelta
    })


@login_required
def alerta_resolver(request, pk):
    alerta = get_object_or_404(AlertaMorosidad, pk=pk)
    if request.method == 'POST':
        motivo = request.POST.get('motivo_resolucion', 'Regularizado por personal de bodega')
        alerta.resolver(usuario=request.user, motivo=motivo)
        messages.success(request, f"Alerta resuelta. Contratista {alerta.contratista.razon_social} evaluado para desbloqueo.")
    return redirect('alertas_list')


@login_required
def ejecutar_verificacion_morosidad_view(request):
    """Ejecuta la revisión de todos los alquileres activos vencidos, calcula mora y bloquea a morosos."""
    if request.method == 'POST':
        hoy = timezone.now().date()
        alquileres_candidatos = AlquilerPrestamo.objects.filter(
            estado__in=['ACTIVO', 'SOLICITADO'],
            fecha_fin_estimada__lt=hoy
        )
        total_bloqueados = 0
        for alq in alquileres_candidatos:
            if alq.verificar_morosidad():
                total_bloqueados += 1

        if total_bloqueados > 0:
            messages.warning(request, f"¡Atención! Se detectaron {total_bloqueados} contratos vencidos. Contratistas bloqueados automáticamente.")
        else:
            messages.success(request, "No se detectaron nuevas morosidades. Todos los contratos activos están al día.")

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
