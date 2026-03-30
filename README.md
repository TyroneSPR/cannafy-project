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
