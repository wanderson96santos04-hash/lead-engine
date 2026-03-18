from fastapi import FastAPI, Form
from backend.lead_manager import save_lead

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Lead Engine Running"}

@app.post("/lead")
def receive_lead(
    nome: str = Form(...),
    telefone: str = Form(...),
    cidade: str = Form(...)
):
    
    lead = {
        "nome": nome,
        "telefone": telefone,
        "cidade": cidade
    }

    save_lead(lead)

    return {"message": "Lead recebido com sucesso"}