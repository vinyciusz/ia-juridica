import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Obtendo a URL do banco de dados do Railway
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados PostgreSQL"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def criar_tabela():
    """Cria a tabela regras_juridicas se ela não existir"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS regras_juridicas (
            id SERIAL PRIMARY KEY,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Criar a tabela ao iniciar o banco
criar_tabela()

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
