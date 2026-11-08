# GUÍA DE PREPARACIÓN: PRUEBA DE SELECCIÓN MÚLTIPLE (40%)
## Asignatura: Desarrollo Backend | Docente: Marcelo Alvarado Aravena
### Evaluación Parcial N°3: Django, DRF, PostgreSQL y AWS Cloud

Esta guía contiene **20 preguntas tipo prueba con alternativas fundamentadas técnicamente** para preparar la evaluación escrita de 20 preguntas que representa el **40% de la nota final**.

---

### Pregunta 1: Arquitectura y Modelado ORM
**¿Cuál es la función principal de una migración en Django (`python manage.py makemigrations` y `migrate`)?**
* A) Compilar el código Python a lenguaje binario ejecutable.
* B) Traducir los cambios definidos en los modelos de Python a sentencias DDL de SQL relacional (CREATE TABLE, ALTER TABLE) y ejecutarlas en el motor de base de datos. *(CORRECTA)*
* C) Crear copias de seguridad de la base de datos en formato JSON.
* D) Reiniciar el servidor de desarrollo en el puerto 8000.
> **Fundamentación:** `makemigrations` detecta los cambios en los modelos de Python y genera archivos de migración (código declarativo), mientras que `migrate` ejecuta las sentencias SQL correspondientes en el motor configurado (PostgreSQL).

---

### Pregunta 2: Conexión a Base de Datos PostgreSQL
**¿Qué parámetro en `settings.py` define el adaptador oficial utilizado por Django para comunicarse con un motor PostgreSQL?**
* A) `'ENGINE': 'django.db.backends.mysql'`
* B) `'ENGINE': 'django.db.backends.postgresql'` *(CORRECTA)*
* C) `'ENGINE': 'django.db.backends.sqlite3'`
* D) `'ENGINE': 'django.db.backends.oracle'`
> **Fundamentación:** El backend oficial de Django para PostgreSQL es `django.db.backends.postgresql`, el cual interactúa a bajo nivel a través de las librerías `psycopg` o `psycopg2`.

---

### Pregunta 3: Django REST Framework (DRF)
**¿Qué componente de Django REST Framework se encarga de convertir objetos complejos de modelos ORM en tipos de datos nativos de Python para ser renderizados en formato JSON?**
* A) Router
* B) ViewSet
* C) Serializer *(CORRECTA)*
* D) Middleware
> **Fundamentación:** Los `Serializers` en DRF permiten que los datos de queryset e instancias de modelos se conviertan a representaciones serializadas (JSON/XML) y validan datos entrantes para deserializarlos.

---

### Pregunta 4: Despliegue en AWS EC2 y Servidores de Aplicación
**En una arquitectura de producción con Django en Linux (AWS EC2), ¿cuál es el rol de Gunicorn?**
* A) Servidor DNS que resuelve el dominio público de la instancia.
* B) Servidor de aplicaciones WSGI que interpreta el código Python y administra los procesos de trabajo (workers). *(CORRECTA)*
* C) Motor de base de datos relacional para almacenar las tablas.
* D) Firewall que abre los puertos 80 y 22 en AWS.
> **Fundamentación:** Gunicorn (Green Unicorn) es un servidor HTTP WSGI para UNIX que ejecuta la aplicación Django mediante múltiples workers y se comunica con Nginx a través de sockets o puertos locales.

---

### Pregunta 5: Servidor Web Inverso (Nginx)
**¿Por qué es una buena práctica utilizar Nginx como Reverse Proxy delante de Gunicorn en AWS EC2?**
* A) Porque Nginx gestiona de manera ultraeficiente las conexiones lentas, sirve directamente archivos estáticos y media, y redirige las peticiones dinámicas a Gunicorn. *(CORRECTA)*
* B) Porque Gunicorn no puede conectarse a internet sin Nginx.
* C) Porque Nginx reemplaza la necesidad de usar PostgreSQL.
* D) Porque Nginx genera las migraciones de base de datos automáticamente.
> **Fundamentación:** Nginx actúa como proxy inverso, absorbiendo la carga de buffering de clientes lentos, aplicando SSL/TLS y sirviendo archivos estáticos (`/static/` y `/media/`) sin consumir recursos del proceso de Django/Gunicorn.

---

### Pregunta 6: Seguridad en Redes AWS (Security Groups)
**Para que una aplicación web desplegada en una instancia EC2 sea accesible públicamente desde cualquier navegador web en internet, ¿qué regla de entrada (Inbound Rule) debe estar configurada en su Security Group?**
* A) Tipo: SSH, Puerto: 22, Origen: 0.0.0.0/0
* B) Tipo: HTTP, Puerto: 80, Origen: 0.0.0.0/0 *(CORRECTA)*
* C) Tipo: RDP, Puerto: 3389, Origen: 127.0.0.1/32
* D) Tipo: PostgreSQL, Puerto: 5432, Origen: 0.0.0.0/0
> **Fundamentación:** El protocolo HTTP opera sobre el puerto 80 por defecto. Para que cualquier usuario en internet pueda ver el sitio web en su navegador, el Security Group debe permitir tráfico TCP entrante en el puerto 80 desde `0.0.0.0/0`.

