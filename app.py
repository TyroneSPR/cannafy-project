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
DEFAULT_ADMIN_EMAIL = "cannafy.pe@gmail.com"
DEFAULT_ADMIN_PASSWORD = "123456"
DEFAULT_ADMIN_NAME = "ADM CANNAFY"
ALLOWED_STATIC_FILES = {
    "index.html",
    "register.html",
    "forgot-password.html",
    "vendedor.html",
    "tienda.html",
    "chat.html",
    "social.html",
    "perfil.html",
    "usuario.html",
    "reportes.html",
    "admin.html",
    "acerca.html",
    "styles.css",
    "cannafy-logo.png",
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
                "bug_reports": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def ensure_default_admin(store: dict[str, Any]) -> bool:
    existing_admin = next(
        (
            user
            for user in store["users"]
            if user.get("role") == "admin" or user.get("correo") == DEFAULT_ADMIN_EMAIL
        ),
        None,
    )
    if existing_admin:
        changed = False
        if existing_admin.get("role") != "admin":
            existing_admin["role"] = "admin"
            changed = True
        if existing_admin.get("nombre") != DEFAULT_ADMIN_NAME:
            existing_admin["nombre"] = DEFAULT_ADMIN_NAME
            changed = True
        if existing_admin.get("apodo") != "ADM CANNAFY":
            existing_admin["apodo"] = "ADM CANNAFY"
            changed = True
        if existing_admin.get("correo") != DEFAULT_ADMIN_EMAIL:
            existing_admin["correo"] = DEFAULT_ADMIN_EMAIL
            changed = True
        if existing_admin.get("foto_perfil") != "cannafy-logo.png":
            existing_admin["foto_perfil"] = "cannafy-logo.png"
            changed = True
        if existing_admin.get("bio") != "Cuenta administrativa compartida de Cannafy.":
            existing_admin["bio"] = "Cuenta administrativa compartida de Cannafy."
            changed = True
        if not password_matches(existing_admin, DEFAULT_ADMIN_PASSWORD):
            existing_admin["password_hash"] = generate_password_hash(DEFAULT_ADMIN_PASSWORD)
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
            "apodo": "ADM CANNAFY",
            "bio": "Cuenta administrativa compartida de Cannafy.",
            "foto_perfil": "cannafy-logo.png",
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
    store.setdefault("bug_reports", [])
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
        "verified": user["role"] == "admin",
        "created_at": user["created_at"],
    }


def build_dealer_rating(user_id: int, store: dict[str, Any]) -> dict[str, Any]:
    ratings = []
    for dealer in store["users"]:
        for rating in dealer.get("ratings", []):
            if dealer["id"] == user_id:
                ratings.append(rating)
    if not ratings:
        return {"average": 0, "count": 0}
    average = round(sum(item["score"] for item in ratings) / len(ratings), 1)
    return {"average": average, "count": len(ratings)}


