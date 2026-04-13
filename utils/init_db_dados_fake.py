import sqlite3
import pandas as pd
import os

DB_NAME = "database_RIO.db"
SCHEMA_FILE = "Schema.csv"

def translate_type(bq_type):
    """Traduz tipos do BigQuery para SQLite."""
    bq_type = bq_type.upper()
    if bq_type == "STRING":
        return "TEXT"
    if bq_type == "INT64":
        return "INTEGER"
    if bq_type == "FLOAT64":
        return "REAL"
    if bq_type == "DATE":
        return "TEXT"
    if bq_type == "TIMESTAMP":
        return "TEXT"
    return "TEXT"

def init_db():
    if not os.path.exists(SCHEMA_FILE):
        print(f"Erro: Arquivo {SCHEMA_FILE} não encontrado.")
        return

    df_schema = pd.read_csv(SCHEMA_FILE)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    tables = df_schema['table_name'].unique()
    
    for table in tables:
        cols = df_schema[df_schema['table_name'] == table]
        col_defs = []
        pk_defined = False
        for _, row in cols.iterrows():
            col_name = row['column_name']
            col_type = translate_type(row['data_type'])
            
            # Adicionar Primary Key se terminar em ID e ainda não houver PK
            pk = ""
            if not pk_defined and col_name.lower().endswith("id"):
                pk = " PRIMARY KEY"
                pk_defined = True
            
            col_defs.append(f"{col_name} {col_type}{pk}")
        
        create_sql = f"CREATE TABLE IF NOT EXISTS {table} (\n    " + ",\n    ".join(col_defs) + "\n);"
        print(f"Criando tabela {table}...")
        cursor.execute(create_sql)
    
    # --- Dados Iniciais (Seeding) ---
    print("Populando dados iniciais...")
    
    # Servico
    cursor.executemany("INSERT OR IGNORE INTO Servico (servicoID, Prefixo, descricao) VALUES (?, ?, ?)", [
        ("S1", "SPPO", "Serviço Público de Passageiros por Ônibus"),
        ("S2", "BRT", "Bus Rapid Transit"),
        ("S3", "STPL", "Sistema de Transporte Público Local"),
    ])
    
    # Operador
    cursor.executemany("INSERT OR IGNORE INTO operador (operadorID, nomeFantasia, razaoSocial) VALUES (?, ?, ?)", [
        ("O1", "Consórcio Intersul", "Consórcio Intersul de Transportes"),
        ("O2", "Consórcio Internorte", "Consórcio Internorte de Transportes"),
        ("O3", "Consórcio Transcarioca", "Consórcio Transcarioca de Transportes"),
        ("O4", "Consórcio Santa Cruz", "Consórcio Santa Cruz de Transportes"),
    ])
    
    # AreaOperacional
    cursor.executemany("INSERT OR IGNORE INTO AreaOperacional (areaOperacionalID, descricao) VALUES (?, ?)", [
        ("A1", "Centro"),
        ("A2", "Zona Sul"),
        ("A3", "Zona Norte"),
        ("A4", "Zona Oeste"),
    ])
    
    # TipoSistema
    cursor.executemany("INSERT OR IGNORE INTO TipoSistema (tipoSistemaID, descricao) VALUES (?, ?)", [
        ("T1", "Convencional"),
        ("T2", "Executivo"),
        ("T3", "Alimentador"),
    ])
    
    # TipoVeiculo
    cursor.executemany("INSERT OR IGNORE INTO TipoVeiculo (tipoVeiculoID, descricao) VALUES (?, ?)", [
        ("V1", "Ônibus Urbano"),
        ("V2", "Micro-ônibus"),
        ("V3", "Articulado"),
    ])

    # GrupamentoBRS
    cursor.executemany("INSERT OR IGNORE INTO GrupamentoBRS (grupamentoBRSID, descricao) VALUES (?, ?)", [
        ("1", 1),
        ("2", 2),
        ("3", 3),
    ])

    conn.commit()
    conn.close()
    print(f"Banco de dados {DB_NAME} inicializado e populado com sucesso.")

if __name__ == "__main__":
    init_db()
