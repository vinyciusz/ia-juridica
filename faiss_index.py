import faiss
import numpy as np
from database import listar_todas_regras
from sentence_transformers import SentenceTransformer

# ✅ Carrega modelo para embeddings
modelo = SentenceTransformer("all-MiniLM-L6-v2")

# ✅ Inicializa FAISS
dimension = 384  # Dimensão do embedding
index = faiss.IndexFlatL2(dimension)
regras_mapeadas = {}

def construir_indice():
    """🔍 Constrói o índice FAISS com as regras do PostgreSQL."""
    global index, regras_mapeadas
    regras = listar_todas_regras()
    textos = [r[1] + " " + r[2] for r in regras]  # Título + descrição
    embeddings = modelo.encode(textos)
    index.add(np.array(embeddings, dtype=np.float32))
    
    # Mapeia ID da regra ao índice FAISS
    regras_mapeadas = {i: r for i, r in enumerate(regras)}

def buscar_regras(consulta, top_k=3):
    """🔎 Busca regras similares no FAISS."""
    embedding_consulta = modelo.encode([consulta])
    _, indices = index.search(np.array(embedding_consulta, dtype=np.float32), top_k)
    
    resultados = [regras_mapeadas[i] for i in indices[0] if i in regras_mapeadas]
    return [{"id": r[0], "titulo": r[1], "descricao": r[2]} for r in resultados]

# ✅ Construir índice ao carregar
construir_indice()
