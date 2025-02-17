from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import inserir_regra_juridica  # Certifique-se que esse arquivo existe

# Criar a API apenas UMA vez
app = FastAPI()

# Modelo de dados para validação do JSON recebido
class RegraJuridica(BaseModel):
    titulo: str
    descricao: str

# Rota de teste para saber se a API está rodando
@app.get("/")
def home():
    return {"mensagem": "API da IA Jurídica rodando na nuvem!"}

# Rota para adicionar regra jurídica
@app.post("/adicionar-regra")
def adicionar_regra(regra: RegraJuridica):
    """Endpoint para adicionar uma nova regra jurídica"""
    try:
        nova_regra = inserir_regra_juridica(regra.titulo, regra.descricao)
        return {"mensagem": "Regra jurídica adicionada com sucesso!", "regra": nova_regra}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
