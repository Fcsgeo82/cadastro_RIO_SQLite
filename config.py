import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database_RIO.db")

def get_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # Habilitar retorno de dicionários ou objetos similares se necessário, 
    # mas o projeto usa pandas (to_dataframe), então a conexão padrão resolve.
    return conn
