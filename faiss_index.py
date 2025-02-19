import faiss
import numpy as np
import pickle
import os
from database import listar_todas_regras
from sentence_transformers import SentenceTransformer

# ✅ Carrega modelo para embeddings
modelo = SentenceTransformer("all-MiniLM-L6-v2")

# ✅ Caminhos para salvar o índice FAISS
INDEX_PATH = "faiss_index.bin"
METADATA_PATH = "faiss_metadata.pkl"

def construir_indice():
    """🔍 Constrói o índice FAISS com as regras do PostgreSQL."""
    regras = listar_todas_regras()
    
    if not regras:
        print("⚠️ Nenhuma regra jurídica encontrada no banco!")
        return None, None

    textos = [r[1] + " " + r[2] for r in regras]  # Concatena título + descrição
    embeddings = modelo.encode(textos, convert_to_numpy=True)

    # ✅ Cria índice FAISS
    d = embeddings.shape[1]  # Dimensão do embedding
    index = faiss.IndexFlatL2(d)
    index.add(embeddings)

    # ✅ Salva o índice e as regras mapeadas
    faiss.write_index(index, INDEX_PATH)
    with open(METADATA_PATH, "wb") as f:
        pickle.dump(regras, f)

    print("✅ Índice FAISS criado e salvo!")
    return index, regras

def carregar_indice():
    """📥 Carrega o índice FAISS salvo ou cria um novo."""
    if not os.path.exists(INDEX_PATH) or not os.path.exists(METADATA_PATH):
        print("⚠️ Índice FAISS não encontrado. Criando um novo...")
        return construir_indice()

    index = faiss.read_index(INDEX_PATH)
    with open(METADATA_PATH, "rb") as f:
        regras = pickle.load(f)

    print("✅ Índice FAISS carregado com sucesso!")
    return index, regras

def buscar_regras(consulta, top_k=3):
    """🔎 Busca regras similares no FAISS."""
    index, regras = carregar_indice()

    if index is None or regras is None:
        return []

    embedding_consulta = modelo.encode([consulta], convert_to_numpy=True)
    _, indices = index.search(embedding_consulta, top_k)
    
    resultados = [regras[i] for i in indices[0] if i < len(regras)]
    
    return [{"id": r[0], "titulo": r[1], "descricao": r[2]} for r in resultados]

# ✅ Construir ou carregar índice ao iniciar
if __name__ == "__main__":
    construir_indice()
