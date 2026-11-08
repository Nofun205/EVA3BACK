from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import datetime

from gestion.models import (
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


class Command(BaseCommand):
    help = "Puebla la base de datos con datos realistas para la evaluación de BuildCorp"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("==> Creando usuarios del sistema..."))

        # 1. Superusuario y usuarios de prueba
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@buildcorp.cl',
                'first_name': 'Administrador',
                'last_name': 'BuildCorp',
                'is_staff': True,
                'is_superuser': True
            }
        )
        admin_user.set_password('Admin123!')
        admin_user.save()

        bodeguero, _ = User.objects.get_or_create(
            username='bodeguero',
            defaults={
                'email': 'bodega@buildcorp.cl',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'is_staff': True
            }
        )
        bodeguero.set_password('Bodega123!')
        bodeguero.save()

        self.stdout.write(self.style.SUCCESS("✔ Superusuario 'admin' (Admin123!) y 'bodeguero' (Bodega123!) listos."))

        # 2. Categorías de Herramientas
        self.stdout.write(self.style.NOTICE("==> Creando categorías de herramientas..."))
        cat_generacion, _ = CategoriaHerramienta.objects.get_or_create(
            nombre="Generación Eléctrica y Fuerza",
            defaults={'descripcion': "Generadores diésel/gasolina, tableros y motobombas para obra."}
        )
        cat_demolicion, _ = CategoriaHerramienta.objects.get_or_create(
            nombre="Demolición y Perforación",
            defaults={'descripcion': "Rotomartillos, martillos demoledores neumáticos y eléctricos."}
        )
        cat_compactacion, _ = CategoriaHerramienta.objects.get_or_create(
            nombre="Compactación y Hormigón",
            defaults={'descripcion': "Placas compactadoras, vibropisones y betoneras."}
        )
        cat_corte, _ = CategoriaHerramienta.objects.get_or_create(
            nombre="Corte y Desbaste",
            defaults={'descripcion': "Cortadoras de pavimento, esmeriles angulares y tronzadoras."}
        )
        cat_nivelacion, _ = CategoriaHerramienta.objects.get_or_create(
            nombre="Topografía y Nivelación",
            defaults={'descripcion': "Niveles láser rotatorios, estaciones totales y taquímetros."}
        )

        # 3. Herramientas
        self.stdout.write(self.style.NOTICE("==> Creando herramientas en catálogo..."))
        hoy = timezone.now().date()

        herramientas_data = [
            {
                'codigo': 'GEN-001',
                'nombre': 'Generador Diésel Insonorizado 6.5 kVA',
                'categoria': cat_generacion,
                'marca': 'Kipor',
                'modelo': 'KDE6700T',
                'numero_serie': 'KP-2023-8871',
                'estado': 'DISPONIBLE',
                'tarifa_diaria': Decimal('28000'),
                'valor_reposicion': Decimal('1450000'),
                'horas_uso_acumuladas': Decimal('85.0'),
                'umbral_horas_mantenimiento': Decimal('100.0'),
                'fecha_adquisicion': hoy - datetime.timedelta(days=365),
                'fecha_proximo_mantenimiento': hoy + datetime.timedelta(days=30),
                'ubicacion_bodega': 'Bodega Central - Pasillo A1'
            },
            {
                'codigo': 'DEM-002',
                'nombre': 'Martillo Demoledor SDS Hex 30mm 2000W',
                'categoria': cat_demolicion,
                'marca': 'Bosch',
                'modelo': 'GSH 16-28 Professional',
                'numero_serie': 'BSH-9921-X',
                'estado': 'DISPONIBLE',
                'tarifa_diaria': Decimal('22000'),
                'valor_reposicion': Decimal('980000'),
                'horas_uso_acumuladas': Decimal('45.0'),
                'umbral_horas_mantenimiento': Decimal('80.0'),
                'fecha_adquisicion': hoy - datetime.timedelta(days=200),
                'fecha_proximo_mantenimiento': hoy + datetime.timedelta(days=45),
                'ubicacion_bodega': 'Bodega Central - Estante B2'
            },
            {
                'codigo': 'COM-003',
                'nombre': 'Placa Compactadora Unidireccional 95 kg',
                'categoria': cat_compactacion,
                'marca': 'Wacker Neuson',
                'modelo': 'WP1550AW',
                'numero_serie': 'WN-1550-741',
                'estado': 'DISPONIBLE',
                'tarifa_diaria': Decimal('25000'),
                'valor_reposicion': Decimal('1600000'),
                'horas_uso_acumuladas': Decimal('105.0'), # Supera umbral -> Alerta mantención
                'umbral_horas_mantenimiento': Decimal('100.0'),
                'fecha_adquisicion': hoy - datetime.timedelta(days=400),
                'fecha_proximo_mantenimiento': hoy - datetime.timedelta(days=5),
                'ubicacion_bodega': 'Bodega Central - Patio de Máquinas'
            },
            {
                'codigo': 'COR-004',
                'nombre': 'Cortadora de Pavimento Disco 14" Motor Honda',
                'categoria': cat_corte,
                'marca': 'Husqvarna',
                'modelo': 'FS400LV',
                'numero_serie': 'HQ-400-0199',
                'estado': 'EN_USO',
                'tarifa_diaria': Decimal('32000'),
                'valor_reposicion': Decimal('2100000'),
                'horas_uso_acumuladas': Decimal('60.0'),
                'umbral_horas_mantenimiento': Decimal('120.0'),
                'fecha_adquisicion': hoy - datetime.timedelta(days=150),
                'fecha_proximo_mantenimiento': hoy + datetime.timedelta(days=60),
                'ubicacion_bodega': 'En Faena Edificio Vista Cordillera'
            },
            {
                'codigo': 'MAN-005',
                'nombre': 'Vibropisón Canguro 4 Tiempos 68 kg',
                'categoria': cat_compactacion,
                'marca': 'Mikasa',
                'modelo': 'MTX-70HDR',
                'numero_serie': 'MK-70-5542',
                'estado': 'MANTENIMIENTO',
                'tarifa_diaria': Decimal('24000'),
                'valor_reposicion': Decimal('1850000'),
                'horas_uso_acumuladas': Decimal('112.0'),
                'umbral_horas_mantenimiento': Decimal('100.0'),
                'fecha_adquisicion': hoy - datetime.timedelta(days=300),
                'fecha_proximo_mantenimiento': hoy - datetime.timedelta(days=2),
                'ubicacion_bodega': 'Taller Mecánico BuildCorp'
            },
            {
                'codigo': 'TOP-006',
                'nombre': 'Nivel Láser Giratorio Autonivelante 360°',
                'categoria': cat_nivelacion,
                'marca': 'DeWalt',
                'modelo': 'DW079PKR',
                'numero_serie': 'DW-079-221',
                'estado': 'DISPONIBLE',
                'tarifa_diaria': Decimal('18000'),
                'valor_reposicion': Decimal('890000'),
                'horas_uso_acumuladas': Decimal('30.0'),
                'umbral_horas_mantenimiento': Decimal('150.0'),
                'fecha_adquisicion': hoy - datetime.timedelta(days=120),
                'fecha_proximo_mantenimiento': hoy + datetime.timedelta(days=90),
                'ubicacion_bodega': 'Bodega Central - Instrumentación'
            }
        ]

        herramientas_creadas = {}
        for h_info in herramientas_data:
            tool, created = Herramienta.objects.get_or_create(
                codigo=h_info['codigo'],
                defaults=h_info
            )
            herramientas_creadas[tool.codigo] = tool
            if created:
                HistorialEstadoHerramienta.objects.create(
                    herramienta=tool,
                    estado_anterior='NUEVO',
                    estado_nuevo=tool.estado,
                    usuario=admin_user,
                    motivo="Carga inicial de inventario de equipos."
                )

        # 4. Contratistas
        self.stdout.write(self.style.NOTICE("==> Creando contratistas..."))
        c1, _ = Contratista.objects.get_or_create(
            rut_empresa='76.432.109-8',
            defaults={
                'razon_social': 'Constructora Andes del Sur SpA',
                'nombre_fantasia': 'Andes Sur Construcciones',
                'contacto_nombre': 'Carlos Valenzuela Ríos',
                'contacto_telefono': '+56 9 8765 4321',
                'contacto_email': 'cvalenzuela@andessur.cl',
                'direccion': 'Av. Los Conquistadores 1950, Providencia',
                'bloqueado': False
            }
        )

        c2, _ = Contratista.objects.get_or_create(
            rut_empresa='77.890.123-4',
            defaults={
                'razon_social': 'Subcontratos e Ingeniería Titan Ltda',
                'nombre_fantasia': 'Titan Obras',
                'contacto_nombre': 'Roberto Mateluna',
                'contacto_telefono': '+56 9 9123 4567',
                'contacto_email': 'rmateluna@titanobras.cl',
                'direccion': 'Camino Melipilla 8900, Maipú',
                'bloqueado': True,
                'motivo_bloqueo': 'Morosidad automática por atraso en devolución de herramientas arriendo ALQ-2026-0001',
                'fecha_bloqueo': timezone.now() - datetime.timedelta(days=3)
            }
        )

        # 5. Obras
        self.stdout.write(self.style.NOTICE("==> Creando obras y faenas..."))
        o1, _ = Obra.objects.get_or_create(
            codigo='OBR-001',
            defaults={
                'nombre': 'Edificio Vista Cordillera (Torre A)',
                'direccion': 'Av. Las Condes 12345',
                'comuna_ciudad': 'Las Condes, Santiago',
                'encargado_obra': 'Ing. Gonzalo Morales',
                'telefono_encargado': '+56 9 5555 1111',
                'contratista': c1,
                'activa': True
            }
        )

        o2, _ = Obra.objects.get_or_create(
            codigo='OBR-002',
            defaults={
                'nombre': 'Condominio Los Robles',
                'direccion': 'Camino El Alba 450',
                'comuna_ciudad': 'Chicureo, Colina',
                'encargado_obra': 'Patricio Fuentes',
                'telefono_encargado': '+56 9 4444 2222',
                'contratista': c2,
                'activa': True
            }
        )

        # 6. Alquileres de demostración
        self.stdout.write(self.style.NOTICE("==> Creando contratos de alquiler..."))

        # Alquiler Activo normal
        alq1, _ = AlquilerPrestamo.objects.get_or_create(
            codigo='ALQ-2026-0002',
            defaults={
                'contratista': c1,
                'obra': o1,
                'usuario_creador': admin_user,
                'fecha_inicio': hoy - datetime.timedelta(days=2),
                'fecha_fin_estimada': hoy + datetime.timedelta(days=5),
                'estado': 'ACTIVO',
                'costo_estimado': Decimal('224000'),
                'observaciones': 'Alquiler de cortadora para pavimento de estacionamientos subterráneos.'
            }
        )
        det1, _ = DetalleAlquiler.objects.get_or_create(
            alquiler=alq1,
            herramienta=herramientas_creadas['COR-004'],
            defaults={
                'tarifa_diaria_pactada': Decimal('32000'),
                'horas_iniciales': Decimal('60.0')
            }
        )

        # Alquiler Vencido en Mora (para demostrar Requerimiento 4 de Morosidad y Bloqueo)
        alq_vencido, _ = AlquilerPrestamo.objects.get_or_create(
            codigo='ALQ-2026-0001',
            defaults={
                'contratista': c2,
                'obra': o2,
                'usuario_creador': admin_user,
                'fecha_inicio': hoy - datetime.timedelta(days=10),
                'fecha_fin_estimada': hoy - datetime.timedelta(days=3), # Vencido hace 3 días
                'estado': 'VENCIDO',
                'costo_estimado': Decimal('168000'),
                'dias_retraso': 3,
                'recargo_mora': Decimal('108000'),
                'observaciones': 'Contrato vencido pendiente de restitución de herramientas.'
            }
        )

        # Generar alerta de morosidad
        AlertaMorosidad.objects.get_or_create(
            alquiler=alq_vencido,
            contratista=c2,
            defaults={
                'dias_vencido': 3,
                'monto_multa_calculada': Decimal('108000'),
                'bloqueo_aplicado': True,
                'resuelta': False
            }
        )

        # 7. Mantenimiento programado
        Mantenimiento.objects.get_or_create(
            herramienta=herramientas_creadas['MAN-005'],
            estado='PROGRAMADO',
            defaults={
                'tipo': 'PREVENTIVO',
                'fecha_programada': hoy + datetime.timedelta(days=2),
                'horas_uso_al_programar': Decimal('112.0'),
                'horas_limite': Decimal('120.0'),
                'tecnico_responsable': 'Taller Mecánico Central BuildCorp',
                'costo': Decimal('45000'),
                'descripcion_trabajo': 'Cambio de fuelles, aceite de pata y limpieza de carburador.',
                'repuestos_utilizados': 'Kit de sellos y aceite 10W-40'
            }
        )

        self.stdout.write(self.style.SUCCESS("✔ Datos de prueba creados exitosamente para BuildCorp."))

