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
from fastapi import Request

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

# ✅ Adicionar Regra Jurídica (Corrigido para retornar os valores corretamente)
@app.post("/adicionar-regra")
def adicionar_regra(regra: RegraJuridica):
    """Insere uma nova regra jurídica na tabela regras_juridicas"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO regras_juridicas (titulo, descricao) VALUES (%s, %s) RETURNING id, titulo, descricao;",
            (regra.titulo, regra.descricao)
        )
        nova_regra = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "mensagem": "📌 Regra jurídica adicionada com sucesso!",
            "regra": {"id": nova_regra[0], "titulo": nova_regra[1], "descricao": nova_regra[2]}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar regra: {str(e)}")

# ✅ Listar Regras Jurídicas (Corrigido para exibir ID, título e descrição corretamente)
@app.get("/listar-regras")
def listar_regras():
    try:
        regras = listar_todas_regras()
        return {"regras": [{"id": r[0], "titulo": r[1], "descricao": r[2]} for r in regras]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Teste de Conexão com o Banco de Dados
@app.get("/testar-conexao")
def testar_conexao():
    """Verifica se a conexão com o banco de dados está funcionando"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        return {"mensagem": "✅ Conexão bem-sucedida!", "resultado": resultado[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Falha na conexão com o banco de dados.")

# ✅ Webhook para WhatsApp (Corrigido)
@app.post("/webhook-whatsapp")
async def webhook_whatsapp(
    Body: str = Form(...),
    From: str = Form(...)
):
    try:
        mensagem = Body.strip().lower()
        numero_remetente = From.strip()

        if not mensagem:
            return {"status": "⚠️ Nenhuma mensagem recebida"}

        resposta = processar_mensagem(mensagem)
        sucesso = enviar_mensagem(numero_remetente, resposta)
        return {"status": "✅ Mensagem processada!" if sucesso else "⚠️ Erro ao enviar resposta"}
    except Exception as e:
        return {"status": f"❌ Erro ao processar mensagem: {str(e)}"}

# ✅ Função para Processar Mensagem do WhatsApp (IA Jurídica consultando base de regras)
def processar_mensagem(mensagem):
    if mensagem in ["oi", "olá", "bom dia"]:
        return "👋 Olá! Eu sou a IA Jurídica. Como posso te ajudar?\nDigite *ajuda* para ver os comandos disponíveis."
    
    elif mensagem == "ajuda":
        return "📌 Comandos disponíveis:\n1️⃣ *Regras* - Listar regras jurídicas\n2️⃣ *Consultar [termo]* - Buscar regras\n3️⃣ *Enviar documento* - Enviar um documento para análise."
    
    elif mensagem.startswith("consultar "):
        termo = mensagem.replace("consultar ", "")
        regras = listar_todas_regras()
        regras_encontradas = [r for r in regras if termo.lower() in r[1].lower()]
        return f"🔎 Regras encontradas:\n" + "\n".join([f"- {r[1]}" for r in regras_encontradas]) if regras_encontradas else "⚠️ Nenhuma regra encontrada."

    elif mensagem == "regras":
        regras = listar_todas_regras()
        return f"📜 Regras disponíveis:\n" + "\n".join([f"- {r[1]}" for r in regras])

    return "🤔 Não entendi. Digite *ajuda* para ver os comandos disponíveis."

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

        if response.status_code in [200, 201]:
            return True
        else:
            print(f"⚠️ Falha ao enviar mensagem. Status: {response.status_code}, Erro: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERRO ao enviar mensagem via Twilio: {e}")
        return False

# ✅ Configuração correta da porta no Railway
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
