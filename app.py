from flask import Flask, request, jsonify
import requests
from openai import OpenAI
import os

app = Flask(__name__)

# Configurações - Pegando dados das variáveis de ambiente
WATI_API_URL = os.environ.get('WATI_API_URL')  # Ex: https://live-server.wati.io/api/v1/sendSessionMessage
WATI_API_KEY = os.environ.get('WATI_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

client = OpenAI(
    api_key=OPENAI_API_KEY,
    project=os.environ.get('OPENAI_PROJECT_ID')  # Opcional, só use se estiver usando o Project ID
)

# Prompt seguro para restringir as respostas
PROMPT_SISTEMA = (
    "Você é um assistente virtual médico do Dr. Rafael Silva, urologista. "
    "Responda apenas sobre locais de atendimento, orientações pós-operatórias e cuidados médicos básicos. "
    "Se a pergunta não estiver relacionada a esses temas, oriente o paciente a entrar em contato com o consultório."
)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("DEBUG - Recebido:", data)

    try:
        mensagem = data['text']['message']
        numero = data['phone']
    except KeyError:
        print("DEBUG - Estrutura inesperada:", data)
        return jsonify({'status': 'estrutura inesperada'}), 400

    # Chamada atualizada para OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": mensagem}
        ]
    )

    resposta_final = response.choices[0].message.content

    # Enviar resposta pelo WhatsApp (WATI)
    headers = {
        'Authorization': f'Bearer {WATI_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'phone': numero,  # Deve estar no formato internacional, ex: 5571999999999
        'message': resposta_final
    }

    response_wati = requests.post(WATI_API_URL, json=payload, headers=headers)
    print("DEBUG - WATI status code:", response_wati.status_code)
    print("DEBUG - WATI response text:", response_wati.text)

    return jsonify({'status': 'mensagem enviada'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
