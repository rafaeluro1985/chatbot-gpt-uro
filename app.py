
from flask import Flask, request, jsonify
import requests
import openai

app = Flask(__name__)

# Configurações - Substitua pelos seus dados
ZAPI_TOKEN = 'SEU_TOKEN_ZAPI'
ZAPI_PHONE_ID = 'SEU_PHONE_ID'  # Exemplo: '5531999999999'
OPENAI_API_KEY = 'SUA_OPENAI_API_KEY'

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
    mensagem = data['message']['body']
    numero = data['message']['from']

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
