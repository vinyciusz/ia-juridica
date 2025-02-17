from fastapi import FastAPI, HTTPException
import uvicorn
import os
from database import inserir_regra_juridica  # Mantendo apenas essa importação

app = FastAPI()

@app.get("/")
def home():
    return {"mensagem": "API da IA Jurídica rodando na nuvem!"}

@app.post("/adicionar-regra")
def adicionar_regra(titulo: str, descricao: str):
    """Endpoint para adicionar uma nova regra jurídica"""
    try:
        nova_regra = inserir_regra_juridica(titulo, descricao)
        return {"mensagem": "Regra jurídica adicionada com sucesso!", "regra": nova_regra}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Configuração correta da porta no Railway
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # Mantendo a porta 8080
    uvicorn.run(app, host="0.0.0.0", port=port)
