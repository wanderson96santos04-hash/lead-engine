from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from datetime import datetime
import os
import requests

app = FastAPI()

# =========================
# 🔥 NOVO (não quebra nada)
# =========================
@app.get("/")
async def root():
    return {"status": "ok"}

@app.head("/")
async def root_head():
    return {"status": "ok"}

@app.head("/lead")
async def lead_head():
    return {"status": "ok"}
# =========================


# Modelo do lead
class Lead(BaseModel):
    name: str
    phone: str


# Criar banco se não existir
def init_db():
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


# Endpoint principal (NÃO ALTERADO)
@app.post("/lead")
async def create_lead(lead: Lead):
    print("📩 NOVO LEAD:", lead)

    # Salvar no banco
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leads (name, phone, created_at) VALUES (?, ?, ?)",
        (lead.name, lead.phone, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    # =========================
    # ENVIO WHATSAPP
    # =========================
    try:
        message = f"Novo lead - Cidadania Italiana\n\nNome: {lead.name}\nTelefone: {lead.phone}"
        url = f"https://api.whatsapp.com/send?phone=5533999149440&text={message}"
        print("📲 WhatsApp URL:", url)
    except Exception as e:
        print("❌ Erro WhatsApp:", e)

    # =========================
    # ENVIO EMAIL (BREVO)
    # =========================
    try:
        BREVO_API_KEY = os.getenv("BREVO_API_KEY")

        if BREVO_API_KEY:
            headers = {
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json"
            }

            data = {
                "sender": {"email": "seuemail@gmail.com"},
                "to": [{"email": "seuemail@gmail.com"}],
                "subject": "Novo Lead - Cidadania Italiana",
                "htmlContent": f"""
                    <h3>Novo Lead</h3>
                    <p><strong>Nome:</strong> {lead.name}</p>
                    <p><strong>Telefone:</strong> {lead.phone}</p>
                """
            }

            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                json=data,
                headers=headers
            )

            print("📧 Email enviado:", response.status_code)
        else:
            print("⚠️ Email não configurado")
    except Exception as e:
        print("❌ Erro Email:", e)

    return {"status": "ok"}