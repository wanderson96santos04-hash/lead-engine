import os
import re
import sqlite3
import requests
import smtplib

from datetime import datetime
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO", "")


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
    return f"""NOVO LEAD - CIDADANIA ITALIANA

Nome: {lead_data.get("name", "-")}
Telefone: {lead_data.get("phone", "-")}
Sobrenome italiano na família: {lead_data.get("surname_italian", "-")}
Antepassado nasceu na Itália: {lead_data.get("ancestor_born_italy", "-")}
Documentos da família: {lead_data.get("family_documents", "-")}
Estado: {lead_data.get("state", "-")}
Data: {lead_data.get("created_at", "-")}

Lead qualificado pronto para contato
""".strip()


def send_whatsapp(lead_data: dict) -> bool:
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID or not WHATSAPP_DESTINO:
        print("WhatsApp não configurado. Pulando envio.")
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
            print("WhatsApp enviado com sucesso")
            return True

        print("Erro ao enviar WhatsApp")
        print(response.text)
        return False

    except Exception as e:
        print("Falha WhatsApp:", str(e))
        return False


def send_email(lead_data: dict) -> bool:
    if not SMTP_USER or not SMTP_PASSWORD or not EMAIL_DESTINO:
        print("Email não configurado. Pulando envio.")
        return False

    assunto = "Novo Lead Qualificado - Cidadania Italiana"
    corpo = format_lead_message(lead_data)

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = EMAIL_DESTINO
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo, "plain", "utf-8"))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, EMAIL_DESTINO, msg.as_string())
        server.quit()

        print("Email enviado com sucesso")
        return True

    except Exception as e:
        print("Falha Email:", str(e))
        return False


init_db()


@app.get("/")
def healthcheck():
    return {"status": "ok"}


@app.post("/lead")
def receive_lead(lead: Lead):
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
    email_ok = send_email(lead_data)

    print("NOVO LEAD:", lead_data)
    print(f"Envio WhatsApp: {whatsapp_ok} | Envio Email: {email_ok}")

    return {
        "status": "success",
        "whatsapp_sent": whatsapp_ok,
        "email_sent": email_ok,
    }