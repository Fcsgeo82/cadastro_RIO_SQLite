import sqlite3
import os
import bcrypt
import uuid
from datetime import datetime, timezone

DB_NAME = "database_RIO.db"

def init_db():
    """Inicializa o banco de dados SQLite com a estrutura baseada no Schema.csv."""
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Definição das tabelas e campos (Schema)
    tables = {
        "AreaOperacional": [
            "areaOperacionalID TEXT PRIMARY KEY",
            "codigo INTEGER",
            "descricao TEXT",
            "corReferencia TEXT"
        ],
        "GrupamentoBRS": [
            "grupamentoBRSID TEXT PRIMARY KEY",
            "descricao INTEGER"
        ],
"Linha": [
    "linhaID TEXT PRIMARY KEY",
    "numeroLinha TEXT",
    "dataCriacaoLinha TIMESTAMP",
    "servico TEXT",
    "operador TEXT",
    "vista TEXT",
    "via TEXT",
    "areaOperacional TEXT",
    "oficio TEXT",
    "oficioprimeiroHistorico TEXT",
    "oficioUltimaAlteracao TEXT",
    "tipoSistema TEXT",
    "kmIDA REAL",
    "kmVOLTA REAL",
    "parametro_novo TEXT",
    "caracteristica TEXT",
    "grupamentoBRS INTEGER",
    "frotaTipoVeiculo TEXT",
    "frotaUltimoOficio TEXT",
    "frotaDataOficio TEXT",
    "observacao TEXT",
    "dataCadastro TIMESTAMP",
    "ultimaAtualizacao TIMESTAMP",
    "areaGeografica TEXT",
    "classificacaoEspacial TEXT",
    "parametro TEXT"
],
        "Oficio": [
            "oficioID TEXT PRIMARY KEY",
            "numeroOficio INTEGER",
            "dataOficio TIMESTAMP",
            "assunto TEXT",
            "numeroProcesso TEXT",
            "dataCadastro TIMESTAMP",
            "linha TEXT"
        ],
        "Parametro": [
            "parametroID TEXT PRIMARY KEY",
            "descricao TEXT"
        ],
        "Caracteristica": [
            "caracteristicaID TEXT PRIMARY KEY",
            "descricao TEXT"
        ],
        "Servico": [
            "servicoID TEXT PRIMARY KEY",
            "descricao TEXT",
            "Prefixo TEXT"
        ],
        "TipoSistema": [
            "tipoSistemaID TEXT PRIMARY KEY",
            "descricao TEXT",
            "sentido TEXT"
        ],
        "TipoVeiculo": [
            "tipoVeiculoID TEXT PRIMARY KEY",
            "descricao TEXT",
            "codigoVeiculo INTEGER"
        ],
"ExclusaoLinha": [
    "exclusaoLinhaID TEXT PRIMARY KEY",
    "linha INTEGER",
    "servico TEXT",
    "oficio TEXT",
    "dataExclusao TIMESTAMP",
    "linhaID TEXT"
],
"LinhaExcluida": [
    "linhaID TEXT PRIMARY KEY",
    "numeroLinha TEXT",
    "dataCriacaoLinha TIMESTAMP",
    "servico TEXT",
    "operador TEXT",
    "vista TEXT",
    "via TEXT",
    "areaOperacional TEXT",
    "oficio TEXT",
    "oficioprimeiroHistorico TEXT",
    "oficioUltimaAlteracao TEXT",
    "tipoSistema TEXT",
    "kmIDA REAL",
    "kmVOLTA REAL",
    "parametro_novo TEXT",
    "caracteristica TEXT",
    "grupamentoBRS INTEGER",
    "frotaTipoVeiculo TEXT",
    "frotaUltimoOficio TEXT",
    "frotaDataOficio TEXT",
    "observacao TEXT",
    "dataCadastro TIMESTAMP",
    "ultimaAtualizacao TIMESTAMP",
    "areaGeografica TEXT",
    "classificacaoEspacial TEXT",
    "parametro TEXT",
    "oficioExclusao TEXT",
    "dataExclusao TIMESTAMP",
    "usuarioExclusao TEXT"
],
"Itinerario": [
    "itinerarioID TEXT PRIMARY KEY",
    "linhaRefID TEXT",
    "sentido TEXT",
    "ordem INTEGER",
    "logradouro TEXT",
    "bairro TEXT",
    "observacao TEXT",
    "tipo TEXT",
    "oficio TEXT"
],
"Operador": [
    "operadorID TEXT PRIMARY KEY",
    "cnpj TEXT",
    "nomeFantasia TEXT",
    "razaoSocial TEXT",
    "termo TEXT",
    "dataCadastro TIMESTAMP"
],
"Usuarios": [
    "userID TEXT PRIMARY KEY",
    "username TEXT UNIQUE",
    "password_hash TEXT",
    "role TEXT",
    "email TEXT",
    "reset_token TEXT",
    "reset_expiry TEXT",
    "failed_attempts INTEGER DEFAULT 0",
    "lockout_until TEXT"
]
    }

    print(f"Inicializando banco de dados: {DB_NAME}")
    
    for table_name, columns in tables.items():
        col_defs = ",\n    ".join(columns)
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {col_defs}\n);"
        print(f"Criando tabela: {table_name}")
        cursor.execute(create_sql)
    
    # Inicializar usuários admin se não existirem
    cursor.execute("SELECT COUNT(*) FROM Usuarios")
    if cursor.fetchone()[0] == 0:
        print("Inserindo usuários iniciais...")
        
        users = [
            {
                "username": "admin",
                "password": "admin123",
                "role": "admin",
                "email": "admin@example.com"
            },
            {
                "username": "user",
                "password": "user123",
                "role": "user",
                "email": "user@example.com"
            }
        ]
        
        for u in users:
            user_id = str(uuid.uuid4())
            pwd_hash = bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt()).decode()
            created = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                INSERT INTO Usuarios (userID, username, password_hash, role, email, reset_token, reset_expiry)
                VALUES (?, ?, ?, ?, ?, NULL, NULL)
            """, (user_id, u["username"], pwd_hash, u["role"], u["email"]))
        
        print("Usuários iniciais inseridos.")

    # Popular Parametro e Caracteristica se estiverem vazios
    cursor.execute("SELECT COUNT(*) FROM Parametro")
    if cursor.fetchone()[0] == 0:
        p_data = [('Polarizada',), ('Inter-Região',), ('Intra-Região',)]
        for p in p_data:
            cursor.execute("INSERT INTO Parametro (parametroID, descricao) VALUES (?, ?)", (str(uuid.uuid4()), p[0]))
            
    cursor.execute("SELECT COUNT(*) FROM Caracteristica")
    if cursor.fetchone()[0] == 0:
        c_data = [('Alimentadora',), ('Inter-Bairro',)]
        for c in c_data:
            cursor.execute("INSERT INTO Caracteristica (caracteristicaID, descricao) VALUES (?, ?)", (str(uuid.uuid4()), c[0]))
    
    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"Banco de dados {DB_NAME} inicializado com sucesso.")

def populate_from_csv():
    """Lê o arquivo Schema BQ - TABELAS.csv e popula o banco de dados."""
    CSV_FILE = "Schema BQ - TABELAS.csv"
    if not os.path.exists(CSV_FILE):
        print(f"Erro: Arquivo {CSV_FILE} not encontrado.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_table = None
    headers = None
    
    for line in lines:
        row = [p.strip() for p in line.split(',')]
        # Limpar partes vazias no final
        while row and not row[-1]:
            row.pop()
            
        if not row:
            # Linha realmente vazia ou apenas vírgulas
            current_table = None
            headers = None
            continue
            
        # Se não temos tabela, o primeiro campo útil é o nome da tabela
        if current_table is None:
            # Ignorar se for uma linha que parece dados ou headers (tem muitos campos)
            if len(row) > 1:
                # Caso especial: se a linha tem dados mas perdemos a tabela, tentamos recuperar?
                # Geralmente a primeira linha de uma seção é a tabela.
                continue
            current_table = row[0]
            headers = None
            print(f"Detectada seção para tabela: {current_table}")
            continue
            
        # Se temos tabela mas não headers, esta linha é o header
        if headers is None:
            headers = row
            # Garantir que os nomes dos campos batam com o esperado (opcional)
            continue
            
        # Se temos tabela e headers, esta linha é dado
        data = row
        # Ajustar tamanho
        if len(data) < len(headers):
            data.extend([''] * (len(headers) - len(data)))
        elif len(data) > len(headers):
            data = data[:len(headers)]
            
        # Pular linhas de dados que estão vazias (ex: ",,,")
        if not any(data):
            continue

        # Evitar inserir em tabelas que mudaram significativamente e não estão no CSV original corretamente
        if current_table in ["Linha", "Parametro", "Caracteristica"]:
            continue
            
        placeholders = ', '.join(['?'] * len(headers))
        cols = ', '.join(headers)
        sql = f"INSERT OR IGNORE INTO {current_table} ({cols}) VALUES ({placeholders})"
        
        try:
            cursor.execute(sql, data)
        except sqlite3.OperationalError as e:
            # Se a tabela não existir, ignora (pode ser uma tabela extra no CSV)
            if "no such table" in str(e):
                pass
            else:
                print(f"Erro ao inserir em {current_table}: {e}")
                
    conn.commit()
    conn.close()
    print("Banco de dados populado com sucesso a partir do CSV.")

if __name__ == "__main__":
    init_db()
    populate_from_csv()
