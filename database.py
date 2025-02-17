import psycopg2
from psycopg2.extras import RealDictCursor
import os
from urllib.parse import urlparse

# Captura a URL correta do banco de dados
DATABASE_URL = os.environ.get("DATABASE_URL", "")

if not DATABASE_URL:
    raise ValueError("Erro: DATABASE_URL não está definida no ambiente!")

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados PostgreSQL"""
    url = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        dbname=url.path[1:],  # Remove a barra inicial do caminho
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
        print("Tabela criada com sucesso!")
    except Exception as e:
        print(f"Erro ao criar a tabela: {e}")

# Criar a tabela ao iniciar o banco
criar_tabela()
