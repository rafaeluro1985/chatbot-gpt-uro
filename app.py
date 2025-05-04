from flask import Flask, request, jsonify
import requests
from openai import OpenAI, APIError  # Import APIError
import os
import logging

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configurações - Pegando dados das variáveis de ambiente
WATI_API_KEY = os.environ.get('WATI_API_KEY')
WATI_BASE_URL = os.environ.get('WATI_BASE_URL')  # Exemplo: https://live-mt-server.wati.io/437995
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Validação inicial das variáveis de ambiente essenciais
if not WATI_API_KEY or not WATI_BASE_URL or not OPENAI_API_KEY:
    logging.error("Erro: Variáveis de ambiente WATI_API_KEY, WATI_BASE_URL ou OPENAI_API_KEY não configuradas.")

try:
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        project=os.environ.get('OPENAI_PROJECT_ID')  # Opcional
    )
except Exception as e:
    logging.error(f"Erro ao inicializar cliente OpenAI: {e}")

# Prompt seguro para restringir as respostas
PROMPT_SISTEMA = (
    "Você é um assistente virtual médico do Dr. Rafael Silva, urologista. "
    "Responda apenas sobre locais de atendimento, orientações pós-operatórias e cuidados médicos básicos relacionados à urologia. "
    "Se a pergunta não estiver relacionada a esses temas, informe educadamente que você só pode responder sobre esses assuntos específicos e sugira entrar em contato com o consultório para outras questões."
)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    logging.info(f"Webhook recebido: {data}")

    try:
        mensagem = data.get('text')  # WATI geralmente envia a mensagem direto na chave 'text'
        numero = data.get('waId') or data.get('phone')  # waId é mais comum

        if not mensagem or not numero:
            raise KeyError("Estrutura de dados incompleta: 'text' ou 'waId'/'phone' ausente.")

    except (KeyError, TypeError) as e:
        logging.error(f"Erro ao processar payload do webhook: {e}. Payload: {data}")
        return jsonify({'status': 'erro ao processar payload', 'error': str(e)}), 400

    # Chamada para a API OpenAI com tratamento de erro
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": mensagem}
            ]
        )
        resposta_final = response.choices[0].message.content
        logging.info(f"Resposta gerada pela OpenAI para {numero}: {resposta_final}")

    except APIError as e:
        logging.error(f"Erro na API OpenAI: {e}")
        return jsonify({'status': 'erro na API OpenAI', 'error': str(e)}), 500
    except Exception as e:
        logging.error(f"Erro inesperado ao chamar OpenAI: {e}")
        return jsonify({'status': 'erro interno no servidor', 'error': str(e)}), 500

    # Enviar resposta pelo WhatsApp (WATI)
    headers = {
        'Authorization': f'Bearer {WATI_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'messageText': resposta_final
    }

    wati_url = f"{WATI_BASE_URL}/api/v1/sendSessionMessage/{numero}"

    try:
        response_wati = requests.post(wati_url, json=payload, headers=headers, timeout=10)
        response_wati.raise_for_status()

        logging.info(f"Resposta enviada via WATI para {numero}. Status: {response_wati.status_code}")
        return jsonify({'status': 'mensagem enviada com sucesso'}), 200

    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao enviar mensagem via WATI para {numero}: {e}. URL: {wati_url}")
        return jsonify({'status': 'erro ao enviar via WATI', 'error': str(e)}), 502

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
