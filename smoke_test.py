import time

from app import app


def main() -> None:
    client = app.test_client()
    stamp = int(time.time())
    dealer_email = f"dealer-demo-{stamp}@cannafy.test"
    buyer_email = f"buyer-demo-{stamp}@cannafy.test"

    print("health", client.get("/api/health").status_code)

    register = client.post(
        "/api/auth/register",
        json={
            "role": "dealer",
            "nombre": "demo-dealer",
            "edad": 24,
            "documento": "12345678",
            "telefono": "+51999999999",
            "correo": dealer_email,
            "password": "secret123",
            "acepto_terminos": True,
        },
    )
    print("register", register.status_code)

    consumer_register = client.post(
        "/api/auth/register",
        json={
            "role": "consumidor",
            "nombre": "demo-buyer",
            "telefono": "+51911111111",
            "correo": buyer_email,
            "password": "secret123",
            "acepto_terminos": True,
        },
    )
    print("consumer_register", consumer_register.status_code)

    login = client.post(
        "/api/auth/login",
        json={"correo": dealer_email, "password": "secret123"},
    )
    print("login", login.status_code)
    token = login.json["token"]
    buyer_id = consumer_register.json["user"]["id"]

    profile = client.put(
        "/api/auth/profile",
        json={
            "apodo": "dealer-profile",
            "bio": "Perfil de prueba",
            "foto_perfil": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WnQx7kAAAAASUVORK5CYII=",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    print("profile", profile.status_code)

    product = client.post(
        "/api/products",
        json={
            "nombre": "Flor premium",
            "precio": "S/ 35",
            "imagen_archivo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WnQx7kAAAAASUVORK5CYII=",
            "descripcion": "Lote de prueba para verificar la API",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    print("create_product", product.status_code)

    products = client.get("/api/products")
    print("products", products.status_code, len(products.json))
    product_detail = client.get(f"/api/products/{product.json['product']['id']}")
    print("product_detail", product_detail.status_code)
    update_product = client.put(
        f"/api/products/{product.json['product']['id']}",
        json={
            "nombre": "Flor premium editada",
            "precio": "S/ 40",
            "descripcion": "Producto actualizado desde prueba",
            "oferta_activa": True,
            "precio_oferta": "S/ 32",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    print("update_product", update_product.status_code)

    conversation = client.post(
        "/api/conversations",
        json={"recipient_id": buyer_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    print("conversation", conversation.status_code)
    conversation_id = conversation.json["conversation"]["id"]

    message = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "Hola, este es un mensaje de prueba"},
        headers={"Authorization": f"Bearer {token}"},
    )
    print("message", message.status_code)

    post = client.post(
        "/api/posts",
        json={"content": "Publicación de prueba para la zona social"},
        headers={"Authorization": f"Bearer {token}"},
    )
    print("post", post.status_code)
    post_id = post.json["post"]["id"]

    comment = client.post(
        f"/api/posts/{post_id}/comments",
        json={"content": "Comentario de prueba"},
        headers={"Authorization": f"Bearer {token}"},
    )
    print("comment", comment.status_code)


if __name__ == "__main__":
    main()
