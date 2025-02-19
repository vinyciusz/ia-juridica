from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import uvicorn
import os
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import re
import requests
from fastapi import Request
from database import inserir_regra_juridica, listar_todas_regras, get_db_connection
from faiss_index import buscar_regras, construir_indice
from openai import OpenAI

# ✅ Configuração do Twilio (WhatsApp)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# ✅ Configuração do cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Inicializando FastAPI
app = FastAPI()

# ✅ Modelo para Regras Jurídicas
class RegraJuridica(BaseModel):
    titulo: str
    descricao: str

# ✅ Construção do índice FAISS ao iniciar a API
construir_indice()

# ✅ Endpoint de Boas-Vindas
@app.get("/")
def home():
    return {"mensagem": "🚀 API da IA Jurídica rodando na nuvem!"}

# ✅ Adicionar Regra Jurídica (PostgreSQL e FAISS)
@app.post("/adicionar-regra")
def adicionar_regra(regra: RegraJuridica):
    """Insere uma nova regra jurídica e atualiza o índice FAISS"""
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

        # Atualiza o FAISS com a nova regra
        construir_indice()

        return {
            "mensagem": "📌 Regra jurídica adicionada com sucesso!",
            "regra": {"id": nova_regra[0], "titulo": nova_regra[1], "descricao": nova_regra[2]}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar regra: {str(e)}")

# ✅ Listar Regras Jurídicas
@app.get("/listar-regras")
def listar_regras():
    try:
        regras = listar_todas_regras()
        return {"regras": [{"id": r[0], "titulo": r[1], "descricao": r[2]} for r in regras]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Webhook para WhatsApp (IA Jurídica Natural)
@app.post("/webhook-whatsapp")
async def webhook_whatsapp(
    Body: str = Form(...),
    From: str = Form(...)
):
    try:
        mensagem = Body.strip()
        numero_remetente = From.strip()

        if not mensagem:
            return {"status": "⚠️ Nenhuma mensagem recebida"}

        resposta = processar_mensagem(mensagem)
        sucesso = enviar_mensagem(numero_remetente, resposta)
        return {"status": "✅ Mensagem processada!" if sucesso else "⚠️ Erro ao enviar resposta"}
    except Exception as e:
        return {"status": f"❌ Erro ao processar mensagem: {str(e)}"}

# ✅ Processamento de Mensagem via IA Jurídica (FAISS + OpenAI)
def processar_mensagem(mensagem):
    regras = buscar_regras(mensagem)

    if regras:
        resposta = "📖 *Regras encontradas:*\n"
        for idx, r in enumerate(regras, start=1):
            resposta += f"\n➖ *{idx}. {r['titulo']}*\n📌 {r['descricao']}\n"
        return resposta
    else:
        return consultar_gpt(mensagem)  # IA responde de forma humanizada

# ✅ Consulta ao GPT-4 para Respostas Humanizadas
def consultar_gpt(pergunta):
    """Envia uma pergunta para o GPT-4 e retorna a resposta humanizada."""
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é uma IA jurídica especializada em direito imobiliário e usucapião. Responda como um advogado experiente, com explicações claras e humanizadas."},
                {"role": "user", "content": pergunta}
            ]
        )
        return resposta.choices[0].message.content
    except Exception as e:
        return f"⚠️ Erro ao consultar IA: {str(e)}"

# ✅ Processamento de Documentos (OCR)
@app.post("/processar-documento")
async def processar_documento(arquivo: UploadFile = File(...)):
    """Processa um documento PDF ou imagem e extrai o texto usando OCR."""
    try:
        conteudo = await arquivo.read()
        
        if arquivo.filename.endswith(".pdf"):
            imagens = convert_from_bytes(conteudo)
            texto_extraido = "\n".join([pytesseract.image_to_string(img) for img in imagens])
        else:
            imagem = Image.open(io.BytesIO(conteudo))
            texto_extraido = pytesseract.image_to_string(imagem)

        return {"mensagem": "📄 Texto extraído com sucesso!", "texto": texto_extraido}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

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

# ✅ Teste de Conexão com OpenAI
@app.get("/testar-gpt")
def testar_gpt():
    """Testa a conexão com a API da OpenAI."""
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Diga apenas: Teste bem-sucedido!"}]
        )
        return {"mensagem": resposta.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar com OpenAI: {str(e)}")

# ✅ Configuração correta da porta no Railway
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
