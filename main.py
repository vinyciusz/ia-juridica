from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import uvicorn
import os
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from database import inserir_regra_juridica, listar_todas_regras
import re
import requests

# ✅ Configuração do Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# ✅ Inicializando FastAPI
app = FastAPI()

# ✅ Modelo para Regras Jurídicas
class RegraJuridica(BaseModel):
    titulo: str
    descricao: str

# ✅ Endpoint de Boas-Vindas
@app.get("/")
def home():
    return {"mensagem": "🚀 API da IA Jurídica rodando na nuvem!"}

# ✅ Adicionar Regra Jurídica
@app.post("/adicionar-regra")
def adicionar_regra(regra: RegraJuridica):
    try:
        nova_regra = inserir_regra_juridica(regra.titulo, regra.descricao)
        
        # Garantir que a regra adicionada está formatada corretamente
        if isinstance(nova_regra, tuple):  
            nova_regra = {"id": nova_regra[0], "titulo": nova_regra[1], "descricao": nova_regra[2]}

        return {"mensagem": "📌 Regra jurídica adicionada com sucesso!", "regra": nova_regra}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Listar Regras Jurídicas
@app.get("/listar-regras")
def listar_regras():
    try:
        regras = listar_todas_regras()
        
        # Garantir que as regras estão formatadas corretamente como dicionários
        regras_formatadas = [{"id": r[0], "titulo": r[1], "descricao": r[2]} for r in regras]

        return {"regras": regras_formatadas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Teste de Conexão com o Banco de Dados
@app.get("/testar-conexao")
def testar_conexao():
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        return {"mensagem": "✅ Conexão bem-sucedida!", "resultado": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Falha na conexão com o banco de dados.")

# ✅ Upload e Processamento de Documentos
@app.post("/upload-documento")
async def upload_documento(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith((".pdf", ".png", ".jpg", ".jpeg")):
            raise HTTPException(status_code=400, detail="⚠️ Formato de arquivo não suportado. Envie um PDF ou imagem!")

        # Converte PDF para Imagem, se necessário
        if file.filename.endswith(".pdf"):
            imagens = convert_from_bytes(await file.read())
            texto_extraido = "\n".join([pytesseract.image_to_string(img) for img in imagens])
        else:
            imagem = Image.open(file.file)
            texto_extraido = pytesseract.image_to_string(imagem)

        texto_limpo = limpar_texto_extraido(texto_extraido)

        return {"mensagem": "📄 Documento processado com sucesso!", "texto": texto_limpo}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao processar o documento.")

# ✅ Configuração correta da porta no Railway
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
