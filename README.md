# EVALUACIÓN PARCIAL N°3: DESARROLLO BACKEND
## BuildCorp - Sistema de Alquiler y Control de Herramientas

* **Docente:** Marcelo Alvarado Aravena
* **Asignatura:** Desarrollo Backend - Inacap
* **Ponderación:** 30% de la nota final
* **Caso Asignado:** BuildCorp (Sistema de Alquiler y Control de Herramientas)

---

## 🌐 Enlace de Despliegue en AWS Cloud (EC2)

> ### **URL Pública de la Aplicación en AWS EC2:**
> 🔗 **`http://54.80.92.55/`**
>
> **Panel Django Admin:**
> 🔗 **`http://54.80.92.55/admin/`**
>
> **API REST Navegable (DRF):**
> 🔗 **`http://54.80.92.55/api/`**

### 🔑 Credenciales de Acceso para Evaluación y Defensa:
* **Superusuario / Administrador:**
  * Usuario: `admin`
  * Contraseña: `Admin123!`
* **Operador de Bodega:**
  * Usuario: `bodeguero`
  * Contraseña: `Bodega123!`

---

## 🏗️ 1. Descripción del Proyecto y Problemática Resuelta

BuildCorp es una solución integral desarrollada sobre **Django** y **Django REST Framework (DRF)** conectada a una base de datos relacional **PostgreSQL**, diseñada para eliminar las principales fuentes de ineficiencia y pérdidas financieras en obras de construcción:

1. **Pérdida de maquinaria ligera y herramientas:** Control estricto de inventario por código interno, número de serie, horómetro de uso acumulado y ubicación en bodega o faena.
2. **Cobros inexactos a subcontratistas:** Liquidación automatizada según días de arriendo pactados, recargos automáticos por morosidad (50% adicional por día de mora) y cobros por reparación de daños técnicos.
3. **Fallas imprevistas en obras:** Sistema de mantenimiento preventivo basado en umbrales de horas de servicio y fechas límite de calibración que inhabilita automáticamente equipos en riesgo de avería.
4. **Falta de respaldo en despachos y recepciones:** Módulo interactivo de firma digital estampada en terreno por el responsable de obra.

---

## 🎯 2. Cobertura de Requerimientos del Caso

| Requerimiento del Caso | Implementación Técnica en BuildCorp | Ubicación en el Código |
| :--- | :--- | :--- |
| **1. Catálogo de Activos con Trazabilidad de Estado** | Estados: `Disponible`, `En Uso`, `En Mantenimiento`, `Dado de Baja`. Cada cambio de estado genera un registro inmutable de auditoría con usuario, fecha y justificación. | `gestion.models.Herramienta`, `gestion.models.HistorialEstadoHerramienta` |
| **2. Entrega y Devolución con Firma Digital** | Interfaz con Canvas HTML5 para firmar con mouse o pantalla táctil en terreno. La firma se procesa en Base64 y se almacena físicamente como PNG en `media/firmas/`. | `gestion.models.RegistroEntrega`, `gestion.models.RegistroDevolucion`, `static/js/signature.js` |
| **3. Programación de Mantenimientos Preventivos** | Detección automática al superar el umbral de horas de uso o fecha límite. Al completar la mantención, se recalcula el próximo ciclo y la herramienta vuelve a estar Disponible. | `gestion.models.Mantenimiento`, `Herramienta.requiere_mantenimiento_preventivo` |
| **4. Alertas de Morosidad y Bloqueo Automático** | Al expirar la fecha de devolución, el arriendo pasa a `VENCIDO`, se calcula la multa y el contratista queda automáticamente `BLOQUEADO`, impidiendo nuevos alquileres. | `AlquilerPrestamo.verificar_morosidad()`, `gestion.models.AlertaMorosidad` |

---

## 🛠️ 3. Arquitectura y Stack Tecnológico

* **Backend:** Python 3.12+ / Django 6.1 / Django REST Framework 3.18
* **Base de Datos Relacional:** PostgreSQL 15 / 16 (con soporte fallback a SQLite para entornos de desarrollo desconectados)
* **Frontend:** Django Templates + Bootstrap 5.3 + FontAwesome 6 + HTML5 Canvas Signature Pad
* **Servidor Web y WSGI:** Gunicorn 26 + Nginx (Reverse Proxy) + Systemd
* **Archivos Estáticos:** WhiteNoise 6.12 (optimización de assets y caché)
* **Infraestructura Cloud:** Instancia única AWS EC2 (Ubuntu 22.04 LTS / AWS Academy)