---

### Pregunta 7: Seguridad y Protección CSRF
**¿Cuál es el propósito del token `{% csrf_token %}` incluido en los formularios POST de las plantillas de Django?**
* A) Encriptar la contraseña del usuario en la base de datos con SHA-256.
* B) Prevenir ataques de falsificación de peticiones en sitios cruzados (Cross-Site Request Forgery) verificando que el formulario fue emitido por el propio servidor. *(CORRECTA)*
* C) Acelerar el tiempo de carga del formulario mediante compresión gzip.
* D) Guardar la sesión del usuario en memoria Redis.
> **Fundamentación:** El middleware CSRF de Django verifica que cada petición POST legítima contenga un token secreto único emitido para la sesión del usuario, impidiendo que sitios maliciosos envíen formularios a espaldas del usuario.

---

### Pregunta 8: Personalización de Django Admin
**En el archivo `admin.py`, ¿qué atributo permite definir las columnas visibles en la tabla principal de un modelo?**
* A) `search_fields`
* B) `list_filter`
* C) `list_display` *(CORRECTA)*
* D) `ordering`
> **Fundamentación:** `list_display` es una tupla o lista de nombres de campos o métodos que Django Admin renderiza como columnas en la vista de lista de registros.

---

### Pregunta 9: Acciones Masivas en Django Admin
**¿Cómo se define una acción personalizada que permita modificar múltiples registros seleccionados simultáneamente en el Django Admin?**
* A) Mediante el decorador `@admin.action` aplicado a una función que reciba `(self, request, queryset)`. *(CORRECTA)*
* B) Creando un archivo `actions.json` en la raíz del proyecto.
* C) Editando directamente el archivo `manage.py`.
* D) Configurando el parámetro `BATCH_ACTIONS = True` en `settings.py`.
> **Fundamentación:** En Django, las acciones masivas de administración se definen con métodos que reciben el `queryset` seleccionado y se decoran con `@admin.action(description="...")`.

---

### Pregunta 10: Relaciones Relacionales en el ORM
**Si eliminamos una categoría y no queremos que se eliminen las herramientas asociadas, sino impedir la eliminación para proteger la integridad referencial, ¿qué opción de `on_delete` debe usarse?**
* A) `models.CASCADE`
* B) `models.SET_NULL`
* C) `models.PROTECT` *(CORRECTA)*
* D) `models.DO_NOTHING`
> **Fundamentación:** `models.PROTECT` genera una excepción `ProtectedError` de Django, impidiendo que un registro padre sea eliminado si existen registros hijos vinculados mediante ForeignKey.

---

### Pregunta 11: Códigos de Estado HTTP en APIs REST
**Cuando un cliente envía datos inválidos a un endpoint de la API REST (por ejemplo, omitiendo un campo requerido o intentando alquilar con un contratista bloqueado), ¿qué código HTTP debe responder la API?**
* A) 200 OK
* B) 400 Bad Request *(CORRECTA)*
* C) 404 Not Found
* D) 500 Internal Server Error
> **Fundamentación:** El código HTTP 400 Bad Request indica que el servidor no puede procesar la petición debido a un error evidente del cliente (fallo de validación de formulario o payload JSON inválido).

---

### Pregunta 12: Códigos de Estado HTTP de Creación
**Cuando se crea exitosamente un nuevo recurso en la base de datos a través de una petición POST en Django REST Framework, ¿cuál es el código de respuesta estándar?**
* A) 200 OK
* B) 201 Created *(CORRECTA)*
* C) 204 No Content
* D) 301 Moved Permanently
> **Fundamentación:** El código HTTP 201 Created indica que la solicitud fue exitosa y condujo a la creación efectiva de un nuevo registro en el servidor.

---

### Pregunta 13: Variables de Entorno y Seguridad
**¿Por qué NUNCA se debe subir el archivo `.env` a un repositorio público como GitHub?**
* A) Porque el archivo `.env` pesa más de 100 MB y GitHub lo rechaza.
* B) Porque contiene credenciales sensibles como contraseñas de bases de datos, claves secretas (`SECRET_KEY`) y tokens de acceso. *(CORRECTA)*
* C) Porque rompe el compilador de Python en el servidor.
* D) Porque Django solo puede leer variables de entorno si se configuran en Linux.
> **Fundamentación:** El archivo `.env` contiene secretos que comprometerían la seguridad del sistema si se exponen públicamente. En su lugar, se incluye un archivo de plantilla como `.env.example`.

---