def sanitize_message(message: dict[str, Any], store: dict[str, Any]) -> dict[str, Any]:
    sender = next((user for user in store["users"] if user["id"] == message["sender_id"]), None)
    return {
        "id": message["id"],
        "conversation_id": message["conversation_id"],
        "sender_id": message["sender_id"],
        "sender_nombre": sender.get("apodo", sender["nombre"]) if sender else "Usuario",
        "sender_foto": sender.get("foto_perfil", "") if sender else "",
        "sender_role": sender["role"] if sender else None,
        "sender_verified": bool(sender and sender["role"] == "admin"),
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
    reactions = post.get("reactions", {})
    current_user = get_current_user(store)
    comments = []
    for comment in post.get("comments", []):
        comment_author = next(
            (user for user in store["users"] if user["id"] == comment["author_id"]), None
        )
        comment_reactions = comment.get("reactions", {})
        replies = []
        for reply in comment.get("replies", []):
            reply_author = next(
                (user for user in store["users"] if user["id"] == reply["author_id"]), None
            )
            replies.append(
                {
                    "id": reply["id"],
                    "author_id": reply["author_id"],
                    "author_nombre": reply_author.get("apodo", reply_author["nombre"])
                    if reply_author
                    else "Usuario",
                    "author_foto": reply_author.get("foto_perfil", "") if reply_author else "",
                    "author_verified": bool(reply_author and reply_author["role"] == "admin"),
                    "content": reply["content"],
                    "created_at": reply["created_at"],
                }
            )

        comments.append(
            {
                "id": comment["id"],
                "author_id": comment["author_id"],
                "author_nombre": comment_author.get("apodo", comment_author["nombre"])
                if comment_author
                else "Usuario",
                "author_foto": comment_author.get("foto_perfil", "") if comment_author else "",
                "author_verified": bool(comment_author and comment_author["role"] == "admin"),
                "content": comment["content"],
                "created_at": comment["created_at"],
                "replies": replies,
                "reactions": {
                    "heart": len(comment_reactions.get("heart", [])),
                    "fire": len(comment_reactions.get("fire", [])),
                },
                "user_reaction": next(
                    (
                        reaction_name
                        for reaction_name, user_ids in comment_reactions.items()
                        if current_user and current_user["id"] in user_ids
                    ),
                    None,
                ),
            }
        )

    return {
        "id": post["id"],
        "author_id": post["author_id"],
        "author_nombre": author.get("apodo", author["nombre"]) if author else "Usuario",
        "author_role": author["role"] if author else None,
        "author_foto": author.get("foto_perfil", "") if author else "",
        "verified": bool(author and author["role"] == "admin"),
        "content": post["content"],
        "imagen": post.get("imagen", ""),
        "created_at": post["created_at"],
        "reactions": {
            "heart": len(reactions.get("heart", [])),
            "fire": len(reactions.get("fire", [])),
        },
        "user_reaction": next(
            (
                reaction_name
                for reaction_name, user_ids in reactions.items()
                if current_user and current_user["id"] in user_ids
            ),
            None,
        ),
        "comments": comments,
    }


def sanitize_product(product: dict[str, Any]) -> dict[str, Any]:
    oferta_activa = bool(product.get("oferta_activa"))
    precio_oferta = str(product.get("precio_oferta", "")).strip()
    categoria = str(product.get("categoria", "accesorios")).strip().lower() or "accesorios"
    especificaciones = product.get("especificaciones", {}) or {}
    colores = [str(item).strip() for item in product.get("colores", []) if str(item).strip()]
    return {
        "id": product["id"],
        "dealer_id": product["dealer_id"],
        "dealer_nombre": "Cannafy" if product.get("dealer_verified") else product["dealer_nombre"],
        "dealer_foto": product.get("dealer_foto", ""),
        "dealer_verified": bool(product.get("dealer_verified", False)),
        "nombre": product["nombre"],
        "categoria": categoria,
        "precio": product["precio"],
        "oferta_activa": oferta_activa,
        "precio_oferta": precio_oferta,
        "precio_mostrar": precio_oferta if oferta_activa and precio_oferta else product["precio"],
        "imagen": product["imagen"],
        "descripcion": product["descripcion"],
        "colores": colores,
        "especificaciones": {
            "material": str(especificaciones.get("material", "")).strip(),
            "tamano": str(especificaciones.get("tamano", "")).strip(),
            "contenido": str(especificaciones.get("contenido", "")).strip(),
        },
        "dealer_rating": product.get("dealer_rating", {"average": 0, "count": 0}),
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


def sanitize_report(report: dict[str, Any], store: dict[str, Any]) -> dict[str, Any]:
    author = next((user for user in store["users"] if user["id"] == report["author_id"]), None)
    return {
        "id": report["id"],
        "author_id": report["author_id"],
        "author_nombre": author.get("apodo", author["nombre"]) if author else "Usuario",
        "author_foto": author.get("foto_perfil", "") if author else "",
        "content": report["content"],
        "imagen": report.get("imagen", ""),
        "status": report.get("status", "nuevo"),
        "created_at": report["created_at"],
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


def normalize_phone(value: str) -> str:
    cleaned = "".join(char for char in str(value).strip() if char.isdigit() or char == "+")
    if cleaned.count("+") > 1:
        return ""
    if "+" in cleaned and not cleaned.startswith("+"):
        return ""
    return cleaned


def validate_phone(value: str) -> bool:
    normalized = normalize_phone(value)
    digits = normalized.replace("+", "")
    return len(digits) >= 7


def find_user_by_identifier(identifier: str, store: dict[str, Any]) -> dict[str, Any] | None:
    normalized_identifier = identifier.strip().lower()
    normalized_phone = normalize_phone(identifier)
    return next(
        (
            user
            for user in store["users"]
            if user.get("correo", "").strip().lower() == normalized_identifier
            or normalize_phone(user.get("telefono", "")) == normalized_phone
        ),
        None,
    )


def password_matches(user: dict[str, Any], password: str) -> bool:
    password_hash = user.get("password_hash", "")
    if not password_hash:
        return False
    try:
        return check_password_hash(password_hash, password)
    except ValueError:
        return False


def bad_request(message: str, code: int = 400):
    return jsonify({"error": message}), code


def create_session(store: dict[str, Any], user: dict[str, Any]) -> str:
    token = secrets.token_hex(24)
    store["sessions"] = [item for item in store["sessions"] if item["user_id"] != user["id"]]
    store["sessions"].append(
        {"token": token, "user_id": user["id"], "created_at": utc_now()}
    )
    return token


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
    telefono = normalize_phone(data.get("telefono", ""))
    acepto_terminos = bool(data.get("acepto_terminos", True))
    edad = data.get("edad")
    documento = str(data.get("documento", "")).strip()

    if role not in {"dealer", "consumidor"}:
        return bad_request("Rol invalido")
    if not nombre or len(nombre) > 24:
        return bad_request("Nombre invalido")
    if correo and not validate_email(correo):
        return bad_request("Correo invalido")
    if telefono and not validate_phone(telefono):
        return bad_request("Telefono invalido")
    if not correo and not telefono:
        return bad_request("Debes indicar un correo o telefono")
    if len(password) < 6:
        return bad_request("La contrasena debe tener minimo 6 caracteres")
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

    if correo and any(user.get("correo") == correo for user in store["users"]):
        return bad_request("Ya existe una cuenta con ese correo", 409)
    if telefono and any(normalize_phone(user.get("telefono", "")) == telefono for user in store["users"]):
        return bad_request("Ya existe una cuenta con ese telefono", 409)

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
        "ratings": [],
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
    identifier = str(data.get("identifier", data.get("correo", data.get("telefono", "")))).strip()
    password = str(data.get("password", ""))

    if not identifier or not password:
        return bad_request("Credenciales incompletas")

    store = read_store()
    user = find_user_by_identifier(identifier, store)

    if not user or not password_matches(user, password):
        return bad_request("Credenciales incorrectas", 401)
    if user.get("banned"):
        return bad_request("Tu cuenta fue suspendida por administracion", 403)

    token = create_session(store, user)
    write_store(store)

    return jsonify({"mensaje": "Login correcto", "token": token, "user": sanitize_user(user)})


@app.post("/api/auth/forgot-password")
def forgot_password():
    data = request.get_json(silent=True) or {}
    identifier = str(data.get("identifier", "")).strip()
    new_password = str(data.get("new_password", ""))

    if not identifier or len(new_password) < 6:
        return bad_request("Datos incompletos")

    store = read_store()
    user = find_user_by_identifier(identifier, store)
    if not user:
        return bad_request("No encontramos una cuenta con ese acceso", 404)

    user["password_hash"] = generate_password_hash(new_password)
    write_store(store)
    return jsonify({"mensaje": "Contrasena actualizada"})


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
            product["dealer_rating"] = build_dealer_rating(user["id"], store)
            product["dealer_verified"] = user["role"] == "admin"

    write_store(store)
    return jsonify({"mensaje": "Perfil actualizado", "user": sanitize_user(user)})


@app.put("/api/auth/security/password")
def update_password():
    store = read_store()
    user = get_current_user(store)
    if not user:
        return bad_request("Sesion invalida", 401)

    data = request.get_json(silent=True) or {}
    current_password = str(data.get("current_password", ""))
    new_password = str(data.get("new_password", ""))

    if not current_password or not new_password:
        return bad_request("Completa ambas contraseñas")
    if not password_matches(user, current_password):
        return bad_request("La contraseña actual no es correcta", 403)
    if len(new_password) < 6:
        return bad_request("La nueva contraseña debe tener minimo 6 caracteres")
    if password_matches(user, new_password):
        return bad_request("La nueva contraseña debe ser diferente")

    user["password_hash"] = generate_password_hash(new_password)
    write_store(store)
    return jsonify({"mensaje": "Contraseña actualizada"})


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


@app.get("/api/users/<int:user_id>")
def get_user_profile(user_id: int):
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Sesion invalida", 401)

    user = next((item for item in store["users"] if item["id"] == user_id), None)
    if not user:
        return bad_request("Usuario no encontrado", 404)

    user_data = sanitize_user(user)
    dealer_products = [
        sanitize_product(product)
        for product in sorted(store["products"], key=lambda item: item["id"], reverse=True)
        if product["dealer_id"] == user_id
    ]
    post_count = sum(1 for post in store.get("posts", []) if post.get("author_id") == user_id)
    if user["role"] == "dealer":
        rating = build_dealer_rating(user_id, store)
        my_rating = next(
            (
                item["score"]
                for item in user.get("ratings", [])
                if item["author_id"] == current_user["id"]
            ),
            None,
        )
    else:
        rating = {"average": 0, "count": 0}
        my_rating = None

    return jsonify(
        {
            "user": user_data,
            "products": dealer_products,
            "stats": {
                "posts": post_count,
                "followers": 0,
                "following": 0,
                "products": len(dealer_products),
            },
            "rating": rating,
            "my_rating": my_rating,
        }
    )


@app.post("/api/dealers/<int:dealer_id>/ratings")
def rate_dealer(dealer_id: int):
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Sesion invalida", 401)

    dealer = next((item for item in store["users"] if item["id"] == dealer_id), None)
    if not dealer or dealer["role"] != "dealer":
        return bad_request("Dealer no encontrado", 404)
    if current_user["id"] == dealer_id:
        return bad_request("No puedes calificarte a ti mismo", 400)

    data = request.get_json(silent=True) or {}
    try:
        score = int(data.get("score"))
    except (TypeError, ValueError):
        return bad_request("Calificacion invalida")
    if score < 1 or score > 5:
        return bad_request("La calificacion debe ser entre 1 y 5")

    dealer.setdefault("ratings", [])
    existing = next(
        (item for item in dealer["ratings"] if item["author_id"] == current_user["id"]),
        None,
    )
    if existing:
        existing["score"] = score
        existing["created_at"] = utc_now()
    else:
        dealer["ratings"].append(
            {
                "author_id": current_user["id"],
                "score": score,
                "created_at": utc_now(),
            }
        )

    rating = build_dealer_rating(dealer_id, store)
    for product in store["products"]:
        if product["dealer_id"] == dealer_id:
            product["dealer_rating"] = rating

    write_store(store)
    return jsonify({"mensaje": "Calificacion guardada", "rating": rating, "my_rating": score})


@app.post("/api/reports")
def create_report():
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Sesion invalida", 401)

    data = request.get_json(silent=True) or {}
    content = str(data.get("content", "")).strip()
    imagen = str(data.get("imagen", "")).strip()
    if not content or len(content) < 8:
        return bad_request("Describe el problema con un poco mas de detalle")
    if len(content) > 1200:
        return bad_request("El reporte es demasiado largo")
    if imagen and not (
        imagen.startswith(("http://", "https://")) or imagen.startswith("data:image/")
    ):
        return bad_request("La imagen debe ser una URL valida o una imagen subida")

    report = {
        "id": next_id(store["bug_reports"]),
        "author_id": current_user["id"],
        "content": content,
        "imagen": imagen,
        "status": "nuevo",
        "created_at": utc_now(),
    }
    store["bug_reports"].append(report)
    write_store(store)
    return jsonify({"mensaje": "Reporte enviado", "report": sanitize_report(report, store)}), 201


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


@app.get("/api/admin/reports")
def admin_list_reports():
    store = read_store()
    _, error_response = require_admin(store)
    if error_response:
        return error_response

    reports = [
        sanitize_report(report, store)
        for report in sorted(store.get("bug_reports", []), key=lambda item: item["id"], reverse=True)
    ]
    return jsonify(reports)


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
    if user["role"] not in {"dealer", "admin"}:
        return bad_request("Solo las cuentas de tienda pueden publicar productos", 403)

    data = request.get_json(silent=True) or {}
    nombre = str(data.get("nombre", "")).strip()
    precio = str(data.get("precio", "")).strip()
    imagen = str(data.get("imagen", "")).strip()
    imagen_archivo = str(data.get("imagen_archivo", "")).strip()
    descripcion = str(data.get("descripcion", "")).strip()
    categoria = str(data.get("categoria", "")).strip().lower()
    oferta_activa = bool(data.get("oferta_activa"))
    precio_oferta = str(data.get("precio_oferta", "")).strip()
    colores = [str(item).strip() for item in data.get("colores", []) if str(item).strip()]
    especificaciones = data.get("especificaciones", {}) or {}
    material = str(especificaciones.get("material", "")).strip()
    tamano = str(especificaciones.get("tamano", "")).strip()
    contenido = str(especificaciones.get("contenido", "")).strip()

    if not nombre or len(nombre) > 60:
        return bad_request("Nombre de producto invalido")
    if categoria not in {"papeles", "grinders", "pipas", "encendedores", "accesorios"}:
        return bad_request("Categoria invalida")
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
    if len(colores) > 8:
        return bad_request("Demasiadas opciones de color")
    if any(len(item) > 30 for item in colores):
        return bad_request("Cada color debe ser corto")
    if len(material) > 50 or len(tamano) > 50 or len(contenido) > 80:
        return bad_request("Las especificaciones son demasiado largas")
    if oferta_activa and not precio_oferta:
        return bad_request("Debes indicar un precio de oferta")

    product = {
        "id": next_id(store["products"]),
        "dealer_id": user["id"],
        "dealer_nombre": user.get("apodo", user["nombre"]),
        "dealer_foto": user.get("foto_perfil", ""),
        "dealer_rating": build_dealer_rating(user["id"], store),
        "dealer_verified": user["role"] == "admin",
        "nombre": nombre,
        "categoria": categoria,
        "precio": precio,
        "oferta_activa": oferta_activa,
        "precio_oferta": precio_oferta,
        "imagen": imagen_final,
        "descripcion": descripcion,
        "colores": colores,
        "especificaciones": {
            "material": material,
            "tamano": tamano,
            "contenido": contenido,
        },
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
    if user["role"] not in {"dealer", "admin"}:
        return bad_request("Solo las cuentas de tienda pueden modificar productos", 403)

    product = next((item for item in store["products"] if item["id"] == product_id), None)
    if not product:
        return bad_request("Producto no encontrado", 404)
    if product["dealer_id"] != user["id"]:
        return bad_request("No puedes modificar este producto", 403)

    data = request.get_json(silent=True) or {}
    nombre = str(data.get("nombre", product["nombre"])).strip()
    precio = str(data.get("precio", product["precio"])).strip()
    descripcion = str(data.get("descripcion", product.get("descripcion", ""))).strip()
    categoria = str(data.get("categoria", product.get("categoria", "accesorios"))).strip().lower()
    oferta_activa = bool(data.get("oferta_activa", product.get("oferta_activa", False)))
    precio_oferta = str(data.get("precio_oferta", product.get("precio_oferta", ""))).strip()
    colores = [str(item).strip() for item in data.get("colores", product.get("colores", [])) if str(item).strip()]
    especificaciones = data.get("especificaciones", product.get("especificaciones", {})) or {}
    material = str(especificaciones.get("material", "")).strip()
    tamano = str(especificaciones.get("tamano", "")).strip()
    contenido = str(especificaciones.get("contenido", "")).strip()

    if not nombre or len(nombre) > 60:
        return bad_request("Nombre de producto invalido")
    if categoria not in {"papeles", "grinders", "pipas", "encendedores", "accesorios"}:
        return bad_request("Categoria invalida")
    if not precio:
        return bad_request("Precio requerido")
    if len(descripcion) > 180:
        return bad_request("Descripcion demasiado larga")
    if len(colores) > 8:
        return bad_request("Demasiadas opciones de color")
    if any(len(item) > 30 for item in colores):
        return bad_request("Cada color debe ser corto")
    if len(material) > 50 or len(tamano) > 50 or len(contenido) > 80:
        return bad_request("Las especificaciones son demasiado largas")
    if oferta_activa and not precio_oferta:
        return bad_request("Debes indicar un precio de oferta")

    product["nombre"] = nombre
    product["categoria"] = categoria
    product["precio"] = precio
    product["descripcion"] = descripcion
    product["oferta_activa"] = oferta_activa
    product["precio_oferta"] = precio_oferta
    product["colores"] = colores
    product["especificaciones"] = {
        "material": material,
        "tamano": tamano,
        "contenido": contenido,
    }
    product["dealer_rating"] = build_dealer_rating(user["id"], store)
    product["dealer_verified"] = user["role"] == "admin"
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
    if user["role"] not in {"dealer", "admin"} or product["dealer_id"] != user["id"]:
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
    imagen = str(data.get("imagen", "")).strip()
    if not content:
        return bad_request("La publicacion no puede estar vacia")
    if len(content) > 500:
        return bad_request("La publicacion es demasiado larga")
    if imagen and not (
        imagen.startswith(("http://", "https://")) or imagen.startswith("data:image/")
    ):
        return bad_request("La imagen debe ser una URL valida o una imagen subida")

    post = {
        "id": next_id(store["posts"]),
        "author_id": current_user["id"],
        "content": content,
        "imagen": imagen,
        "created_at": utc_now(),
        "reactions": {"heart": [], "fire": []},
        "comments": [],
    }
    store["posts"].append(post)
    write_store(store)
    return jsonify({"mensaje": "Publicacion creada", "post": sanitize_post(post, store)}), 201


@app.post("/api/posts/<int:post_id>/reactions")
def react_to_post(post_id: int):
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Debes iniciar sesion", 401)

    post = next((item for item in store["posts"] if item["id"] == post_id), None)
    if not post:
        return bad_request("Publicacion no encontrada", 404)

    data = request.get_json(silent=True) or {}
    reaction = str(data.get("reaction", "")).strip().lower()
    if reaction not in {"heart", "fire"}:
        return bad_request("Reaccion invalida")

    post.setdefault("reactions", {"heart": [], "fire": []})
    for reaction_name in ("heart", "fire"):
        post["reactions"].setdefault(reaction_name, [])
        if current_user["id"] in post["reactions"][reaction_name]:
            post["reactions"][reaction_name] = [
                user_id for user_id in post["reactions"][reaction_name] if user_id != current_user["id"]
            ]

    if data.get("toggle_off") is not True:
        post["reactions"][reaction].append(current_user["id"])

    write_store(store)
    return jsonify({"mensaje": "Reaccion actualizada", "post": sanitize_post(post, store)})


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
    parent_comment_id = data.get("parent_comment_id")
    if not content:
        return bad_request("El comentario no puede estar vacio")
    if len(content) > 280:
        return bad_request("El comentario es demasiado largo")

    if parent_comment_id is not None:
        try:
            parent_comment_id = int(parent_comment_id)
        except (TypeError, ValueError):
            return bad_request("Comentario base invalido")

    if parent_comment_id is None:
        comment = {
            "id": next_id(post.get("comments", [])),
            "author_id": current_user["id"],
            "content": content,
            "created_at": utc_now(),
            "reactions": {"heart": [], "fire": []},
            "replies": [],
        }
        post.setdefault("comments", []).append(comment)
    else:
        comment = next((item for item in post.get("comments", []) if item["id"] == parent_comment_id), None)
        if not comment:
            return bad_request("Comentario no encontrado", 404)
        reply = {
            "id": next_id(comment.get("replies", [])),
            "author_id": current_user["id"],
            "content": content,
            "created_at": utc_now(),
        }
        comment.setdefault("replies", []).append(reply)

    write_store(store)
    return jsonify({"mensaje": "Comentario agregado", "post": sanitize_post(post, store)}), 201


@app.post("/api/posts/<int:post_id>/comments/<int:comment_id>/reactions")
def react_to_comment(post_id: int, comment_id: int):
    store = read_store()
    current_user = get_current_user(store)
    if not current_user:
        return bad_request("Debes iniciar sesion", 401)

    post = next((item for item in store["posts"] if item["id"] == post_id), None)
    if not post:
        return bad_request("Publicacion no encontrada", 404)

    comment = next((item for item in post.get("comments", []) if item["id"] == comment_id), None)
    if not comment:
        return bad_request("Comentario no encontrado", 404)

    data = request.get_json(silent=True) or {}
    reaction = str(data.get("reaction", "")).strip().lower()
    if reaction not in {"heart", "fire"}:
        return bad_request("Reaccion invalida")

    comment.setdefault("reactions", {"heart": [], "fire": []})
    for reaction_name in ("heart", "fire"):
        comment["reactions"].setdefault(reaction_name, [])
        if current_user["id"] in comment["reactions"][reaction_name]:
            comment["reactions"][reaction_name] = [
                user_id
                for user_id in comment["reactions"][reaction_name]
                if user_id != current_user["id"]
            ]

    if data.get("toggle_off") is not True:
        comment["reactions"][reaction].append(current_user["id"])

    write_store(store)
    return jsonify({"mensaje": "Reaccion actualizada", "post": sanitize_post(post, store)})


if __name__ == "__main__":
    ensure_store()
    app.run(host="0.0.0.0", port=5000, debug=True)
