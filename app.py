import os
import logging
from flask import Flask, request, jsonify
import requests
from openai import OpenAI

# Configuração do logger para facilitar debug
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# 🔑 Pega as variáveis de ambiente
WATI_API_URL = os.environ.get('WATI_API_URL')
WATI_API_KEY = os.environ.get('WATI_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_PROJECT_ID = os.environ.get('OPENAI_PROJECT_ID')  # Opcional

# 🔍 Validação: se faltar algo, para tudo com erro claro
if not WATI_API_URL or not WATI_API_KEY:
    raise ValueError("Erro: Variáveis de ambiente WATI_API_URL e/ou WATI_API_KEY não estão definidas.")
if not OPENAI_API_KEY:
    raise ValueError("Erro: Variável de ambiente OPENAI_API_KEY não está definida.")

logging.info(f"WATI_API_URL carregado: {WATI_API_URL}")

# 🔗 Configuração do cliente OpenAI
client = OpenAI(
    api_key=OPENAI_API_KEY,
    project=OPENAI_PROJECT_ID  # OK se for None
)

# Prompt do sistema para restringir as respostas
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
    except (KeyError, TypeError):
        logging.error("Erro: Estrutura inesperada no payload recebido.")
        return jsonify({'status': 'estrutura inesperada'}), 400

    logging.info("Chamando OpenAI para gerar resposta...")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": mensagem}
            ]
        )
        resposta_final = response.choices[0].message.content.strip()
        logging.info(f"Resposta da OpenAI: {resposta_final}")

    except Exception as e:
        logging.error(f"Erro na API OpenAI: {str(e)}")
        return jsonify({'status': 'erro na geração de resposta'}), 500

    # Enviar a resposta via WATI
    payload = {
        'phone': numero,  # Ex: 557799999999
        'message': resposta_final
    }

    headers = {
        'Authorization': f'Bearer {WATI_API_KEY}',
        'Content-Type': 'application/json'
    }

    wati_endpoint = f"{WATI_API_URL}/sendSessionMessage"
    logging.info(f"Enviando resposta para o WhatsApp via WATI: {payload}")

    try:
        response_wati = requests.post(wati_endpoint, json=payload, headers=headers)
        logging.info(f"WATI status code: {response_wati.status_code}")
        logging.info(f"WATI response text: {response_wati.text}")
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem para WATI: {str(e)}")
        return jsonify({'status': 'erro ao enviar para WATI'}), 500

    return jsonify({'status': 'mensagem enviada'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
