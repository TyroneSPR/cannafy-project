# Cannafy

Cannafy es un MVP web social con enfoque marketplace, construido con frontend estático y backend Flask.

Hoy el proyecto ya incluye:

- registro para consumidores y dealers
- cuenta administradora con moderación
- login con redirección por rol
- perfiles editables y perfiles públicos entre usuarios
- catálogo de productos con detalle, carrito y contacto directo con dealer
- chat directo entre usuarios
- notificaciones con contador, panel y sonido genérico
- zona social estilo feed ligero con publicaciones, respuestas y reacciones
- calificaciones para dealers
- formulario de reporte de bugs con imagen opcional

## Stack actual

- Backend: Flask
- Frontend: HTML, CSS y JavaScript vanilla
- Persistencia: [data.json](./data.json)
- Deploy: compatible con Render y Railway

## Cómo funciona hoy

El proyecto funciona como un MVP monolítico simple:

- [app.py](./app.py) sirve la API y también las páginas HTML
- el frontend consume la API usando `fetch`
- el almacenamiento se hace en [data.json](./data.json)
- las contraseñas se guardan con hash
- la sesión se maneja con tokens guardados en `sessions`

La información se guarda en estas colecciones dentro de `data.json`:

- `users`
- `products`
- `sessions`
- `conversations`
- `posts`
- `notifications`
- `bug_reports`

## Funcionalidades actuales

### Autenticación y roles

- registro de consumidores y dealers
- login por correo y contraseña
- acceso por rol:
  - admin
  - dealer
  - consumidor
- cierre de sesión
- cuenta admin sembrada automáticamente
- ban y unban de usuarios desde panel admin

### Perfiles

- edición de apodo, bio y foto
- avatar con inicial automática si no hay foto
- perfiles públicos de usuarios
- check verde para el administrador

### Productos

- dealers pueden publicar productos
- edición de nombre, precio, descripción y oferta
- eliminación de productos
- detalle de producto
- botón directo para hablar con el dealer
- carrito local para compra directa por chat
- calificación visible del dealer

### Chat y notificaciones

- conversaciones directas entre usuarios
- apertura automática de chat desde producto o carrito
- envío con botón o con `Enter`
- actualización periódica sin recargar
- burbujas ajustadas al contenido
- panel de notificaciones
- contador de no leídos
- sonido genérico cuando llegan mensajes

### Comunidad

- publicaciones en feed social
- respuestas a publicaciones
- reacciones:
  - `Me gusta`
  - `Fuego`
  - `Idea`
- perfil público accesible desde nombres y avatares

### Moderación y soporte

- panel admin con gestión de usuarios
- listado de reportes de bugs
- formulario de reporte con texto e imagen opcional

## Archivos principales

- [app.py](./app.py): backend Flask, rutas API y lógica principal
- [data.json](./data.json): persistencia local del MVP
- [index.html](./index.html): entrada y términos
- [rol.html](./rol.html): elección de rol
- [comprador.html](./comprador.html): registro consumidor
- [dealer-register.html](./dealer-register.html): registro dealer
- [login.html](./login.html): inicio de sesión
- [tienda.html](./tienda.html): catálogo público y carrito
- [vendedor.html](./vendedor.html): panel dealer
- [chat.html](./chat.html): mensajes directos
- [social.html](./social.html): zona social
- [perfil.html](./perfil.html): edición de perfil propio
- [usuario.html](./usuario.html): perfil público
- [admin.html](./admin.html): panel administrador
- [reportes.html](./reportes.html): reporte de bugs
- [styles.css](./styles.css): estilos globales

## Ejecutar localmente

1. Activa el entorno virtual:
   `venv\Scripts\activate`
2. Inicia la aplicación:
   `python app.py`
3. Abre en navegador:
   `http://127.0.0.1:5000/`

## Deploy

### Render

Configuración recomendada:

- `Build Command`: `pip install -r requirements.txt`
- `Start Command`: `gunicorn app:app --bind 0.0.0.0:$PORT`

### Railway

Comando de inicio recomendado:

- `gunicorn app:app --bind 0.0.0.0:$PORT`

## Estado actual

El proyecto ya funciona como MVP bastante completo para pruebas reales, pero sigue teniendo límites típicos de prototipo:

- usa JSON en vez de base de datos real
- no tiene tiempo real real, sino polling
- no tiene almacenamiento externo de imágenes
- no tiene tests amplios
- no está separado aún en backend profesional + frontend SPA + app móvil

## Próximos pasos recomendados

- migrar de `data.json` a PostgreSQL
- organizar el backend por módulos
- mover imágenes a un servicio externo
- usar WebSockets para chat y notificaciones en tiempo real
- mejorar pedidos, historial y reputación
- preparar API estable para app móvil

## Nota

Si vas a escalar este proyecto hacia una app móvil o una versión profesional, el siguiente salto natural es:

1. base de datos real
2. API más estructurada
3. almacenamiento externo
4. tiempo real real
5. app móvil consumiendo el mismo backend
