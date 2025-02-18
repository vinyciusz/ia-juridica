from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import uvicorn
import os
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from database import inserir_regra_juridica, listar_todas_regras  # Mantendo importações necessárias
import re  # Adicione essa importação no topo do arquivo

app = FastAPI()

# ✅ Modelo Pydantic para validação de regras jurídicas
class RegraJuridica(BaseModel):
    titulo: str
    descricao: str

@app.get("/")
def home():
    """🏠 Endpoint de boas-vindas da API"""
    return {"mensagem": "🚀 API da IA Jurídica rodando na nuvem!"}

@app.post("/adicionar-regra")
def adicionar_regra(regra: RegraJuridica):
    """📜 Adiciona uma nova regra jurídica ao banco de dados"""
    try:
        print(f"📝 Tentando inserir regra: {regra.titulo}")
        nova_regra = inserir_regra_juridica(regra.titulo, regra.descricao)
        print(f"✅ Regra inserida com sucesso! {nova_regra}")
        return {"mensagem": "📌 Regra jurídica adicionada com sucesso!", "regra": nova_regra}
    except Exception as e:
        print(f"❌ ERRO ao inserir regra: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/listar-regras")
def listar_regras():
    """📜 Lista todas as regras jurídicas armazenadas"""
    try:
        regras = listar_todas_regras()
        print(f"📂 {len(regras)} regras encontradas!")
        return {"regras": regras}
    except Exception as e:
        print(f"❌ ERRO ao listar regras: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/testar-conexao")
def testar_conexao():
    """🔍 Teste de conexão com o banco de dados"""
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
        print(f"❌ ERRO ao conectar ao banco: {e}")
        raise HTTPException(status_code=500, detail="Falha na conexão com o banco de dados.")

@app.post("/upload-documento")
async def upload_documento(file: UploadFile = File(...)):
    """📄 Faz upload e processa um documento PDF ou imagem"""
    try:
        print(f"📤 Recebendo arquivo: {file.filename}")
        if not file.filename.endswith((".pdf", ".png", ".jpg", ".jpeg")):
            raise HTTPException(status_code=400, detail="⚠️ Formato de arquivo não suportado. Envie um PDF ou imagem!")

        # Converte PDF para imagem se necessário
        if file.filename.endswith(".pdf"):
            imagens = convert_from_bytes(await file.read())
            texto_extraido = "\n".join([pytesseract.image_to_string(img) for img in imagens])
        else:
            imagem = Image.open(file.file)
            texto_extraido = pytesseract.image_to_string(imagem)
            texto_limpo = limpar_texto_extraido(texto_extraido)  # Aplicando a limpeza no texto extraído

        print(f"🔍 Texto extraído do documento:\n{texto_extraido}")
        return {"mensagem": "📄 Documento processado com sucesso!", "texto": texto_limpo}
    except Exception as e:
        print(f"❌ ERRO ao processar documento: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar o documento.")

# ✅ Configuração correta da porta no Railway (NÃO ALTERAR)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

def limpar_texto_extraido(texto):
    """
    🧹 Função para limpar e organizar o texto extraído do documento.
    - Remove múltiplos espaços e quebras de linha
    - Substitui caracteres estranhos
    """
    if not texto:
        return ""

    # Remove espaços duplicados e caracteres estranhos
    texto_limpo = re.sub(r'\s+', ' ', texto).strip()
    return texto_limpo
