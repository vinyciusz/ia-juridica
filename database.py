import psycopg2
from psycopg2.extras import RealDictCursor
import os
from urllib.parse import urlparse

# Obtendo a URL do banco de dados do Railway
DATABASE_URL = os.getenv("DATABASE_URL")

# Parse da URL para garantir que os parâmetros estão corretos
def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados PostgreSQL"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL não está definida!")

    url = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        dbname=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        cursor_factory=RealDictCursor
    )
    return conn

def criar_tabela():
    """Cria a tabela regras_juridicas se ela não existir"""
    try:
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
    except Exception as e:
        print(f"Erro ao criar a tabela: {e}")

# Criar a tabela ao iniciar o banco
criar_tabela()

def inserir_regra_juridica(titulo, descricao):
    """Adiciona uma nova regra jurídica ao banco de dados"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO regras_juridicas (titulo, descricao) VALUES (%s, %s) RETURNING id;",
                (titulo, descricao))
    regra_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": regra_id, "titulo": titulo, "descricao": descricao}
