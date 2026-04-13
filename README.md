# Cannafy

Cannafy es un MVP web social con enfoque marketplace, construido con frontend estatico y backend Flask.

Hoy el proyecto ya incluye:

- registro para consumidores
- cuenta administradora con moderacion
- login con redireccion por rol
- perfiles editables y perfiles publicos entre usuarios
- catalogo de productos con detalle, carrito y contacto directo con dealer
- chat directo entre usuarios
- notificaciones con contador, panel y sonido generico
- zona social estilo feed ligero con publicaciones, respuestas y reacciones
- calificaciones para dealers
- formulario de reporte de bugs con imagen opcional

## Stack actual

- Backend: Flask
- Frontend: HTML, CSS y JavaScript vanilla
- Persistencia: [data.json](./data.json)
- Deploy: compatible con Render y Railway

## Como funciona hoy

El proyecto funciona como un MVP monolitico simple:

- [app.py](./app.py) sirve la API y tambien las paginas HTML
- el frontend consume la API usando `fetch`
- el almacenamiento se hace en [data.json](./data.json)
- las contrasenas se guardan con hash
- la sesion se maneja con tokens guardados en `sessions`

La informacion se guarda en estas colecciones dentro de `data.json`:

- `users`
- `products`
- `sessions`
- `conversations`
- `posts`
- `notifications`
- `bug_reports`

## Funcionalidades actuales

### Autenticacion y roles

- registro de consumidores
- login por correo y contrasena
- acceso por rol: admin, dealer y consumidor
- cierre de sesion
- cuenta admin sembrada automaticamente
- ban y unban de usuarios desde panel admin

### Perfiles

- edicion de apodo, bio y foto
- avatar con inicial automatica si no hay foto
- perfiles publicos de usuarios
- check verde para el administrador

### Productos

- dealers pueden publicar productos
- edicion de nombre, precio, descripcion y oferta
- eliminacion de productos
- detalle de producto
- boton directo para hablar con el dealer
- carrito local para compra directa por chat
- calificacion visible del dealer

### Chat y notificaciones

- conversaciones directas entre usuarios
- apertura automatica de chat desde producto o carrito
- envio con boton o con `Enter`
- actualizacion periodica sin recargar
- burbujas ajustadas al contenido
- panel de notificaciones
- contador de no leidos
- sonido generico cuando llegan mensajes

### Comunidad

- publicaciones en feed social
- respuestas a publicaciones
- reacciones: `Me gusta`, `Fuego`, `Idea`
- perfil publico accesible desde nombres y avatares

### Moderacion y soporte

- panel admin con gestion de usuarios
- listado de reportes de bugs
- formulario de reporte con texto e imagen opcional

## Archivos principales

- [app.py](./app.py): backend Flask, rutas API y logica principal
- [data.json](./data.json): persistencia local del MVP
- [index.html](./index.html): inicio de sesion
- [register.html](./register.html): registro consumidor
- [forgot-password.html](./forgot-password.html): cambio de contrasena
- [tienda.html](./tienda.html): catalogo publico y carrito
- [vendedor.html](./vendedor.html): panel dealer
- [chat.html](./chat.html): mensajes directos
- [social.html](./social.html): zona social
- [perfil.html](./perfil.html): edicion de perfil propio
- [usuario.html](./usuario.html): perfil publico
- [admin.html](./admin.html): panel administrador
- [reportes.html](./reportes.html): reporte de bugs
- [styles.css](./styles.css): estilos globales

## Ejecutar localmente

1. Activa el entorno virtual:
   `venv\Scripts\activate`
2. Inicia la aplicacion:
   `python app.py`
3. Abre en navegador:
   `http://127.0.0.1:5000/`

## Deploy

### Render

Configuracion recomendada:

- `Build Command`: `pip install -r requirements.txt`
- `Start Command`: `gunicorn app:app --bind 0.0.0.0:$PORT`
- `render.yaml` ya viene listo para crear de nuevo el servicio web

### Railway

Comando de inicio recomendado:

- `gunicorn app:app --bind 0.0.0.0:$PORT`

## Estado actual

El proyecto funciona como MVP bastante completo para pruebas reales, pero sigue teniendo limites tipicos de prototipo:

- usa JSON en vez de base de datos real
- no tiene tiempo real real, sino polling
- no tiene almacenamiento externo de imagenes
- no tiene tests amplios
- no esta separado aun en backend profesional + frontend SPA + app movil

## Proximos pasos recomendados

- migrar de `data.json` a PostgreSQL
- organizar el backend por modulos
- mover imagenes a un servicio externo
- usar WebSockets para chat y notificaciones en tiempo real
- mejorar pedidos, historial y reputacion
- preparar API estable para app movil
