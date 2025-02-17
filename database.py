import psycopg2
from psycopg2.extras import RealDictCursor
import os
from urllib.parse import urlparse

# Obtendo a URL do banco de dados do Railway
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERRO: A variável DATABASE_URL não está definida!")
    raise ValueError("DATABASE_URL não está definida!")

# Parseando a URL do banco para garantir que os dados estejam corretos
parsed_url = urlparse(DATABASE_URL)

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados PostgreSQL"""
    print("Tentando conectar ao banco de dados...")  # Debug
    try:
        conn = psycopg2.connect(
            dbname=parsed_url.path[1:],  # Remove a barra inicial do nome do banco
            user=parsed_url.username,
            password=parsed_url.password,
            host=parsed_url.hostname,
            port=parsed_url.port or 5432,  # Garante que usa a porta correta
            cursor_factory=RealDictCursor
        )
        print("Conexão com o banco de dados bem-sucedida!")  # Debug
        return conn
    except Exception as e:
        print(f"ERRO: Falha ao conectar ao banco de dados - {e}")
        raise e  # Relança a exceção para os logs do Railway

def inserir_regra_juridica(titulo, descricao):
    """Adiciona uma nova regra jurídica ao banco de dados"""
    print(f"Inserindo nova regra: {titulo}")  # Debug
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO regras_juridicas (titulo, descricao) VALUES (%s, %s) RETURNING id;",
                    (titulo, descricao))
        regra_id = cur.fetchone()[0]
        conn.commit()
        print(f"Regra adicionada com ID {regra_id}")  # Debug
        return {"id": regra_id, "titulo": titulo, "descricao": descricao}
    except Exception as e:
        print(f"ERRO: Falha ao inserir regra - {e}")
        raise e
    finally:
        cur.close()
        conn.close()

def listar_todas_regras():
    """Lista todas as regras jurídicas cadastradas no banco de dados"""
    print("Buscando todas as regras cadastradas...")  # Debug
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, titulo, descricao FROM regras_juridicas;")
        regras = cur.fetchall()
        print(f"Encontradas {len(regras)} regras.")  # Debug
        return regras
    except Exception as e:
        print(f"ERRO: Falha ao listar regras - {e}")
        raise e
    finally:
        cur.close()
        conn.close()