---

## 🚀 4. Guía de Ejecución en Entorno Local

### Prerrequisitos:
* Python 3.10 o superior instalado.
* Git instalado.

### Pasos de Instalación:
```bash
# 1. Clonar el repositorio
git clone https://github.com/Nofun205/EVA3BACK.git
cd EVA3BACK

# 2. Crear y activar el entorno virtual
python -m venv venv

# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# En Linux/macOS:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
# Copiar archivo de ejemplo
cp .env.example .env

# 5. Aplicar migraciones relacionales a la base de datos
python manage.py makemigrations
python manage.py migrate

# 6. Recopilar archivos estáticos
python manage.py collectstatic --noinput

# 7. Cargar datos iniciales de prueba (usuarios, herramientas, contratistas y alertas)
python manage.py seed_data

# 8. Ejecutar pruebas unitarias automatizadas
python manage.py test

# 9. Iniciar el servidor de desarrollo
python manage.py runserver 0.0.0.0:8000
```
Abrir el navegador web en: `http://localhost:8000/`

---

## ☁️ 5. Guía de Despliegue en AWS EC2 (Paso a Paso)

### Paso 1: Lanzar Instancia en AWS Academy
1. Iniciar sesión en la consola de **AWS Academy Learner Lab**.
2. Ir al servicio **EC2** y pulsar **Launch Instance**.
3. Configuración recomendada:
   * **Nombre:** `BuildCorp-Backend-EC2`
   * **AMI:** `Ubuntu Server 22.04 LTS (HVM), SSD Volume Type` (64-bit x86).
   * **Tipo de Instancia:** `t2.micro` o `t3.micro` (Apto para capa gratuita / Academy).
   * **Key Pair:** Seleccionar su par de llaves `.pem` para conexión SSH.
4. **Network Settings (Security Group) - CRÍTICO:**
   * Crear o asignar un Security Group con las siguientes reglas de entrada (**Inbound Rules**):
     * **SSH (Puerto 22):** Origen `0.0.0.0/0` (o su IP).
     * **HTTP (Puerto 80):** Origen `0.0.0.0/0` (Acceso público web).
     * **Custom TCP (Puerto 8000):** Origen `0.0.0.0/0` (Pruebas directas con Gunicorn/Django).
5. Lanzar la instancia y copiar la **IP Pública IPv4**.

---

### Paso 2: Conexión SSH y Despliegue Automatizado
Conéctese mediante su terminal a la instancia EC2:
```bash
ssh -i "su-llave.pem" ubuntu@54.80.92.55
```

Una vez dentro de la máquina virtual Ubuntu, ejecute:
```bash
# 1. Clonar el repositorio
git clone https://github.com/Nofun205/EVA3BACK.git EVA3BACK
cd EVA3BACK

# 2. Dar permisos de ejecución al script de aprovisionamiento
chmod +x deploy/deploy_ec2.sh

# 3. Ejecutar el despliegue automático
./deploy/deploy_ec2.sh
```

El script `deploy_ec2.sh` realizará de forma 100% desatendida:
* Actualización de paquetes del sistema.
* Instalación y configuración del servidor **PostgreSQL** (creación de base de datos `buildcorp_db` y usuario `buildcorp_user`).
* Creación de entorno virtual Python e instalación de librerías.
* Ejecución de migraciones y carga de datos iniciales (`seed_data`).
* Configuración del servicio **Gunicorn** administrado por **Systemd** (`buildcorp.service`).
* Configuración del proxy inverso **Nginx** en el puerto 80 sirviendo estáticos y media.

---

## 📡 6. Catálogo de Endpoints de la API REST (DRF)

