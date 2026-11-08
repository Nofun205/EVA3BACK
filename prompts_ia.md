# Registro de Consultas y Apoyo de Inteligencia Artificial (prompts_ia.md)

**Asignatura:** Desarrollo Backend  
**Evaluación:** Evaluación Parcial N°3 (Ponderación 30%)  
**Docente:** Marcelo Alvarado Aravena  
**Proyecto Asignado:** Sistema de Alquiler y Control de Herramientas (**BuildCorp**)  
**Estudiante:** Evaluación Práctica Individual  

---

## 1. Introducción y Metodología de Uso de IA

En conformidad con las bases de la Evaluación Parcial N°3, se utilizó inteligencia artificial como herramienta de asistencia técnica, optimización arquitectónica y buenas prácticas de ingeniería de software. Las directrices principales fueron:

1. **Modelado Relacional Óptimo:** Diseñar esquemas relacionales normalizados para PostgreSQL que cumplieran con integridad referencial, trazabilidad de estados y auditoría.
2. **Personalización Avanzada de Django Admin:** Cumplir con la máxima ponderación de la rúbrica (Criterio 2) implementando filtros, búsquedas, acciones administrativas masivas y badges visuales formateados con HTML seguro (`format_html`).
3. **Módulo de Firma Digital:** Diseñar una solución ligera, responsiva y funcional en terreno utilizando Canvas HTML5 que enviara la firma en base64 para persistirse como imagen física PNG en el backend.
4. **Lógica de Negocio y Automatización:** Codificar algoritmos eficientes para la detección de morosidad, recargos y bloqueo automático de contratistas.
5. **Arquitectura y Despliegue en la Nube (AWS EC2):** Automatizar el aprovisionamiento de un servidor Ubuntu con PostgreSQL, Gunicorn y Nginx.

---

## 2. Registro Cronológico de Prompts y Orientaciones Técnicas

### Prompt 1: Arquitectura de Datos y Modelado de Dominio en Django / PostgreSQL
* **Consulta / Prompt:**
  > "Actúa como un arquitecto de software backend senior en Python/Django. Necesito diseñar los modelos del ORM para el 'Sistema de Alquiler y Control de Herramientas (BuildCorp)'. El sistema debe resolver la pérdida de maquinaria ligera, cobros inexactos y fallas imprevistas. Requiero:
  > 1. Catálogo de activos y herramientas con trazabilidad de estado (Disponible, En Uso, Mantenimiento, Dado de Baja) y modelo de auditoría histórica para cada cambio de estado.
  > 2. Modelo de contratistas y obras con soporte de bloqueo preventivo por morosidad.
  > 3. Modelo de alquileres con cálculo automático de tarifas, días de duración y costos.
  > 4. Registro de entregas y devoluciones con almacenamiento de firma digital en imagen.
  > 5. Programación de mantenimientos preventivos y correctivos basados en horómetros y fechas límite.
  > 6. Sistema de alertas por morosidad.
  > Todo debe ser compatible con PostgreSQL y Django REST Framework."
* **Respuesta y Decisión Técnica de la IA:**
  - Sugirió crear 11 modelos relacionales bien delimitados (`CategoriaHerramienta`, `Herramienta`, `HistorialEstadoHerramienta`, `Contratista`, `Obra`, `AlquilerPrestamo`, `DetalleAlquiler`, `RegistroEntrega`, `RegistroDevolucion`, `Mantenimiento`, `AlertaMorosidad`).
  - Implementó el método `cambiar_estado()` en `Herramienta` que automáticamente inserta un registro inmutable en `HistorialEstadoHerramienta` con usuario y motivo.
  - Implementó el método `verificar_morosidad()` en `AlquilerPrestamo` para automatizar la penalización y bloqueo.

---

### Prompt 2: Personalización Visual y Funcional de Django Admin
* **Consulta / Prompt:**
  > "Para la rúbrica de evaluación (Criterio 2: 20 puntos), necesito personalizar completamente el panel de Django Admin. Todos los modelos deben registrarse con `list_display`, `list_filter`, `search_fields` y campos visuales HTML estilizados con badges de colores para los estados (Disponible en verde, En Uso en azul, Mantenimiento en amarillo, Dado de Baja en rojo; Bloqueado en rojo; etc.). También requiero acciones administrativas (`@admin.action`) para bloquear/desbloquear contratistas en lote, cambiar estados y regularizar alertas, además de inlines para herramientas alquiladas y plantillas personalizadas con branding corporativo."
