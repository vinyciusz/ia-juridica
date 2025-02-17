import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Obtendo a URL do banco de dados do Railway
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não está definida!")

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados PostgreSQL"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def inserir_regra_juridica(titulo, descricao):
    """Adiciona uma nova regra jurídica ao banco de dados"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO regras_juridicas (titulo, descricao) VALUES (%s, %s) RETURNING id;",
                (titulo, descricao))
    regra_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": regra_id, "titulo": titulo, "descricao": descricao}

def listar_todas_regras():
    """Lista todas as regras jurídicas cadastradas no banco de dados"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, titulo, descricao FROM regras_juridicas;")
    regras = cur.fetchall()
    cur.close()
    conn.close()
    return regras

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados PostgreSQL"""
    print("Tentando conectar ao banco de dados...")  # Adicionado para debug
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
