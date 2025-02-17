from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
from database import inserir_regra_juridica, listar_todas_regras  # Certifique-se de que listar_todas_regras está implementado corretamente

app = FastAPI()

# ✅ Definição do modelo Pydantic para validação dos dados enviados via JSON
class RegraJuridica(BaseModel):
    titulo: str
    descricao: str

@app.get("/")
def home():
    return {"mensagem": "API da IA Jurídica rodando na nuvem!"}

# ✅ Agora recebendo os dados via JSON no body
@app.post("/adicionar-regra")
def adicionar_regra(regra: RegraJuridica):
    """Endpoint para adicionar uma nova regra jurídica"""
    try:
        nova_regra = inserir_regra_juridica(regra.titulo, regra.descricao)
        return {"mensagem": "Regra jurídica adicionada com sucesso!", "regra": nova_regra}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/listar-regras")
def listar_regras():
    """Endpoint para listar todas as regras jurídicas"""
    try:
        regras = listar_todas_regras()
        return {"regras": regras}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Configuração correta da porta no Railway (NÃO ALTERAR)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # Mantendo a porta 8080
    uvicorn.run(app, host="0.0.0.0", port=port)

@app.post("/adicionar-regra")
def adicionar_regra(titulo: str, descricao: str):
    """Endpoint para adicionar uma nova regra jurídica"""
    try:
        print(f"Tentando inserir regra: {titulo} - {descricao}")  # Log para verificar entrada
        nova_regra = inserir_regra_juridica(titulo, descricao)
        print(f"Regra inserida com sucesso: {nova_regra}")  # Log para verificar sucesso
        return {"mensagem": "Regra jurídica adicionada com sucesso!", "regra": nova_regra}
    except Exception as e:
        print(f"Erro ao inserir regra: {e}")  # Log para capturar erro
        raise HTTPException(status_code=500, detail=str(e))