### Pregunta 14: Manejo de Archivos Estáticos en Producción
**¿Cuál es la función del comando `python manage.py collectstatic`?**
* A) Descargar librerías JavaScript desde internet.
* B) Recopilar todos los archivos estáticos (CSS, JS, imágenes) de todas las aplicaciones en un único directorio especificado en `STATIC_ROOT` para ser servidos por Nginx o WhiteNoise. *(CORRECTA)*
* C) Comprimir las tablas de PostgreSQL.
* D) Eliminar el historial de navegación de los usuarios.
> **Fundamentación:** `collectstatic` busca los archivos estáticos dispersos en las aplicaciones instaladas y los copia en la carpeta central `STATIC_ROOT` para que el servidor web los sirva eficientemente.

---

### Pregunta 15: Sistema de Administración de Servicios en Linux (Systemd)
**En una instancia EC2 con Ubuntu, ¿qué comando recarga y reinicia el servicio de Gunicorn tras actualizar el código fuente?**
* A) `sudo apt update && sudo apt upgrade`
* B) `sudo systemctl restart buildcorp` *(CORRECTA)*
* C) `python manage.py runserver`
* D) `git status`
> **Fundamentación:** `systemctl restart <nombre_servicio>` envía la señal para detener y volver a iniciar el proceso gestionado por systemd (Gunicorn).

---

### Pregunta 16: Campos de Fecha y Filtros en ORM
**Para consultar todos los alquileres cuya fecha de devolución pactada (`fecha_fin_estimada`) sea menor a la fecha actual (contratos vencidos), ¿cuál es la sintaxis correcta del ORM de Django?**
* A) `AlquilerPrestamo.objects.filter(fecha_fin_estimada=hoy)`
* B) `AlquilerPrestamo.objects.filter(fecha_fin_estimada__lt=hoy)` *(CORRECTA)*
* C) `AlquilerPrestamo.objects.filter(fecha_fin_estimada__gt=hoy)`
* D) `AlquilerPrestamo.objects.all().delete()`
> **Fundamentación:** El lookup `__lt` significa "Less Than" (menor que), filtrando fechas anteriores a la indicada. Por su parte, `__gt` significa "Greater Than" (mayor que).

---

### Pregunta 17: Autenticación y Restricción de Vistas Web
**¿Qué decorador de Django se utiliza en las vistas basadas en funciones para restringir el acceso únicamente a usuarios que hayan iniciado sesión?**
* A) `@admin.register`
* B) `@login_required` *(CORRECTA)*
* C) `@csrf_exempt`
* D) `@api_view`
> **Fundamentación:** `@login_required` intercepta la solicitud y verifica si `request.user.is_authenticated` es verdadero; si no lo es, redirige automáticamente al usuario a la página de login (`LOGIN_URL`).

---

### Pregunta 18: Renderizado Seguro de HTML en Django Admin
**Si en un método del `ModelAdmin` se desea retornar código HTML para mostrar un badge de color (por ejemplo, `<span style="...">Disponible</span>`), ¿qué función de Django debe envolver la cadena para evitar que Django escape las etiquetas?**
* A) `mark_safe` o `format_html` *(CORRECTA)*
* B) `json.dumps()`
* C) `str.strip()`
* D) `print()`
> **Fundamentación:** Django escapa por defecto cualquier cadena en el admin para prevenir ataques XSS. `format_html` permite generar fragmentos HTML válidos de manera segura contra inyecciones.

---

### Pregunta 19: Procesamiento de Imágenes en Base64
**Cuando una firma digital dibujada en un `<canvas>` HTML5 se envía al backend como `data:image/png;base64,iVBORw0...`, ¿cuál es el procedimiento para almacenarla en un `models.ImageField`?**
* A) Guardar el texto Base64 directamente en un CharField sin decodificar.
* B) Separar el encabezado, decodificar los datos con `base64.b64decode()` y envolverlos en un `ContentFile` de Django asignándole un nombre de archivo `.png`. *(CORRECTA)*
* C) Tomarle una captura de pantalla al monitor del servidor.
* D) No es posible almacenar firmas digitales en Django.
> **Fundamentación:** `ContentFile` convierte los bytes decodificados en un archivo en memoria que el sistema de almacenamiento de archivos de Django guarda en disco (`MEDIA_ROOT`).

---

### Pregunta 20: Relación OneToOne en el ORM de Django
**¿Por qué el modelo `RegistroEntrega` se vincula a `AlquilerPrestamo` mediante un campo `models.OneToOneField` en lugar de un `ForeignKey` tradicional?**
* A) Porque un contrato de arriendo solo puede tener un único despacho/entrega oficial físico con firma asociada, garantizando unicidad y evitando duplicidades. *(CORRECTA)*
* B) Porque OneToOneField consume menos memoria en PostgreSQL.
* C) Porque ForeignKey no permite almacenar firmas digitales.
* D) Porque Django obliga a usar OneToOneField en todas las relaciones.
> **Fundamentación:** `OneToOneField` implementa una relación 1 a 1 estricta con restricción de unicidad (`UNIQUE`), garantizando a nivel de base de datos que cada contrato tenga como máximo una sola entrega registrada.

