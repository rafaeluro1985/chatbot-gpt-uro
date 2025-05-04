from flask import Flask, request, jsonify
import requests
import logging
import os

from openai import OpenAI

app = Flask(__name__)

# Configurações - Pegando dados das variáveis de ambiente
WATI_API_URL = os.environ.get('WATI_API_URL')  # Exemplo: https://live-server.wati.io/api/v1/sendSessionMessage
WATI_API_KEY = os.environ.get('WATI_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

client = OpenAI(
    api_key=OPENAI_API_KEY,
    project=os.environ.get('OPENAI_PROJECT_ID')  # Opcional, use se tiver o Project ID
)

# Prompt seguro para restringir as respostas
PROMPT_SISTEMA = (
    "Você é um assistente virtual médico do Dr. Rafael Silva, urologista. "
    "Responda apenas sobre locais de atendimento, orientações pós-operatórias e cuidados médicos básicos. "
    "Se a pergunta não estiver relacionada a esses temas, oriente o paciente a entrar em contato com o consultório."
)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    logging.info(f"Webhook recebido: {data}")

    try:
        # Pegando a mensagem (tratando se vier como dict ou string)
        mensagem_obj = data.get('text')
        numero = data.get('waId') or data.get('phone')

        if not mensagem_obj or not numero:
            raise KeyError("Estrutura de dados incompleta: 'text' ou 'waId'/'phone' ausente.")

        # Aqui é o ponto principal da correção 👇
        mensagem = mensagem_obj.get('message') if isinstance(mensagem_obj, dict) else mensagem_obj

    except (KeyError, TypeError, AttributeError) as e:
        logging.error(f"Erro ao processar payload do webhook: {e}. Payload: {data}")
        return jsonify({'status': 'erro ao processar payload', 'error': str(e)}), 400

    # Chamada para a API da OpenAI
    try:
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

    except Exception as e:
        logging.error(f"Erro na API OpenAI: {e}")
        return jsonify({'status': 'erro ao gerar resposta', 'error': str(e)}), 500

    # Enviar resposta pelo WhatsApp (WATI)
    headers = {
        'Authorization': f'Bearer {WATI_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'phone': numero,  # Deve estar no formato internacional, ex: 5571999999999
        'message': resposta_final
    }

    try:
        logging.info(f"Enviando resposta para o WhatsApp via WATI: {payload}")
        response_wati = requests.post(WATI_API_URL, json=payload, headers=headers)
        logging.info(f"WATI status code: {response_wati.status_code}")
        logging.info(f"WATI response text: {response_wati.text}")

        if response_wati.status_code not in (200, 201):
            raise Exception(f"Erro ao enviar mensagem via WATI: {response_wati.text}")

    except Exception as e:
        logging.error(f"Erro ao enviar mensagem para WATI: {e}")
        return jsonify({'status': 'erro ao enviar mensagem', 'error': str(e)}), 500

    return jsonify({'status': 'mensagem enviada com sucesso'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
