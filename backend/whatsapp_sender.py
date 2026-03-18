import requests
import re

WHATSAPP_TOKEN = "SEU_TOKEN_AQUI"
PHONE_NUMBER_ID = "SEU_PHONE_ID"
DESTINO = "55SEUNUMERO"  # número que vai receber os leads


def clean_phone(phone):
    """Remove tudo que não é número"""
    return re.sub(r"\D", "", phone)


def format_message(lead):
    """Monta mensagem profissional"""
    telefone = clean_phone(lead.get("telefone", ""))

    mensagem = f"""
🚀 NOVO LEAD - CIDADANIA ITALIANA

👤 Nome: {lead.get('nome', '-')}
📞 Telefone: {telefone}
📍 Cidade: {lead.get('cidade', '-')}

🔥 Lead pronto para contato imediato
"""

    return mensagem.strip()


def send_whatsapp(lead):
    """Envia mensagem via WhatsApp Cloud API"""

    mensagem = format_message(lead)

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": DESTINO,
        "type": "text",
        "text": {"body": mensagem}
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            print("✅ WhatsApp enviado com sucesso")
            return True
        else:
            print("❌ Erro ao enviar WhatsApp")
            print(response.text)
            return False

    except Exception as e:
        print("❌ Falha na conexão WhatsApp:", str(e))
        return False