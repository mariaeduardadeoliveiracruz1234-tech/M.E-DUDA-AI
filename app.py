import os
import json
import base64
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.8-flash"

app.config["MAX_CONTENT_LENGTH"] = 7 * 1024 * 1024

INSTRUCOES = """
Seu nome é Duda. Você é uma inteligência artificial brasileira,
amigável, inteligente e criativa. Responda sempre em português brasileiro.
Ajude com estudos de Direito usando explicações simples e exemplos.
Ajude também com escrita, organização, tecnologia e tarefas do cotidiano.
Se receber uma foto, analise o que realmente consegue observar.
Não invente detalhes que não estejam visíveis.
Se não souber algo, admita e não invente fatos, leis ou fontes.
"""

@app.get("/")
def home():
    return send_from_directory(".", "index.html")


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    image = data.get("image")

    if not message and not image:
        return jsonify({
            "error": "Digite uma mensagem ou envie uma foto."
        }), 400

    if len(message) > 10000:
        return jsonify({
            "error": "A mensagem é muito longa."
        }), 400

    if not API_KEY:
        return jsonify({
            "error": "A chave da API não está configurada no servidor."
        }), 500

    parts = []

    if message:
        parts.append({"text": message})
    elif image:
        parts.append({
            "text": "Analise esta foto e descreva o que consegue observar."
        })

    if image:
        mime_type = image.get("mimeType", "")
        image_data = image.get("data", "")

        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp"
        ]

        if mime_type not in allowed_types:
            return jsonify({
                "error": "Envie uma foto JPG, PNG ou WebP."
            }), 400

        if not isinstance(image_data, str) or not image_data:
            return jsonify({
                "error": "Não consegui ler a foto enviada."
            }), 400

        try:
            decoded_image = base64.b64decode(
                image_data,
                validate=True
            )
        except Exception:
            return jsonify({
                "error": "O arquivo de imagem é inválido."
            }), 400

        if len(decoded_image) > 5 * 1024 * 1024:
            return jsonify({
                "error": "A foto deve ter no máximo 5 MB."
            }), 400

        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": image_data
            }
        })

    payload = {
        "system_instruction": {
            "parts": [{"text": INSTRUCOES}]
        },
        "contents": [{
            "role": "user",
            "parts": parts
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 512
        }
    }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + MODEL
        + ":generateContent"
    )

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        candidates = result.get("candidates", [])

        if not candidates:
            return jsonify({
                "error": "A Gemini não retornou uma resposta. Tente novamente."
            }), 502

        response_parts = (
            candidates[0].get("content", {}).get("parts", [])
        )

        reply = "\n".join(
            part["text"]
            for part in response_parts
            if "text" in part
        ).strip()

        if not reply:
            reply = "Não consegui formular uma resposta. Pode tentar novamente?"

        return jsonify({"reply": reply})

    except urllib.error.HTTPError as error:
        details = error.read().decode(
            "utf-8",
            errors="replace"
        )
        print("Erro da API Gemini:", error.code, details)

        return jsonify({
            "error": "A Gemini apresentou um erro. Verifique os registros do servidor."
        }), 502

    except Exception as error:
        print("Erro ao conversar com a Gemini:", str(error))

        return jsonify({
            "error": "Não foi possível conectar à inteligência artificial."
        }), 502


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "error": "O arquivo enviado é muito grande."
    }), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
