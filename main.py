from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import uvicorn
import os
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from database import inserir_regra_juridica, listar_todas_regras  # Mantendo importações necessárias
import re
import requests

# ✅ Configuração do Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_NUMBER:
    print("❌ ERRO: Variáveis do Twilio não configuradas corretamente!")
    exit(1)

# ✅ Inicializando FastAPI
app = FastAPI()

# ✅ Modelo Pydantic para validação de regras jurídicas
class RegraJuridica(BaseModel):
    titulo: str
    descricao: str

# 🏠 Endpoint de boas-vindas
@app.get("/")
def home():
    return {"mensagem": "🚀 API da IA Jurídica rodando na nuvem!"}

# 📜 Adicionar uma nova regra jurídica
@app.post("/adicionar-regra")
def adicionar_regra(regra: RegraJuridica):
    try:
        nova_regra = inserir_regra_juridica(regra.titulo, regra.descricao)
        return {"mensagem": "📌 Regra jurídica adicionada com sucesso!", "regra": nova_regra}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📜 Listar todas as regras jurídicas
@app.get("/listar-regras")
def listar_regras():
    try:
        regras = listar_todas_regras()
        return {"regras": regras}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📂 Upload e processamento de documentos
@app.post("/upload-documento")
async def upload_documento(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith((".pdf", ".png", ".jpg", ".jpeg")):
            raise HTTPException(status_code=400, detail="⚠️ Formato de arquivo não suportado. Envie um PDF ou imagem!")

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

# 🧹 Função para limpar texto extraído do OCR
def limpar_texto_extraido(texto):
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto).strip()

# ✅ Webhook para WhatsApp (Twilio)
@app.post("/webhook-whatsapp")
async def webhook_whatsapp(
    Body: str = Form(...),
    From: str = Form(...)
):
    try:
        if not Body:
            return {"status": "⚠️ Nenhuma mensagem recebida"}

        mensagem = Body.strip().lower()
        numero_remetente = From.strip()

        resposta = processar_mensagem(mensagem)

        if not resposta:
            resposta = "🤔 Não entendi. Digite *ajuda* para ver os comandos disponíveis."

        sucesso = enviar_mensagem(numero_remetente, resposta)

        if sucesso:
            return {"status": "✅ Mensagem processada!"}
        else:
            return {"status": "⚠️ Erro ao enviar resposta"}

    except Exception as e:
        return {"status": f"❌ Erro ao processar mensagem: {str(e)}"}

# 📤 Função para enviar mensagens via Twilio
def enviar_mensagem(telefone, mensagem):
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
        data = {
            "From": f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            "To": telefone,
            "Body": mensagem
        }
        auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        response = requests.post(url, data=data, auth=auth)

        if response.status_code == 201:
            return True
        else:
            return False

    except Exception as e:
        return False

# ✅ Processamento de mensagens do WhatsApp
def processar_mensagem(mensagem):
    if mensagem in ["oi", "olá", "bom dia"]:
        return "👋 Olá! Eu sou a IA Jurídica. Como posso te ajudar?\nDigite *ajuda* para ver os comandos disponíveis."
    
    elif mensagem == "ajuda":
        return "📌 Comandos disponíveis:\n1️⃣ *Regras* - Listar regras jurídicas\n2️⃣ *Consultar [termo]* - Buscar regras\n3️⃣ *Enviar documento* - Enviar um documento para análise."
    
    elif mensagem.startswith("consultar "):
        termo = mensagem.replace("consultar ", "")
        regras = listar_todas_regras()
        if regras:
            return f"🔎 Regras encontradas:\n" + "\n".join([f"- {r['titulo']}" for r in regras])
        return "⚠️ Nenhuma regra encontrada para esse termo."
    
    elif mensagem == "regras":
        regras = listar_todas_regras()
        return f"📜 Regras disponíveis:\n" + "\n".join([f"- {r['titulo']}" for r in regras])

    return "🤔 Não entendi. Digite *ajuda* para ver os comandos disponíveis."

# ✅ Configuração da porta correta para Railway
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
