from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, init_db, RegraJuridica

# Inicializando o banco de dados
init_db()

app = FastAPI()

@app.get("/")
def home():
    return {"mensagem": "API da IA Jurídica rodando na nuvem!"}

# Dependência para obter a sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/adicionar-regra")
def adicionar_regra(titulo: str, descricao: str, db: Session = Depends(get_db)):
    """Endpoint para adicionar uma nova regra jurídica"""
    try:
        nova_regra = RegraJuridica(titulo=titulo, descricao=descricao)
        db.add(nova_regra)
        db.commit()
        db.refresh(nova_regra)
        return {"mensagem": "Regra jurídica adicionada com sucesso!", "regra": nova_regra}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/listar-regras")
def listar_regras(db: Session = Depends(get_db)):
    """Endpoint para listar todas as regras jurídicas"""
    regras = db.query(RegraJuridica).all()
    return {"regras": regras}
