import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Obtendo a URL do banco de dados do Railway
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ ERRO: DATABASE_URL não está definida!")

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados PostgreSQL"""
    try:
        print("🔄 Tentando conectar ao banco de dados...")
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        print("✅ Conexão com o banco de dados bem-sucedida!")
        return conn
    except Exception as e:
        print(f"❌ ERRO ao conectar ao banco de dados: {e}")
        raise

def criar_tabela():
    """Cria a tabela regras_juridicas se não existir"""
    query = """
    CREATE TABLE IF NOT EXISTS regras_juridicas (
        id SERIAL PRIMARY KEY,
        titulo TEXT NOT NULL,
        descricao TEXT NOT NULL
    );
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                conn.commit()
                print("✅ Tabela 'regras_juridicas' garantida no banco!")
    except Exception as e:
        print(f"❌ ERRO ao criar tabela: {e}")
        raise

def inserir_regra_juridica(titulo, descricao):
    """Adiciona uma nova regra jurídica ao banco de dados"""
    query = "INSERT INTO regras_juridicas (titulo, descricao) VALUES (%s, %s) RETURNING id;"
    try:
        print(f"📝 Inserindo nova regra: {titulo}")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (titulo, descricao))
                regra = cur.fetchone()
                
                if not regra:
                    raise Exception("⚠️ Nenhum ID retornado ao inserir a regra.")
                
                regra_id = regra["id"]
                conn.commit()
                print(f"✅ Regra inserida com sucesso! ID: {regra_id}")
                return {"id": regra_id, "titulo": titulo, "descricao": descricao}
    except Exception as e:
        print(f"❌ ERRO: Falha ao inserir regra: {e}")
        raise

def listar_todas_regras():
    """Lista todas as regras jurídicas cadastradas no banco de dados"""
    query = "SELECT id, titulo, descricao FROM regras_juridicas;"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                regras = cur.fetchall()
                
                if not regras:
                    print("⚠️ Nenhuma regra encontrada.")
                    return []
                
                print(f"📜 {len(regras)} regras encontradas.")
                return regras
    except Exception as e:
        print(f"❌ ERRO: Falha ao listar regras: {e}")
        raise

# ✅ Garante que a tabela seja criada apenas uma vez
if __name__ == "__main__":
    criar_tabela()
