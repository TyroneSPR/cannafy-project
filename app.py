from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"
DEFAULT_ADMIN_EMAIL = "tyronegonzalesg4@gmail.com"
DEFAULT_ADMIN_PASSWORD = "Macnanime26."
DEFAULT_ADMIN_NAME = "Tyrone"
ALLOWED_STATIC_FILES = {
    "index.html",
    "rol.html",
    "comprador.html",
    "login.html",
    "dealer-login.html",
    "dealer-register.html",
    "vendedor.html",
    "tienda.html",
    "chat.html",
    "social.html",
    "perfil.html",
    "admin.html",
    "acerca.html",
    "styles.css",
    "terms-background.jpg",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_store() -> None:
    if DATA_FILE.exists():
        return

    DATA_FILE.write_text(
        json.dumps(
            {
                "users": [],
                "products": [],
                "sessions": [],
                "conversations": [],
                "posts": [],
                "notifications": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def ensure_default_admin(store: dict[str, Any]) -> bool:
    existing_admin = next(
        (user for user in store["users"] if user["correo"] == DEFAULT_ADMIN_EMAIL),
        None,
    )
    if existing_admin:
        changed = False
        if existing_admin.get("role") != "admin":
            existing_admin["role"] = "admin"
            changed = True
        if existing_admin.get("apodo") != "ADM":
            existing_admin["apodo"] = "ADM"
            changed = True
        if "banned" not in existing_admin:
            existing_admin["banned"] = False
            changed = True
        return changed

    store["users"].append(
        {
            "id": next_id(store["users"]),
            "role": "admin",
            "nombre": DEFAULT_ADMIN_NAME,
            "apodo": "ADM",
            "bio": "Administrador principal de Cannafy.",
            "foto_perfil": "",
            "correo": DEFAULT_ADMIN_EMAIL,
            "telefono": "",
            "edad": None,
            "documento": "",
            "password_hash": generate_password_hash(DEFAULT_ADMIN_PASSWORD),
            "accepted_terms": True,
            "banned": False,
            "created_at": utc_now(),
        }
    )
    return True


def read_store() -> dict[str, Any]:
    ensure_store()
    store = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    store.setdefault("users", [])
    store.setdefault("products", [])
    store.setdefault("sessions", [])
    store.setdefault("conversations", [])
    store.setdefault("posts", [])
    store.setdefault("notifications", [])
    if ensure_default_admin(store):
        write_store(store)
    return store


def write_store(store: dict[str, Any]) -> None:
    DATA_FILE.write_text(json.dumps(store, indent=2), encoding="utf-8")


def next_id(items: list[dict[str, Any]]) -> int:
    return max((item["id"] for item in items), default=0) + 1


def sanitize_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "role": user["role"],
        "nombre": user["nombre"],
        "apodo": user.get("apodo", user["nombre"]),
        "bio": user.get("bio", ""),
        "foto_perfil": user.get("foto_perfil", ""),
        "correo": user["correo"],
        "telefono": user.get("telefono"),
        "edad": user.get("edad"),
        "documento": user.get("documento"),
        "banned": bool(user.get("banned", False)),
        "created_at": user["created_at"],
    }


def sanitize_message(message: dict[str, Any], store: dict[str, Any]) -> dict[str, Any]:
    sender = next((user for user in store["users"] if user["id"] == message["sender_id"]), None)
    return {
        "id": message["id"],
        "conversation_id": message["conversation_id"],
        "sender_id": message["sender_id"],
        "sender_nombre": sender.get("apodo", sender["nombre"]) if sender else "Usuario",
        "sender_foto": sender.get("foto_perfil", "") if sender else "",
        "content": message["content"],
        "created_at": message["created_at"],
    }


def sanitize_conversation(
    conversation: dict[str, Any], current_user_id: int, store: dict[str, Any]
) -> dict[str, Any]:
    other_id = next(
        participant_id
        for participant_id in conversation["participant_ids"]
        if participant_id != current_user_id
    )
    other_user = next((user for user in store["users"] if user["id"] == other_id), None)
    messages = conversation.get("messages", [])
    last_message = messages[-1] if messages else None
    return {
        "id": conversation["id"],
        "other_user": sanitize_user(other_user) if other_user else None,
        "updated_at": conversation["updated_at"],
        "last_message": sanitize_message(last_message, store) if last_message else None,
        "unread_count": sum(
            1
            for notification in store.get("notifications", [])
            if notification.get("user_id") == current_user_id
            and notification.get("type") == "message"
            and notification.get("conversation_id") == conversation["id"]
            and not notification.get("read", False)
        ),
    }


def sanitize_post(post: dict[str, Any], store: dict[str, Any]) -> dict[str, Any]:
    author = next((user for user in store["users"] if user["id"] == post["author_id"]), None)
    comments = []
    for comment in post.get("comments", []):
        comment_author = next(
            (user for user in store["users"] if user["id"] == comment["author_id"]), None
        )
        comments.append(
            {
                "id": comment["id"],
                "author_id": comment["author_id"],
                "author_nombre": comment_author.get("apodo", comment_author["nombre"])
                if comment_author
                else "Usuario",
                "author_foto": comment_author.get("foto_perfil", "") if comment_author else "",
                "content": comment["content"],
                "created_at": comment["created_at"],
            }
        )

    return {
        "id": post["id"],
        "author_id": post["author_id"],
        "author_nombre": author.get("apodo", author["nombre"]) if author else "Usuario",
        "author_role": author["role"] if author else None,
        "author_foto": author.get("foto_perfil", "") if author else "",
        "content": post["content"],
        "created_at": post["created_at"],
        "comments": comments,
    }


def sanitize_product(product: dict[str, Any]) -> dict[str, Any]:
    oferta_activa = bool(product.get("oferta_activa"))
    precio_oferta = str(product.get("precio_oferta", "")).strip()
    return {
        "id": product["id"],
        "dealer_id": product["dealer_id"],
        "dealer_nombre": product["dealer_nombre"],
        "dealer_foto": product.get("dealer_foto", ""),
        "nombre": product["nombre"],
        "precio": product["precio"],
        "oferta_activa": oferta_activa,
        "precio_oferta": precio_oferta,
        "precio_mostrar": precio_oferta if oferta_activa and precio_oferta else product["precio"],
        "imagen": product["imagen"],
        "descripcion": product["descripcion"],
        "created_at": product["created_at"],
    }


def sanitize_notification(notification: dict[str, Any], store: dict[str, Any]) -> dict[str, Any]:
    actor = next((user for user in store["users"] if user["id"] == notification["actor_id"]), None)
    return {
        "id": notification["id"],
        "type": notification["type"],
        "user_id": notification["user_id"],
        "actor_id": notification["actor_id"],
        "actor_nombre": actor.get("apodo", actor["nombre"]) if actor else "Usuario",
        "actor_foto": actor.get("foto_perfil", "") if actor else "",
        "conversation_id": notification.get("conversation_id"),
        "message_preview": notification.get("message_preview", ""),
        "read": bool(notification.get("read", False)),
        "created_at": notification["created_at"],
    }


def get_token_from_request() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return None


def get_current_user(store: dict[str, Any]) -> dict[str, Any] | None:
    token = get_token_from_request()
    if not token:
        return None

    session = next((item for item in store["sessions"] if item["token"] == token), None)
    if not session:
        return None

    user = next((user for user in store["users"] if user["id"] == session["user_id"]), None)
    if not user or user.get("banned"):
        return None
    return user


def require_admin(store: dict[str, Any]) -> tuple[dict[str, Any] | None, Any | None]:
    user = get_current_user(store)
    if not user:
        return None, bad_request("Sesion invalida", 401)
    if user["role"] != "admin":
        return None, bad_request("Solo el administrador puede hacer esto", 403)
    return user, None


def validate_email(value: str) -> bool:
    return "@" in value and "." in value


def bad_request(message: str, code: int = 400):
    return jsonify({"error": message}), code


@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/health")
def health():
    return jsonify(
        {
            "app": "Cannafy",
            "status": "ok",
            "message": "API lista para trabajar",
        }
    )


@app.get("/<path:filename>")
def static_pages(filename: str):
    if filename not in ALLOWED_STATIC_FILES:
        return bad_request("Archivo no encontrado", 404)
    return send_from_directory(BASE_DIR, filename)


@app.post("/api/auth/register")
def register():
    data = request.get_json(silent=True) or {}

    role = str(data.get("role", "")).strip().lower()
    nombre = str(data.get("nombre", "")).strip()
    correo = str(data.get("correo", "")).strip().lower()
    password = str(data.get("password", ""))
    telefono = str(data.get("telefono", "")).strip()
    acepto_terminos = bool(data.get("acepto_terminos"))
    edad = data.get("edad")
    documento = str(data.get("documento", "")).strip()

    if role not in {"dealer", "consumidor"}:
        return bad_request("Rol invalido")
    if not nombre or len(nombre) > 24:
        return bad_request("Nombre invalido")
    if not validate_email(correo):
        return bad_request("Correo invalido")
    if len(password) < 6:
        return bad_request("La contrasena debe tener minimo 6 caracteres")
    if not telefono:
        return bad_request("Telefono requerido")
    if not acepto_terminos:
        return bad_request("Debes aceptar los terminos")

    if role == "dealer":
        try:
            edad_int = int(edad)
        except (TypeError, ValueError):
            return bad_request("Edad invalida")
        if edad_int < 18:
            return bad_request("Debes ser mayor de edad para registrarte como dealer")
        if len(documento) != 8 or not documento.isdigit():
            return bad_request("Documento invalido")
    else:
        edad_int = None
        documento = ""

    store = read_store()

    if any(user["correo"] == correo for user in store["users"]):
        return bad_request("Ya existe una cuenta con ese correo", 409)

    user = {
        "id": next_id(store["users"]),
        "role": role,
        "nombre": nombre,
        "apodo": nombre,
        "bio": "",
        "foto_perfil": "",
        "correo": correo,
        "telefono": telefono,
        "edad": edad_int,
        "documento": documento,
        "password_hash": generate_password_hash(password),
        "accepted_terms": acepto_terminos,
        "banned": False,
        "created_at": utc_now(),
    }

    store["users"].append(user)
    write_store(store)

    return jsonify({"mensaje": "Usuario registrado", "user": sanitize_user(user)}), 201


@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    correo = str(data.get("correo", "")).strip().lower()
    password = str(data.get("password", ""))

    if not validate_email(correo) or not password:
        return bad_request("Credenciales incompletas")

    store = read_store()
    user = next((item for item in store["users"] if item["correo"] == correo), None)

    if not user or not check_password_hash(user["password_hash"], password):
        return bad_request("Credenciales incorrectas", 401)
    if user.get("banned"):
        return bad_request("Tu cuenta fue suspendida por administracion", 403)

    token = secrets.token_hex(24)
    store["sessions"] = [item for item in store["sessions"] if item["user_id"] != user["id"]]
    store["sessions"].append(
        {"token": token, "user_id": user["id"], "created_at": utc_now()}
    )
    write_store(store)

    return jsonify({"mensaje": "Login correcto", "token": token, "user": sanitize_user(user)})


@app.get("/api/auth/me")
def me():
    store = read_store()
    user = get_current_user(store)
    if not user:
        return bad_request("Sesion invalida", 401)

    return jsonify({"user": sanitize_user(user)})


@app.put("/api/auth/profile")
def update_profile():
    store = read_store()
    user = get_current_user(store)
    if not user:
        return bad_request("Sesion invalida", 401)

    data = request.get_json(silent=True) or {}
    apodo = str(data.get("apodo", user.get("apodo", user["nombre"]))).strip()
    bio = str(data.get("bio", user.get("bio", ""))).strip()
    foto_perfil = str(data.get("foto_perfil", user.get("foto_perfil", ""))).strip()

    if not apodo or len(apodo) > 24:
        return bad_request("Apodo invalido")
    if len(bio) > 160:
        return bad_request("La bio es demasiado larga")
    if foto_perfil and not (
        foto_perfil.startswith(("http://", "https://")) or foto_perfil.startswith("data:image/")
    ):
        return bad_request("La foto debe ser una URL valida o una imagen subida")

    user["apodo"] = apodo
    user["bio"] = bio
    user["foto_perfil"] = foto_perfil

    for product in store["products"]:
        if product["dealer_id"] == user["id"]:
            product["dealer_nombre"] = apodo
            product["dealer_foto"] = foto_perfil

    write_store(store)
    return jsonify({"mensaje": "Perfil actualizado", "user": sanitize_user(user)})


@app.get("/api/users")
def list_users():
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Sesion invalida", 401)

    users = [
        sanitize_user(user)
        for user in store["users"]
        if user["id"] != current_user["id"]
    ]
    users.sort(key=lambda item: (item["role"], item["nombre"].lower()))
    return jsonify(users)


@app.get("/api/notifications")
def list_notifications():
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Sesion invalida", 401)

    notifications = [
        sanitize_notification(notification, store)
        for notification in sorted(
            store.get("notifications", []),
            key=lambda item: item["id"],
            reverse=True,
        )
        if notification["user_id"] == current_user["id"]
    ]
    unread_count = sum(1 for item in notifications if not item["read"])
    return jsonify({"items": notifications[:30], "unread_count": unread_count})


@app.post("/api/notifications/read")
def mark_notifications_read():
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Sesion invalida", 401)

    data = request.get_json(silent=True) or {}
    conversation_id = data.get("conversation_id")

    for notification in store.get("notifications", []):
        if notification["user_id"] != current_user["id"]:
            continue
        if conversation_id is not None and notification.get("conversation_id") != conversation_id:
            continue
        notification["read"] = True

    write_store(store)
    return jsonify({"mensaje": "Notificaciones actualizadas"})


@app.get("/api/admin/users")
def admin_list_users():
    store = read_store()
    admin_user, error_response = require_admin(store)
    if error_response:
        return error_response

    users = [sanitize_user(user) for user in store["users"] if user["id"] != admin_user["id"]]
    users.sort(key=lambda item: (item["banned"], item["role"], item["nombre"].lower()))
    return jsonify(users)


@app.post("/api/admin/users/<int:user_id>/ban")
def admin_ban_user(user_id: int):
    store = read_store()
    admin_user, error_response = require_admin(store)
    if error_response:
        return error_response

    user = next((item for item in store["users"] if item["id"] == user_id), None)
    if not user:
        return bad_request("Usuario no encontrado", 404)
    if user["id"] == admin_user["id"]:
        return bad_request("No puedes banear tu propia cuenta", 400)
    if user["role"] == "admin":
        return bad_request("No puedes banear a otro administrador", 400)

    user["banned"] = True
    store["sessions"] = [session for session in store["sessions"] if session["user_id"] != user_id]
    write_store(store)
    return jsonify({"mensaje": "Usuario baneado", "user": sanitize_user(user)})


@app.post("/api/admin/users/<int:user_id>/unban")
def admin_unban_user(user_id: int):
    store = read_store()
    _, error_response = require_admin(store)
    if error_response:
        return error_response

    user = next((item for item in store["users"] if item["id"] == user_id), None)
    if not user:
        return bad_request("Usuario no encontrado", 404)

    user["banned"] = False
    write_store(store)
    return jsonify({"mensaje": "Usuario rehabilitado", "user": sanitize_user(user)})


@app.post("/api/auth/logout")
def logout():
    token = get_token_from_request()
    if not token:
        return bad_request("Sesion invalida", 401)

    store = read_store()
    sessions_before = len(store["sessions"])
    store["sessions"] = [item for item in store["sessions"] if item["token"] != token]
    if len(store["sessions"]) == sessions_before:
        return bad_request("Sesion invalida", 401)

    write_store(store)
    return jsonify({"mensaje": "Sesion cerrada"})


@app.get("/api/products")
def list_products():
    store = read_store()
    products = sorted(store["products"], key=lambda item: item["id"], reverse=True)
    return jsonify([sanitize_product(product) for product in products])


@app.get("/api/products/<int:product_id>")
def get_product(product_id: int):
    store = read_store()
    product = next((item for item in store["products"] if item["id"] == product_id), None)
    if not product:
        return bad_request("Producto no encontrado", 404)
    return jsonify(sanitize_product(product))


@app.post("/api/products")
def create_product():
    store = read_store()
    user = get_current_user(store)
    if not user:
        return bad_request("Debes iniciar sesion", 401)
    if user["role"] != "dealer":
        return bad_request("Solo los dealers pueden publicar productos", 403)

    data = request.get_json(silent=True) or {}
    nombre = str(data.get("nombre", "")).strip()
    precio = str(data.get("precio", "")).strip()
    imagen = str(data.get("imagen", "")).strip()
    imagen_archivo = str(data.get("imagen_archivo", "")).strip()
    descripcion = str(data.get("descripcion", "")).strip()
    oferta_activa = bool(data.get("oferta_activa"))
    precio_oferta = str(data.get("precio_oferta", "")).strip()

    if not nombre or len(nombre) > 60:
        return bad_request("Nombre de producto invalido")
    if not precio:
        return bad_request("Precio requerido")
    imagen_final = imagen_archivo or imagen
    if not imagen_final:
        return bad_request("Debes subir una imagen o indicar una URL")
    if not (
        imagen_final.startswith(("http://", "https://"))
        or imagen_final.startswith("data:image/")
    ):
        return bad_request("La imagen debe ser una URL valida o un archivo de imagen")
    if len(descripcion) > 180:
        return bad_request("Descripcion demasiado larga")
    if oferta_activa and not precio_oferta:
        return bad_request("Debes indicar un precio de oferta")

    product = {
        "id": next_id(store["products"]),
        "dealer_id": user["id"],
        "dealer_nombre": user.get("apodo", user["nombre"]),
        "dealer_foto": user.get("foto_perfil", ""),
        "nombre": nombre,
        "precio": precio,
        "oferta_activa": oferta_activa,
        "precio_oferta": precio_oferta,
        "imagen": imagen_final,
        "descripcion": descripcion,
        "created_at": utc_now(),
    }
    store["products"].append(product)
    write_store(store)

    return jsonify({"mensaje": "Producto publicado", "product": sanitize_product(product)}), 201


@app.put("/api/products/<int:product_id>")
def update_product(product_id: int):
    store = read_store()
    user = get_current_user(store)
    if not user:
        return bad_request("Debes iniciar sesion", 401)
    if user["role"] != "dealer":
        return bad_request("Solo los dealers pueden modificar productos", 403)

    product = next((item for item in store["products"] if item["id"] == product_id), None)
    if not product:
        return bad_request("Producto no encontrado", 404)
    if product["dealer_id"] != user["id"]:
        return bad_request("No puedes modificar este producto", 403)

    data = request.get_json(silent=True) or {}
    nombre = str(data.get("nombre", product["nombre"])).strip()
    precio = str(data.get("precio", product["precio"])).strip()
    descripcion = str(data.get("descripcion", product.get("descripcion", ""))).strip()
    oferta_activa = bool(data.get("oferta_activa", product.get("oferta_activa", False)))
    precio_oferta = str(data.get("precio_oferta", product.get("precio_oferta", ""))).strip()

    if not nombre or len(nombre) > 60:
        return bad_request("Nombre de producto invalido")
    if not precio:
        return bad_request("Precio requerido")
    if len(descripcion) > 180:
        return bad_request("Descripcion demasiado larga")
    if oferta_activa and not precio_oferta:
        return bad_request("Debes indicar un precio de oferta")

    product["nombre"] = nombre
    product["precio"] = precio
    product["descripcion"] = descripcion
    product["oferta_activa"] = oferta_activa
    product["precio_oferta"] = precio_oferta
    write_store(store)

    return jsonify({"mensaje": "Producto actualizado", "product": sanitize_product(product)})


@app.delete("/api/products/<int:product_id>")
def delete_product(product_id: int):
    store = read_store()
    user = get_current_user(store)
    if not user:
        return bad_request("Debes iniciar sesion", 401)

    product = next((item for item in store["products"] if item["id"] == product_id), None)
    if not product:
        return bad_request("Producto no encontrado", 404)
    if user["role"] != "dealer" or product["dealer_id"] != user["id"]:
        return bad_request("No puedes eliminar este producto", 403)

    store["products"] = [item for item in store["products"] if item["id"] != product_id]
    write_store(store)
    return jsonify({"mensaje": "Producto eliminado"})


@app.get("/api/conversations")
def list_conversations():
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Debes iniciar sesion", 401)

    conversations = [
        sanitize_conversation(conversation, current_user["id"], store)
        for conversation in store["conversations"]
        if current_user["id"] in conversation["participant_ids"]
    ]
    conversations.sort(key=lambda item: item["updated_at"], reverse=True)
    return jsonify(conversations)


@app.post("/api/conversations")
def start_conversation():
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Debes iniciar sesion", 401)

    data = request.get_json(silent=True) or {}
    try:
        recipient_id = int(data.get("recipient_id"))
    except (TypeError, ValueError):
        return bad_request("Destinatario invalido")

    if recipient_id == current_user["id"]:
        return bad_request("No puedes iniciar un chat contigo")

    recipient = next((user for user in store["users"] if user["id"] == recipient_id), None)
    if not recipient:
        return bad_request("Usuario no encontrado", 404)

    participant_ids = sorted([current_user["id"], recipient_id])
    existing = next(
        (
            conversation
            for conversation in store["conversations"]
            if sorted(conversation["participant_ids"]) == participant_ids
        ),
        None,
    )
    if existing:
        return jsonify(
            {"conversation": sanitize_conversation(existing, current_user["id"], store)}
        )

    conversation = {
        "id": next_id(store["conversations"]),
        "participant_ids": participant_ids,
        "messages": [],
        "updated_at": utc_now(),
    }
    store["conversations"].append(conversation)
    write_store(store)
    return jsonify({"conversation": sanitize_conversation(conversation, current_user["id"], store)}), 201


@app.get("/api/conversations/<int:conversation_id>/messages")
def get_messages(conversation_id: int):
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Debes iniciar sesion", 401)

    conversation = next(
        (item for item in store["conversations"] if item["id"] == conversation_id), None
    )
    if not conversation or current_user["id"] not in conversation["participant_ids"]:
        return bad_request("Conversacion no encontrada", 404)

    for notification in store.get("notifications", []):
        if (
            notification["user_id"] == current_user["id"]
            and notification.get("type") == "message"
            and notification.get("conversation_id") == conversation_id
        ):
            notification["read"] = True

    write_store(store)
    messages = [sanitize_message(message, store) for message in conversation.get("messages", [])]
    return jsonify(messages)


@app.post("/api/conversations/<int:conversation_id>/messages")
def send_message(conversation_id: int):
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Debes iniciar sesion", 401)

    conversation = next(
        (item for item in store["conversations"] if item["id"] == conversation_id), None
    )
    if not conversation or current_user["id"] not in conversation["participant_ids"]:
        return bad_request("Conversacion no encontrada", 404)

    data = request.get_json(silent=True) or {}
    content = str(data.get("content", "")).strip()
    if not content:
        return bad_request("Escribe un mensaje")
    if len(content) > 600:
        return bad_request("El mensaje es demasiado largo")

    message = {
        "id": next_id(conversation.get("messages", [])),
        "conversation_id": conversation_id,
        "sender_id": current_user["id"],
        "content": content,
        "created_at": utc_now(),
    }
    conversation.setdefault("messages", []).append(message)
    conversation["updated_at"] = message["created_at"]
    recipient_id = next(
        participant_id
        for participant_id in conversation["participant_ids"]
        if participant_id != current_user["id"]
    )
    store.setdefault("notifications", []).append(
        {
            "id": next_id(store["notifications"]),
            "type": "message",
            "user_id": recipient_id,
            "actor_id": current_user["id"],
            "conversation_id": conversation_id,
            "message_preview": content[:120],
            "read": False,
            "created_at": message["created_at"],
        }
    )
    write_store(store)
    return jsonify({"mensaje": "Mensaje enviado", "message": sanitize_message(message, store)}), 201


@app.get("/api/posts")
def list_posts():
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Debes iniciar sesion", 401)

    posts = [sanitize_post(post, store) for post in sorted(store["posts"], key=lambda item: item["id"], reverse=True)]
    return jsonify(posts)


@app.post("/api/posts")
def create_post():
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Debes iniciar sesion", 401)

    data = request.get_json(silent=True) or {}
    content = str(data.get("content", "")).strip()
    if not content:
        return bad_request("La publicacion no puede estar vacia")
    if len(content) > 500:
        return bad_request("La publicacion es demasiado larga")

    post = {
        "id": next_id(store["posts"]),
        "author_id": current_user["id"],
        "content": content,
        "created_at": utc_now(),
        "comments": [],
    }
    store["posts"].append(post)
    write_store(store)
    return jsonify({"mensaje": "Publicacion creada", "post": sanitize_post(post, store)}), 201


@app.post("/api/posts/<int:post_id>/comments")
def add_comment(post_id: int):
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Debes iniciar sesion", 401)

    post = next((item for item in store["posts"] if item["id"] == post_id), None)
    if not post:
        return bad_request("Publicacion no encontrada", 404)

    data = request.get_json(silent=True) or {}
    content = str(data.get("content", "")).strip()
    if not content:
        return bad_request("El comentario no puede estar vacio")
    if len(content) > 280:
        return bad_request("El comentario es demasiado largo")

    comment = {
        "id": next_id(post.get("comments", [])),
        "author_id": current_user["id"],
        "content": content,
        "created_at": utc_now(),
    }
    post.setdefault("comments", []).append(comment)
    write_store(store)
    return jsonify({"mensaje": "Comentario agregado", "post": sanitize_post(post, store)}), 201


if __name__ == "__main__":
    ensure_store()
    app.run(host="0.0.0.0", port=5000, debug=True)
