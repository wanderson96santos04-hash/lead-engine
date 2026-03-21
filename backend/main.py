import os
import re
import sqlite3
import requests
import logging

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("lead-engine")

app = FastAPI()

FRONTEND_ORIGINS = [
    "https://analisecidadaniaitaliana.com",
    "https://www.analisecidadaniaitaliana.com",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "leads.db")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
WHATSAPP_DESTINO = os.getenv("WHATSAPP_DESTINO", "")

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_API_KEY = (os.getenv("BREVO_API_KEY") or "").strip()
EMAIL_FROM = (os.getenv("EMAIL_FROM") or "").strip()
EMAIL_FROM_NAME = (os.getenv("EMAIL_FROM_NAME") or "Análise Cidadania Italiana").strip()
EMAIL_TO = (os.getenv("EMAIL_TO") or "").strip()
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))


class QuizAnswers(BaseModel):
    surname_italian: Optional[str] = ""
    ancestor_born_italy: Optional[str] = ""
    family_documents: Optional[str] = ""
    state: Optional[str] = ""


class Lead(BaseModel):
    name: str
    phone: str
    quiz_answers: Optional[QuizAnswers] = None


def get_connection():
    return sqlite3.connect(DB)


def ensure_column(cursor, column_name, column_type):
    cursor.execute("PRAGMA table_info(leads)")
    columns = [column[1] for column in cursor.fetchall()]

    if column_name not in columns:
        cursor.execute(f"ALTER TABLE leads ADD COLUMN {column_name} {column_type}")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            created_at TEXT
        )
        """
    )

    ensure_column(cursor, "surname_italian", "TEXT")
    ensure_column(cursor, "ancestor_born_italy", "TEXT")
    ensure_column(cursor, "family_documents", "TEXT")
    ensure_column(cursor, "state", "TEXT")

    conn.commit()
    conn.close()


def clean_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")


def format_lead_message(lead_data: dict) -> str:
    return f"""Novo Lead - Cidadania Italiana

Nome: {lead_data.get("name", "-")}
Telefone: {lead_data.get("phone", "-")}
Quando gostaria de iniciar: {lead_data.get("surname_italian", "-")}
Interesse em investir entre R$5.000 e R$20.000: {lead_data.get("ancestor_born_italy", "-")}
Documentos ou informações sobre antepassados: {lead_data.get("family_documents", "-")}
Deseja ajuda de um especialista: {lead_data.get("state", "-")}
Data: {lead_data.get("created_at", "-")}
""".strip()


def log_email_config_status():
    logger.info(
        "EMAIL CONFIG | BREVO_API_KEY=%s | EMAIL_FROM=%s | EMAIL_TO=%s | EMAIL_TIMEOUT=%s",
        "OK" if BREVO_API_KEY else "MISSING",
        "OK" if EMAIL_FROM else "MISSING",
        "OK" if EMAIL_TO else "MISSING",
        EMAIL_TIMEOUT,
    )


def send_whatsapp(lead_data: dict) -> bool:
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID or not WHATSAPP_DESTINO:
        logger.info("WhatsApp não configurado. Pulando envio.")
        return False

    mensagem = format_lead_message(lead_data)
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    data = {
        "messaging_product": "whatsapp",
        "to": WHATSAPP_DESTINO,
        "type": "text",
        "text": {"body": mensagem},
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)

        if response.status_code == 200:
            logger.info("WhatsApp enviado com sucesso")
            return True

        logger.error("Erro ao enviar WhatsApp | status=%s | body=%s", response.status_code, response.text)
        return False

    except Exception as e:
        logger.exception("Falha WhatsApp: %s", str(e))
        return False


def send_email_lead(lead_data: dict) -> bool:
    if not BREVO_API_KEY or not EMAIL_FROM or not EMAIL_TO:
        logger.error(
            "Email não configurado. Pulando envio. BREVO_API_KEY=%s EMAIL_FROM=%s EMAIL_TO=%s",
            "OK" if BREVO_API_KEY else "MISSING",
            "OK" if EMAIL_FROM else "MISSING",
            "OK" if EMAIL_TO else "MISSING",
        )
        return False

    subject = "Novo Lead - Cidadania Italiana"
    body_text = format_lead_message(lead_data)
    body_html = f"""
    <html>
        <body>
            <h2>Novo Lead - Cidadania Italiana</h2>
            <p><strong>Nome:</strong> {lead_data.get("name", "-")}</p>
            <p><strong>Telefone:</strong> {lead_data.get("phone", "-")}</p>
            <p><strong>Quando gostaria de iniciar:</strong> {lead_data.get("surname_italian", "-")}</p>
            <p><strong>Interesse em investir entre R$5.000 e R$20.000:</strong> {lead_data.get("ancestor_born_italy", "-")}</p>
            <p><strong>Documentos ou informações sobre antepassados:</strong> {lead_data.get("family_documents", "-")}</p>
            <p><strong>Deseja ajuda de um especialista:</strong> {lead_data.get("state", "-")}</p>
            <p><strong>Data:</strong> {lead_data.get("created_at", "-")}</p>
        </body>
    </html>
    """.strip()

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": EMAIL_FROM_NAME,
            "email": EMAIL_FROM,
        },
        "to": [
            {
                "email": EMAIL_TO,
                "name": "Recebimento de Leads",
            }
        ],
        "subject": subject,
        "textContent": body_text,
        "htmlContent": body_html,
    }

    try:
        response = requests.post(
            BREVO_API_URL,
            headers=headers,
            json=payload,
            timeout=EMAIL_TIMEOUT,
        )

        if response.status_code in (200, 201, 202):
            try:
                result = response.json()
            except Exception:
                result = {}

            logger.info("Email enviado com sucesso | response=%s", result)
            return True

        logger.error(
            "Erro ao enviar email | status=%s | body=%s",
            response.status_code,
            response.text,
        )
        return False

    except requests.RequestException as e:
        logger.exception("Erro ao enviar email: %s", str(e))
        return False


init_db()


@app.on_event("startup")
def startup_event():
    logger.info("Aplicação iniciada com sucesso")
    log_email_config_status()


@app.get("/")
def healthcheck():
    return {"status": "ok"}


@app.post("/lead")
def receive_lead(lead: Lead, background_tasks: BackgroundTasks):
    quiz = lead.quiz_answers or QuizAnswers()

    lead_data = {
        "name": lead.name.strip(),
        "phone": clean_phone(lead.phone.strip()),
        "surname_italian": (quiz.surname_italian or "").strip(),
        "ancestor_born_italy": (quiz.ancestor_born_italy or "").strip(),
        "family_documents": (quiz.family_documents or "").strip(),
        "state": (quiz.state or "").strip(),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO leads (
            name,
            phone,
            surname_italian,
            ancestor_born_italy,
            family_documents,
            state,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead_data["name"],
            lead_data["phone"],
            lead_data["surname_italian"],
            lead_data["ancestor_born_italy"],
            lead_data["family_documents"],
            lead_data["state"],
            lead_data["created_at"],
        ),
    )

    conn.commit()
    conn.close()

    whatsapp_ok = send_whatsapp(lead_data)
    background_tasks.add_task(send_email_lead, lead_data)

    logger.info("NOVO LEAD: %s", lead_data)
    logger.info("Envio WhatsApp: %s | Email agendado: True", whatsapp_ok)

    return {
        "status": "success",
        "whatsapp_sent": whatsapp_ok,
        "email_queued": True,
    }