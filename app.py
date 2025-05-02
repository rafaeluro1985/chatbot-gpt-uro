from flask import Flask, request, jsonify
import requests
from openai import OpenAI
import os  # para acessar variáveis de ambiente

app = Flask(__name__)

# Configurações - Pegando dados das variáveis de ambiente
ZAPI_TOKEN = os.environ.get('ZAPI_TOKEN')
ZAPI_PHONE_ID = os.environ.get('ZAPI_PHONE_ID')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

client = OpenAI(
    api_key=OPENAI_API_KEY,
    project="proj_MwQwbc8w6NFUqAMOaLtXBpUt"  # Coloque seu Project ID real aqui
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
