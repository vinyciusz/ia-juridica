from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uvicorn
import os
from database import SessionLocal, init_db, RegraJuridica

# Iniciar o banco de dados no Railway
init_db()

# Criar a API
app = FastAPI()

# Criar a conexão com o banco de dados em cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Definir o modelo de entrada
class RegraJuridicaSchema(BaseModel):
    titulo: str
    descricao: str

@app.get("/")
def home():
    return {"mensagem": "API da IA Jurídica rodando na nuvem!"}

# Criar regra jurídica e salvar no PostgreSQL
@app.post("/adicionar-regra")
def adicionar_regra(regra: RegraJuridicaSchema, db: Session = Depends(get_db)):
    """Endpoint para adicionar uma nova regra jurídica"""
    try:
        nova_regra = RegraJuridica(titulo=regra.titulo, descricao=regra.descricao)
        db.add(nova_regra)
        db.commit()
        db.refresh(nova_regra)
        return {"mensagem": "Regra jurídica adicionada com sucesso!", "regra": nova_regra}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # Railway usa a porta 8080
    uvicorn.run(app, host="0.0.0.0", port=port)
