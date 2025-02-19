from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import uvicorn
import os
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from database import inserir_regra_juridica, listar_todas_regras, get_db_connection
import re
import requests
from fastapi import Request
from faiss_index import buscar_regras
import openai  # Biblioteca da OpenAI

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

# ✅ Listar Regras Jurídicas
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

# ✅ Webhook para WhatsApp
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

def processar_mensagem(mensagem):
    if mensagem in ["oi", "olá", "bom dia"]:
        return "👋 Olá! Eu sou a IA Jurídica. Como posso te ajudar?\nDigite *ajuda* para ver os comandos disponíveis."
    
    elif mensagem == "ajuda":
        return "📌 Comandos disponíveis:\n1️⃣ *Regras* - Listar regras jurídicas\n2️⃣ *Consultar [termo]* - Buscar regras\n3️⃣ *Enviar documento* - Enviar um documento para análise."

    elif mensagem.startswith("consultar "):
        termo = mensagem.replace("consultar ", "")
        regras = buscar_regras(termo)  # Agora busca no FAISS corretamente

        if not regras:
            return "⚠️ Nenhuma regra encontrada para esse termo."

        resposta = "📖 *Regras encontradas:*\n"
        for idx, r in enumerate(regras, start=1):
            resposta += f"\n➖ *{idx}. {r['titulo']}*\n📌 {r['descricao']}\n"

        return resposta

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

# ✅ Configuração da OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# ✅ Consulta ao GPT-4o
def consultar_gpt(pergunta):
    """Envia uma pergunta para o GPT-4o e retorna a resposta."""
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é uma IA jurídica especializada em direito imobiliário e usucapião."},
                {"role": "user", "content": pergunta}
            ]
        )
        return resposta.choices[0].message.content
    except Exception as e:
        return f"⚠️ Erro ao consultar IA: {str(e)}"

# ✅ Configuração correta da porta no Railway
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
