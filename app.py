
from flask import Flask, request, jsonify
import requests
import openai

app = Flask(__name__)

# Configurações - Substitua pelos seus dados
ZAPI_TOKEN = '06494CCF4713B1147443184B'
ZAPI_PHONE_ID = '5577998535209'
OPENAI_API_KEY = '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'

openai.api_key = OPENAI_API_KEY

# Prompt seguro para restringir as respostas
PROMPT_SISTEMA = (
    "Você é um assistente virtual médico do Dr. Rafael Silva, urologista. "
    "Responda apenas sobre locais de atendimento, orientações pós-operatórias e cuidados médicos básicos. "
    "Se a pergunta não estiver relacionada a esses temas, oriente o paciente a entrar em contato com o consultório."
)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("DEBUG - Recebido:", data)  # <-- Adiciona esse log para ver o que chega

    # Tenta acessar as chaves mais básicas
    if 'message' in data:
        mensagem = data['message']['body']
        numero = data['message']['from']
    elif 'data' in data:
        mensagem = data['text']['message']
        numero = data['phone']
    elif 'body' in data and 'phone' in data:
        mensagem = data['body']
        numero = data['phone']
    else:
        mensagem = "Mensagem não reconhecida"
        numero = "Número não reconhecido"

    # ... (segue igual com o resto do código)


    # Chamada à OpenAI
    resposta_gpt = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": mensagem}
        ]
    )

    resposta_final = resposta_gpt['choices'][0]['message']['content']

    # Enviar resposta pelo WhatsApp (Z-API)
    url = f'https://api.z-api.io/instances/{ZAPI_PHONE_ID}/token/{ZAPI_TOKEN}/send-text'
    payload = {
        'phone': numero,
        'message': resposta_final
    }
    requests.post(url, json=payload)

    return jsonify({'status': 'mensagem enviada'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
