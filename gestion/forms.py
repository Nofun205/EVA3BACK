from django import forms
from django.utils import timezone
from .models import (
    Herramienta,
    CategoriaHerramienta,
    Contratista,
    Obra,
    AlquilerPrestamo,
    DetalleAlquiler,
    RegistroEntrega,
    RegistroDevolucion,
    Mantenimiento,
    AlertaMorosidad
)


class HerramientaForm(forms.ModelForm):
    class Meta:
        model = Herramienta
        fields = [
            'codigo', 'nombre', 'categoria', 'marca', 'modelo', 'numero_serie',
            'estado', 'tarifa_diaria', 'valor_reposicion', 'horas_uso_acumuladas',
            'umbral_horas_mantenimiento', 'fecha_adquisicion', 'fecha_proximo_mantenimiento',
            'ubicacion_bodega', 'imagen', 'observaciones'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: HER-010'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Rotomartillo SDS Max'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'tarifa_diaria': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'valor_reposicion': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'horas_uso_acumuladas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'umbral_horas_mantenimiento': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '1'}),
            'fecha_adquisicion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_proximo_mantenimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ubicacion_bodega': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ContratistaForm(forms.ModelForm):
    class Meta:
        model = Contratista
        fields = [
            'rut_empresa', 'razon_social', 'nombre_fantasia',
            'contacto_nombre', 'contacto_telefono', 'contacto_email',
            'direccion', 'bloqueado', 'motivo_bloqueo'
        ]
        widgets = {
            'rut_empresa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 76.543.210-K'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Constructora Titanium SpA'}),
            'nombre_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 1234 5678'}),
            'contacto_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contacto@empresa.cl'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'bloqueado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'motivo_bloqueo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Razón de la sanción o bloqueo'}),
        }


class ObraForm(forms.ModelForm):
    class Meta:
        model = Obra
        fields = ['codigo', 'nombre', 'contratista', 'direccion', 'comuna_ciudad', 'encargado_obra', 'telefono_encargado', 'activa']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: OBR-005'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'contratista': forms.Select(attrs={'class': 'form-select'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'comuna_ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'encargado_obra': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_encargado': forms.TextInput(attrs={'class': 'form-control'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AlquilerPrestamoForm(forms.ModelForm):
    herramientas = forms.ModelMultipleChoiceField(
        queryset=Herramienta.objects.filter(estado='DISPONIBLE'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8}),
        help_text="Seleccione una o más herramientas disponibles para este arriendo."
    )

    class Meta:
        model = AlquilerPrestamo
        fields = ['codigo', 'contratista', 'obra', 'fecha_inicio', 'fecha_fin_estimada', 'observaciones']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: ALQ-2026-0010'}),
            'contratista': forms.Select(attrs={'class': 'form-select'}),
            'obra': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin_estimada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_contratista(self):
        contratista = self.cleaned_data.get('contratista')
        if contratista and contratista.bloqueado:
            raise forms.ValidationError(
                f"El contratista {contratista.razon_social} se encuentra BLOQUEADO "
                f"debido a: '{contratista.motivo_bloqueo}'. No es posible autorizar nuevos alquileres."
            )
        return contratista

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get('fecha_inicio')
        fin = cleaned_data.get('fecha_fin_estimada')
        if inicio and fin and fin < inicio:
            self.add_error('fecha_fin_estimada', 'La fecha pactada no puede ser anterior a la fecha de inicio.')
        return cleaned_data


class EntregaForm(forms.Form):
    responsable_obra_nombre = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre y Apellidos'})
    )
    responsable_obra_rut = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'})
    )
    firma_digital_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
        help_text="Firma digital obligatoria capturada en pantalla táctil o mouse."
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observaciones de despacho'})
    )


class DevolucionForm(forms.Form):
    responsable_obra_nombre = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre quien entrega'})
    )
    responsable_obra_rut = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'})
    )
    estado_general = forms.ChoiceField(
        choices=[
            ('Operativo en óptimas condiciones', 'Operativo en óptimas condiciones'),
            ('Desgaste normal de faena', 'Desgaste normal de faena'),
            ('Con daños / Requiere reparación técnica', 'Con daños / Requiere reparación técnica'),
            ('Inoperativo / Averiado grave', 'Inoperativo / Averiado grave')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    firma_digital_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Detalles de la recepción y revisión'})
    )


class MantenimientoForm(forms.ModelForm):
    class Meta:
        model = Mantenimiento
        fields = [
            'herramienta', 'tipo', 'fecha_programada', 'horas_limite',
            'tecnico_responsable', 'costo', 'estado', 'descripcion_trabajo', 'repuestos_utilizados'
        ]
        widgets = {
            'herramienta': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_programada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'horas_limite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'tecnico_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'descripcion_trabajo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'repuestos_utilizados': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
