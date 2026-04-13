import tempfile
import time
from pathlib import Path

import app as cannafy_app


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        cannafy_app.DATA_FILE = Path(temp_dir) / "data.json"
        client = cannafy_app.app.test_client()
        stamp = time.time_ns()
        buyer_email = f"buyer-demo-{stamp}@cannafy.test"
        buyer_phone = f"+51{str(stamp)[-8:]}7"

        print("health", client.get("/api/health").status_code)

        consumer_register = client.post(
            "/api/auth/register",
            json={
                "role": "consumidor",
                "nombre": "demo-buyer",
                "telefono": buyer_phone,
                "correo": buyer_email,
                "password": "secret123",
                "acepto_terminos": True,
            },
        )
        print("consumer_register", consumer_register.status_code)

        login = client.post(
            "/api/auth/login",
            json={"identifier": "cannafy.pe@gmail.com", "password": "123456"},
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
                "categoria": "accesorios",
                "precio": "S/ 35",
                "imagen_archivo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WnQx7kAAAAASUVORK5CYII=",
                "descripcion": "Lote de prueba para verificar la API",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        print("create_product", product.status_code)
        product_id = product.json["product"]["id"]

        products = client.get("/api/products")
        print("products", products.status_code, len(products.json))
        product_detail = client.get(f"/api/products/{product_id}")
        print("product_detail", product_detail.status_code)
        update_product = client.put(
            f"/api/products/{product_id}",
            json={
                "nombre": "Flor premium editada",
                "categoria": "accesorios",
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
            json={
                "content": "Publicacion de prueba para la zona social",
                "imagen": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WnQx7kAAAAASUVORK5CYII=",
            },
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
        comment_id = comment.json["post"]["comments"][0]["id"]

        reply = client.post(
            f"/api/posts/{post_id}/comments",
            json={
                "content": "Respuesta de prueba",
                "parent_comment_id": comment_id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        print("reply", reply.status_code)

        comment_reaction = client.post(
            f"/api/posts/{post_id}/comments/{comment_id}/reactions",
            json={"reaction": "heart"},
            headers={"Authorization": f"Bearer {token}"},
        )
        print("comment_reaction", comment_reaction.status_code)

        forgot_password = client.post(
            "/api/auth/forgot-password",
            json={"identifier": buyer_email, "new_password": "secret456"},
        )
        print("forgot_password", forgot_password.status_code)


if __name__ == "__main__":
    main()
