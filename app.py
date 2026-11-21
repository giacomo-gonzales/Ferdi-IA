
from flask import Flask, request, jsonify, send_from_directory
from ai import consultar_ia, ALLOWED_MODELS
import os

app = Flask(
    __name__,
    static_folder="frontend",
    static_url_path=""
)

# Límite máximo de datos recibidos
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024

@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(
        os.path.join(app.root_path, "assets"),
        filename
    )

@app.route("/")
def inicio():
    return send_from_directory("frontend", "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "name": "Ferdi IA",
        "specialty": "Física de Corriente Alterna",
        "models": ALLOWED_MODELS
    })


@app.route("/api/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "La solicitud no contiene datos válidos."
        }), 400

    messages = data.get("messages", [])

    if not isinstance(messages, list) or not messages:
        return jsonify({
            "error": "No se encontró ningún mensaje."
        }), 400

    if len(messages) > 40:
        return jsonify({
            "error": "El historial es demasiado largo."
        }), 400

    
    # Validar el último mensaje
    last_message = messages[-1]

    if not isinstance(last_message, dict) or last_message.get("role") != "user":
        return jsonify({
            "error": "El último mensaje debe ser del usuario."
        }), 400

    content = last_message.get("content")

    # Aceptar texto normal o contenido multimodal
    if isinstance(content, str):
        if not content.strip():
            return jsonify({
                "error": "Escribe una pregunta válida."
            }), 400

    elif isinstance(content, list):
        if not content or len(content) > 2:
            return jsonify({
                "error": "El contenido del mensaje no es válido."
            }), 400

        for item in content:
            if not isinstance(item, dict):
                return jsonify({
                    "error": "El contenido de la imagen no es válido."
                }), 400

            if item.get("type") == "text":
                if not isinstance(item.get("text"), str):
                    return jsonify({
                        "error": "El texto adjunto no es válido."
                    }), 400

            elif item.get("type") == "image_url":
                image_url = item.get("image_url")

                if (
                    not isinstance(image_url, dict)
                    or not isinstance(image_url.get("url"), str)
                    or not image_url["url"].startswith(
                        ("data:image/jpeg;base64,",
                        "data:image/png;base64,",
                        "data:image/webp;base64,")
                    )
                ):
                    return jsonify({
                        "error": "La imagen adjunta no es válida."
                    }), 400

            else:
                return jsonify({
                    "error": "Tipo de contenido no permitido."
                }), 400

    else:
        return jsonify({
            "error": "El formato del mensaje no es válido."
        }), 400


    model = data.get("model", "openai/gpt-oss-20b")

    if model not in ALLOWED_MODELS:
        model = "openai/gpt-oss-20b"

    try:
        temperature = float(data.get("temperature", 0.4))
        max_tokens = int(data.get("max_tokens", 3000))

        temperature = max(0, min(temperature, 2))
        max_tokens = max(64, min(max_tokens, 8192))

        mode = data.get("mode", "both")

        if mode not in ("both", "theory", "solve", "practice"):
            mode = "both"

        respuesta = consultar_ia(
            messages=messages,
            model=model,
            mode=mode,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return jsonify({
            "success": True,
            "reply": respuesta,
            "model": model
        })

    except Exception as error:
        print(f"Error en Ferdi IA: {error}")

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


if __name__ == "__main__":
    print("=" * 45)
    print("FERDI IA")
    print("Tutor de Física de Corriente Alterna")
    print("=" * 45)
    print("Servidor: http://127.0.0.1:8000")
    print("Estado: iniciado")

    app.run(
        host="127.0.0.1",
        port=8000,
        debug=False
    )
