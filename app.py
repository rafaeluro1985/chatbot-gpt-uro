from flask import Flask, request, jsonify
import requests
import logging
import os
from openai import OpenAI

# Configuração básica do app Flask
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Variáveis de ambiente
WATI_API_URL = os.environ.get('WATI_API_URL')  # EX: https://app-server.wati.io/api/v1
WATI_API_KEY = os.environ.get('WATI_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)

PROMPT_SISTEMA = (
    "Você é um assistente virtual médico do Dr. Rafael Silva, urologista. "
    "Responda apenas sobre locais de atendimento, orientações pós-operatórias e cuidados médicos básicos. "
    "Se a pergunta não estiver relacionada a esses temas, oriente o paciente a entrar em contato com o consultório."
)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    logging.info(f"Webhook recebido: {data}")

    try:
        mensagem = data['text']['message']
        numero = data['phone']
    except KeyError:
        logging.error(f"Estrutura inesperada: {data}")
        return jsonify({'status': 'estrutura inesperada'}), 400

    # Chamada OpenAI
    logging.info("Chamando OpenAI para gerar resposta...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": mensagem}
        ]
    )
    resposta_final = response.choices[0].message.content
    logging.info(f"Resposta da OpenAI: {resposta_final}")

    # Enviar para WhatsApp (Session Message)
    url = f"{WATI_API_URL}/sendSessionMessage"
    headers = {
        'Authorization': f'Bearer {WATI_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'phone': numero,
        'message': resposta_final
    }
    logging.info(f"Enviando resposta para o WhatsApp via WATI: {payload}")
    response_wati = requests.post(url, json=payload, headers=headers)

    if response_wati.status_code != 200:
        logging.error(f"Erro ao enviar mensagem para WATI: {response_wati.text}")
        return jsonify({'status': 'erro ao enviar para WATI'}), 500

    return jsonify({'status': 'mensagem enviada'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
