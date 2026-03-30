# Cannafy

MVP web con frontend estático y backend Flask para:

- aceptar términos
- registrar consumidores y dealers
- iniciar sesión
- publicar productos como dealer
- ver la tienda pública como consumidor

## Ejecutar

1. Activa el entorno virtual:
   `venv\Scripts\activate`
2. Inicia la API:
   `python app.py`
3. Abre `index.html` en el navegador.

La API corre en `http://127.0.0.1:5000`.

## Publicarlo en internet

La forma más simple es desplegar este repo en un servicio como Render o Railway.

### Render

1. Entra a Render y conecta tu repositorio de GitHub.
2. Crea un `Web Service`.
3. Usa:
   `Build Command`: `pip install -r requirements.txt`
   `Start Command`: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Al terminar, Render te dará una URL pública.

### Railway

1. Conecta tu repo de GitHub en Railway.
2. Crea un proyecto nuevo desde el repositorio.
3. Si te lo pide, usa como comando de inicio:
   `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Genera el dominio público desde la sección de networking.

## Importante sobre aparecer en Google

Tener una URL pública no significa aparecer de inmediato en búsquedas.
Para eso normalmente necesitas:

- una web pública estable
- tiempo para indexación
- opcionalmente un dominio propio
- registrar el sitio en Google Search Console

## Archivos clave

- `app.py`: API Flask y lógica de autenticación/productos
- `data.json`: almacenamiento local del MVP
- `index.html`: entrada y aceptación de términos
- `rol.html`: selección de tipo de usuario
- `comprador.html`: registro consumidor
- `dealer-register.html`: registro dealer
- `login.html`: login compartido
- `vendedor.html`: panel dealer
- `tienda.html`: catálogo público

## Nota

Este proyecto ya funciona como MVP, pero aún conviene migrar más adelante a:

- base de datos real
- autenticación más robusta
- backend sirviendo el frontend
- validaciones y tests más completos
