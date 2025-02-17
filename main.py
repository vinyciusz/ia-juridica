from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os

# Definição do modelo de entrada
class RegraJuridica(BaseModel):
    titulo: str
    descricao: str

app = FastAPI()

@app.get("/")
def home():
    return {"mensagem": "API da IA Jurídica rodando na nuvem!"}

@app.post("/adicionar-regra")
def adicionar_regra(regra: RegraJuridica):
    """Endpoint para adicionar uma nova regra jurídica"""
    try:
        # Simulação da inserção no banco
        nova_regra = {"titulo": regra.titulo, "descricao": regra.descricao}
        return {"mensagem": "Regra jurídica adicionada com sucesso!", "regra": nova_regra}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # Railway usa a porta 8080
    uvicorn.run(app, host="0.0.0.0", port=port)
