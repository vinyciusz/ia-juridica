from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import uvicorn
import os
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from database import inserir_regra_juridica, listar_todas_regras, buscar_regras_juridicas
import re
import requests
from fastapi import Request

# ✅ Configuração do Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_NUMBER:
    print("❌ ERRO: Variáveis do Twilio não configuradas corretamente!")
    exit(1)

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

# ✅ Upload e Processamento de Documentos
@app.post("/upload-documento")
async def upload_documento(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith((".pdf", ".png", ".jpg", ".jpeg")):
            raise HTTPException(status_code=400, detail="⚠️ Formato de arquivo não suportado!")

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
        print(f"❌ ERRO ao processar documento: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar o documento.")

# ✅ Webhook para WhatsApp (Twilio)
@app.post("/webhook-whatsapp")
async def webhook_whatsapp(
    Body: str = Form(...),
    From: str = Form(...)
):
    """📩 Webhook para receber mensagens do WhatsApp"""
    try:
        mensagem = Body.strip().lower()
        numero_remetente = From.strip()

        print(f"📥 Mensagem recebida de {numero_remetente}: {mensagem}")

        # 🔎 Verifica se há uma regra jurídica relacionada ao termo da mensagem
        regras_encontradas = buscar_regras_juridicas(mensagem)

        if regras_encontradas:
            resposta = "📖 Regras encontradas:\n"
            resposta += "\n".join([f"🔹 {r['titulo']}: {r['descricao']}" for r in regras_encontradas])
        else:
            resposta = "⚠️ Nenhuma regra encontrada para esse termo. Consulte um advogado para mais informações."

        # 📤 Enviar resposta para o WhatsApp
        sucesso = enviar_mensagem(numero_remetente, resposta)

        if sucesso:
            return {"status": "✅ Mensagem processada!"}
        else:
            return {"status": "⚠️ Mensagem recebida, mas erro ao enviar resposta"}

    except Exception as e:
        print(f"❌ ERRO no webhook do WhatsApp: {e}")
        return {"status": f"❌ Erro ao processar mensagem: {str(e)}"}

# ✅ Envio de Mensagem para WhatsApp via Twilio
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

        print(f"📤 Enviando mensagem para {telefone}: {mensagem}")
        print(f"📡 Resposta Twilio: {response.status_code} - {response.text}")

        if response.status_code in [200, 201]:
            return True
        else:
            return False

    except Exception as e:
        print(f"❌ ERRO ao enviar mensagem via Twilio: {e}")
        return False

# ✅ Função para Processar Mensagem do WhatsApp
def processar_mensagem(mensagem):
    if mensagem in ["oi", "olá", "bom dia"]:
        return "👋 Olá! Eu sou a IA Jurídica. Como posso te ajudar?\nDigite *ajuda* para ver os comandos disponíveis."
    
    elif mensagem == "ajuda":
        return "📌 Comandos disponíveis:\n1️⃣ *Regras* - Listar regras jurídicas\n2️⃣ *Consultar [termo]* - Buscar regras\n3️⃣ *Enviar documento* - Enviar um documento para análise."
    
    elif mensagem.startswith("consultar "):
        termo = mensagem.replace("consultar ", "")
        regras = listar_todas_regras()
        regras_encontradas = [r for r in regras if termo.lower() in r['titulo'].lower()]
        return f"🔎 Regras encontradas:\n" + "\n".join([f"- {r['titulo']}" for r in regras_encontradas]) if regras_encontradas else "⚠️ Nenhuma regra encontrada."

    elif mensagem == "regras":
        regras = listar_todas_regras()
        return f"📜 Regras disponíveis:\n" + "\n".join([f"- {r['titulo']}" for r in regras])

    return "🤔 Não entendi. Digite *ajuda* para ver os comandos disponíveis."

# ✅ Função para Limpar Texto Extraído
def limpar_texto_extraido(texto):
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto).strip()

# ✅ Configuração correta da porta no Railway
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