La aplicación expone una API REST moderna para integración con frontend móvil o sistemas externos:

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/herramientas/` | Listado completo de herramientas y estados. |
| `GET` | `/api/herramientas/disponibles/` | Herramientas listas para ser alquiladas. |
| `GET` | `/api/herramientas/requieren_mantenimiento/` | Herramientas en umbral de mantención preventiva. |
| `POST` | `/api/herramientas/{id}/cambiar_estado/` | Cambia estado dejando trazabilidad de auditoría. |
| `GET / POST` | `/api/contratistas/` | CRUD de contratistas y obras. |
| `POST` | `/api/contratistas/{id}/bloquear/` | Bloqueo administrativo de un contratista. |
| `POST` | `/api/contratistas/{id}/desbloquear/` | Desbloqueo y regularización comercial. |
| `GET / POST` | `/api/alquileres/` | Listado y registro de contratos de arriendo. |
| `POST` | `/api/alquileres/verificar_morosidades/` | Ejecuta chequeo global de vencimientos y sanciones. |
| `POST` | `/api/alquileres/{id}/registrar_entrega/` | Despacho de herramientas con firma digital Base64. |
| `POST` | `/api/alquileres/{id}/registrar_devolucion/` | Devolución con horómetro, cobro de daños y firma digital. |
| `GET / POST` | `/api/mantenimientos/` | Registro y programación de mantenciones. |
| `POST` | `/api/mantenimientos/{id}/completar/` | Finaliza mantención y reprograma próximo ciclo. |
| `GET / POST` | `/api/alertas/` | Alertas de morosidad y sanciones activas. |

---

## 🎓 7. Guía de Defensa Práctica ante el Docente

Durante la evaluación práctica en vivo con el docente **Marcelo Alvarado Aravena**, siga esta secuencia estructurada para demostrar dominio total:

### 1. Demostración en la IP Pública de AWS EC2:
* Ingrese a `http://54.80.92.55/` desde el navegador.
* Inicie sesión con el superusuario `admin` / `Admin123!`.
* **Dashboard:** Muestre las métricas en tiempo real (herramientas disponibles, en uso, contratistas bloqueados y alertas activas).

### 2. Flujo del Requerimiento 1 (Catálogo y Trazabilidad):
* Vaya a **Herramientas**. Ingrese al detalle de una herramienta (ej: `GEN-001` o `COM-003`).
* Muestre la pestaña **"Trazabilidad de Estados (Auditoría)"** donde se observa el historial inmutable de cada cambio de estado, el usuario responsable y el motivo.
* Cambie el estado mediante el botón "Cambiar Estado" y verifique cómo se inserta la nueva fila de auditoría.

### 3. Flujo del Requerimiento 2 (Entrega y Devolución con Firma Digital):
* Vaya a **Alquileres** y abra un contrato solicitado (o cree uno nuevo en "+ Nuevo Alquiler").
* Presione **"Despachar y Firmar Entrega"**.
* Dibuje la firma con el mouse/touch en el recuadro Canvas interactivo. Confirme la entrega y muestre cómo el estado del contrato pasa a `ACTIVO`, las herramientas pasan a `EN_USO` y la firma queda almacenada como imagen PNG.
* Presione **"Recibir y Firmar Devolución"**.
* Ingrese el horómetro final, el estado físico y estampe la firma digital de conformidad. Al finalizar, muestre la liquidación de costo y la reactivación de herramientas.

### 4. Flujo del Requerimiento 3 (Mantenimientos Preventivos):
* Muestre en la sección **Mantenimiento** la alerta amarilla de herramientas que superaron su umbral de horas de uso (ej: `COM-003`).
* Presione "Programar Ahora" y complete el formulario.
* Muestre cómo la herramienta pasa automáticamente a estado `MANTENIMIENTO`.
* Finalice el servicio con el botón "Finalizar", ingrese los repuestos y demuestre cómo el equipo vuelve a quedar `DISPONIBLE` y con su próximo mantenimiento reprogramado a 90 días.

### 5. Flujo del Requerimiento 4 (Morosidad y Bloqueo Automático):
* Presione en la barra superior el botón **"Chequear Morosidad"** (o en la sección Alertas).
* El sistema identificará el contrato `ALQ-2026-0001` vencido, calculará los días de retraso, la multa y **bloqueará inmediatamente al contratista** `Subcontratos e Ingeniería Titan Ltda`.
* Intente crear un nuevo alquiler para este contratista: demuestre que el sistema rechaza la operación informando que el contratista se encuentra bloqueado.
* Regularice la alerta y compruebe cómo se desbloquea al contratista.

### 6. Demostración en Django Admin:
* Acceda a `http://54.80.92.55/admin/`.
* Muestre la personalización visual con badges de colores para cada estado (`DISPONIBLE`, `EN_USO`, `MANTENIMIENTO`, `BLOQUEADO`), los filtros laterales, búsquedas y las acciones masivas personalizadas (`@admin.action`).

