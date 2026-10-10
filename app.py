
import os
import json
import urllib.request
import urllib.error
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"

@app.get("/")
def home():
    return jsonify({
        "app": "M.E Duda AI",
        "status": "online"
    })

@app.post("/chat")
def chat():
    if not API_KEY:
        return jsonify({"error": "Servidor sem chave configurada."}), 503

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Digite uma mensagem."}), 400

    if len(message) > 4000:
        return jsonify({"error": "Mensagem muito longa."}), 400

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + MODEL + ":generateContent"
    )

    payload = {
        "system_instruction": {
            "parts": [{
                "text": (
                    "Seu nome é Duda, uma inteligência artificial brasileira, "
                    "amigável, inteligente e criativa. Responda sempre em "
                    "português brasileiro. Ajude com estudos de Direito usando "
                    "explicações simples e exemplos. Ajude também com escrita, "
                    "organização, tecnologia e tarefas do cotidiano. Seja "
                    "paciente. Se não souber algo, admita e não invente leis "
                    "nem fontes."
                )
            }]
        },
        "contents": [{
            "role": "user",
            "parts": [{"text": message}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 512
        }
    }

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
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        answer = result["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify({"reply": answer})

    except urllib.error.HTTPError as error:
        print("Gemini HTTP error:", error.code)
        return jsonify({
            "error": "O serviço de IA recusou a solicitação. Verifique a configuração da API."
        }), 502

    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError):
        return jsonify({
            "error": "Não foi possível obter uma resposta da IA. Tente novamente."
        }), 502
