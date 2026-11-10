from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import datetime

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
from .views import procesar_firma_base64


class BuildCorpCoreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testadmin',
            email='admin@test.cl',
            password='Password123!',
            is_staff=True
        )
        self.client = Client()
        self.client.login(username='testadmin', password='Password123!')

        self.categoria = CategoriaHerramienta.objects.create(
            nombre='Perforación y Demolición',
            descripcion='Herramientas de impacto'
        )

        self.herramienta = Herramienta.objects.create(
            codigo='ROT-101',
            nombre='Rotomartillo Industrial 1500W',
            categoria=self.categoria,
            marca='Makita',
            modelo='HR4013C',
            tarifa_diaria=Decimal('20000'),
            horas_uso_acumuladas=Decimal('95.0'),
            umbral_horas_mantenimiento=Decimal('100.0'),
            estado='DISPONIBLE'
        )

        self.contratista = Contratista.objects.create(
            rut_empresa='76.111.222-3',
            razon_social='Constructora Los Álamos SpA',
            contacto_nombre='Pedro Morales',
            contacto_telefono='+56 9 1122 3344',
            contacto_email='pedro@losalamos.cl'
        )

        self.obra = Obra.objects.create(
            codigo='OBR-100',
            nombre='Torre Alameda Centro',
            direccion='Av. Libertador Bernardo O Higgins 1000',
            comuna_ciudad='Santiago',
            encargado_obra='Ing. Carlos Soto',
            contratista=self.contratista
        )

    def test_cambio_estado_con_trazabilidad(self):
        """Verifica que al cambiar estado de herramienta se genere registro en HistorialEstadoHerramienta."""
        self.assertEqual(self.herramienta.estado, 'DISPONIBLE')
        self.herramienta.cambiar_estado('EN_USO', usuario=self.user, motivo='Despachado a faena')

        self.assertEqual(self.herramienta.estado, 'EN_USO')
        historial = HistorialEstadoHerramienta.objects.filter(herramienta=self.herramienta).first()
        self.assertIsNotNone(historial)
        self.assertEqual(historial.estado_anterior, 'DISPONIBLE')
        self.assertEqual(historial.estado_nuevo, 'EN_USO')
        self.assertEqual(historial.usuario, self.user)

    def test_alerta_mantenimiento_preventivo_por_horas(self):
        """Verifica que la herramienta detecte cuando supera el umbral de horas de mantenimiento."""
        self.assertFalse(self.herramienta.requiere_mantenimiento_preventivo)
        # Sumamos 10 horas -> total 105 hrs > 100 hrs umbral
        self.herramienta.horas_uso_acumuladas = Decimal('105.0')
        self.herramienta.save()
        self.assertTrue(self.herramienta.requiere_mantenimiento_preventivo)

    def test_bloqueo_automatico_por_morosidad(self):
        """Verifica la detección automática de morosidad y bloqueo del contratista."""
        hoy = timezone.now().date()
        # Creamos un alquiler vencido
        alquiler = AlquilerPrestamo.objects.create(
            codigo='ALQ-TEST-001',
            contratista=self.contratista,
            obra=self.obra,
            usuario_creador=self.user,
            fecha_inicio=hoy - datetime.timedelta(days=7),
            fecha_fin_estimada=hoy - datetime.timedelta(days=2), # Vencido hace 2 días
            estado='ACTIVO'
        )
        DetalleAlquiler.objects.create(
            alquiler=alquiler,
            herramienta=self.herramienta,
            tarifa_diaria_pactada=Decimal('20000')
        )

        self.assertFalse(self.contratista.bloqueado)

        # Ejecutamos verificación
        fue_bloqueado = alquiler.verificar_morosidad()
        self.assertTrue(fue_bloqueado)
        self.assertEqual(alquiler.estado, 'VENCIDO')
        self.assertEqual(alquiler.dias_retraso, 2)
        self.assertGreater(alquiler.recargo_mora, Decimal('0'))

        # El contratista debe estar bloqueado
        self.contratista.refresh_from_db()
        self.assertTrue(self.contratista.bloqueado)

        # Debe haberse creado la alerta
        alerta = AlertaMorosidad.objects.filter(alquiler=alquiler).first()
        self.assertIsNotNone(alerta)
        self.assertFalse(alerta.resuelta)

    def test_bloqueo_impide_nuevo_alquiler(self):
        """Verifica la regla de negocio que prohíbe crear un alquiler para un contratista bloqueado."""
        self.contratista.bloquear('Sancionado por morosidad')
        self.assertTrue(self.contratista.bloqueado)

        response = self.client.post('/alquileres/nuevo/', {
            'codigo': 'ALQ-TEST-BLOQUEADO',
            'contratista': self.contratista.id,
            'obra': self.obra.id,
            'fecha_inicio': timezone.now().date(),
            'fecha_fin_estimada': timezone.now().date() + datetime.timedelta(days=2),
            'herramientas': [self.herramienta.id]
        })

        # Debe fallar la validación y no crearse el alquiler
        self.assertFalse(AlquilerPrestamo.objects.filter(codigo='ALQ-TEST-BLOQUEADO').exists())

    def test_firma_digital_procesador(self):
        """Verifica que el procesador de base64 convierta correctamente a un ContentFile."""
        # Imagen PNG 1x1 píxel en base64
        base64_demo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        archivo = procesar_firma_base64(base64_demo, prefijo="test_firma")
        self.assertIsNotNone(archivo)
        self.assertTrue(archivo.name.startswith("test_firma_"))
        self.assertTrue(archivo.name.endswith(".png"))

    def test_vistas_principales_responden_200(self):
        """Verifica que las rutas web principales respondan con código HTTP 200."""
        rutas = [
            '/',
            '/herramientas/',
            f'/herramientas/{self.herramienta.id}/',
            '/contratistas/',
            f'/contratistas/{self.contratista.id}/',
            '/obras/',
            '/alquileres/',
            '/mantenimientos/',
            '/alertas/',
        ]
        for ruta in rutas:
            res = self.client.get(ruta)
            self.assertEqual(res.status_code, 200, f"Falla en ruta {ruta}")

    def test_api_rest_endpoints(self):
        """Verifica los endpoints de Django REST Framework."""
        res_herramientas = self.client.get('/api/herramientas/')
        self.assertEqual(res_herramientas.status_code, 200)

        res_disponibles = self.client.get('/api/herramientas/disponibles/')
        self.assertEqual(res_disponibles.status_code, 200)

        res_contratistas = self.client.get('/api/contratistas/')
        self.assertEqual(res_contratistas.status_code, 200)

    def test_admin_vistas_responden_200(self):
        """Verifica que el panel de Django Admin y sus formularios respondan 200."""
        self.user.is_superuser = True
        self.user.save()
        admin_rutas = [
            '/admin/',
            '/admin/gestion/herramienta/',
            '/admin/gestion/herramienta/add/',
            '/admin/gestion/contratista/',
            '/admin/gestion/contratista/add/',
            '/admin/gestion/obra/',
            '/admin/gestion/obra/add/',
            '/admin/gestion/alquilerprestamo/',
            '/admin/gestion/alquilerprestamo/add/',
            '/admin/gestion/mantenimiento/',
            '/admin/gestion/alertamorosidad/',
        ]
        for ruta in admin_rutas:
            res = self.client.get(ruta)
            self.assertEqual(res.status_code, 200, f"Falla en admin ruta {ruta}")