* **Respuesta y Decisión Técnica de la IA:**
  - Se estructuró `gestion/admin.py` utilizando `format_html` para renderizar etiquetas con estilos CSS en línea accesibles y legibles.
  - Se añadieron `TabularInline` para `DetalleAlquilerInline` y `HistorialEstadoHerramientaInline`.
  - Se diseñó `templates/admin/base_site.html` modificando el branding superior a `BUILDCORP | Sistema de Alquiler y Control de Herramientas` con colores corporativos oscuros y amarillos de faena.

---

### Prompt 3: Implementación del Módulo de Firma Digital en Terreno
* **Consulta / Prompt:**
  > "Explícame cómo implementar un módulo de firma digital para la entrega y devolución de herramientas en obra. El encargado debe firmar con el dedo en una pantalla táctil o con el mouse. ¿Cómo capturar el trazo en JavaScript con HTML5 Canvas, convertirlo a base64, enviarlo en un formulario Django estándar y convertirlo en el servidor a un `ContentFile` de Django para guardarlo en un `models.ImageField` como archivo PNG?"
* **Respuesta y Decisión Técnica de la IA:**
  - Se diseñó el script `static/js/signature.js` con soporte para eventos `mousedown/mousemove/mouseup` y eventos táctiles `touchstart/touchmove/touchend` con ajuste de escala para pantallas Retina (`devicePixelRatio`).
  - Se codificó la función auxiliar `procesar_firma_base64()` en Python (`views.py` y `api_views.py`), decodificando la cadena Base64 y guardándola como imagen PNG con un nombre único generado vía UUID.

---

### Prompt 4: Lógica de Detección de Morosidad y Bloqueo de Contratistas
* **Consulta / Prompt:**
  > "Requiero codificar una regla de negocio estricta: si un alquiler supera la fecha de devolución pactada y aún no se han devuelto las herramientas, el sistema debe cambiar el estado a 'VENCIDO', calcular los días de retraso, generar un recargo del 50% extra por día, bloquear al contratista (`bloqueado=True`) y levantar una `AlertaMorosidad`. Además, al intentar crear un nuevo alquiler, si el contratista está bloqueado, el formulario y la API REST deben rechazar la transacción con un mensaje claro."
* **Respuesta y Decisión Técnica de la IA:**
  - Se implementó la validación en `clean()` del modelo `AlquilerPrestamo`, en `clean_contratista()` de `AlquilerPrestamoForm`, y en el serializer `AlquilerPrestamoSerializer.validate()`.
  - Se añadió la vista y acción global `verificar_morosidad_global` que puede ser ejecutada tanto desde un botón en el Dashboard, desde Django Admin en lote, o programada vía tarea cron.

---

### Prompt 5: Despliegue Automatizado en AWS EC2 (Gunicorn, Nginx y PostgreSQL)
* **Consulta / Prompt:**
  > "Genera un script bash (`deploy_ec2.sh`) reproducible y robusto para desplegar esta aplicación Django en una instancia EC2 de AWS Academy (Ubuntu 22.04 LTS). Debe instalar automáticamente PostgreSQL, crear la base de datos `buildcorp_db` y el usuario, configurar el entorno virtual, aplicar migraciones, ejecutar `collectstatic`, poblar los datos con `seed_data`, configurar un servicio systemd para Gunicorn y configurar Nginx como proxy inverso en el puerto 80 sirviendo estáticos y media."
* **Respuesta y Decisión Técnica de la IA:**
  - Creación del script `deploy/deploy_ec2.sh` totalmente automatizado e idempotente.
  - Creación de archivos de configuración complementarios `deploy/nginx_buildcorp.conf` y `deploy/buildcorp.service`.
  - Inclusión de `Dockerfile` y `docker-compose.yml` para alternativas de ejecución mediante contenedores.

---

## 3. Conclusión y Valor Agregado del Apoyo de IA

El uso guiado de herramientas de Inteligencia Artificial permitió acelerar los procesos mecánicos de maquetación HTML/CSS y configuración de servidores, permitiendo centrar el 100% del esfuerzo en la integridad relacional de la base de datos PostgreSQL, la seguridad en el manejo de sesiones y el cumplimiento exhaustivo de las 4 reglas clave de negocio exigidas en la rúbrica de evaluación.
