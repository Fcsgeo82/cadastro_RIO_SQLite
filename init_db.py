import sqlite3
import os

DB_NAME = "database_RIO.db"

def init_db():
    """Inicializa o banco de dados SQLite com a estrutura baseada no Schema.csv."""
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Definição das tabelas e campos (Schema)
    tables = {
        "AreaGeograficaOperacao": [
            "areaGeograficaOperacaoID TEXT PRIMARY KEY",
            "area TEXT"
        ],
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
            "areaOperacional TEXT",
            "oficio TEXT",
            "oficioprimeiroHistorico TEXT",
            "oficioUltimaAlteracao TEXT",
            "tipoSistema TEXT",
            "kmIDA REAL",
            "kmVOLTA REAL",
            "areaGeografica TEXT",
            "classificacaoEspacial TEXT",
            "parametro TEXT",
            "grupamentoBRS INTEGER",
            "frotaTipoVeiculo TEXT",
            "frotaUltimoOficio TEXT",
            "frotaDataOficio TEXT",
            "itinerarioIDA TEXT",
            "itinerarioIdaOficio TEXT",
            "itinerarioIdaData TEXT",
            "itinerarioVOLTA TEXT",
            "itinerarioVoltaOficio TEXT",
            "itinerarioVoltaData TEXT",
            "observacao TEXT",
            "dataCadastro TIMESTAMP",
            "ultimaAtualizacao TIMESTAMP"
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
        "ParametroFuncional": [
            "parametroFuncionalID TEXT PRIMARY KEY",
            "parametro TEXT"
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
        "Operador": [
            "operadorID TEXT PRIMARY KEY",
            "cnpj TEXT",
            "nomeFantasia TEXT",
            "razaoSocial TEXT",
            "termo TEXT",
            "dataCadastro TIMESTAMP"
        ]
    }

    print(f"Inicializando banco de dados: {DB_NAME}")
    
    for table_name, columns in tables.items():
        col_defs = ",\n    ".join(columns)
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {col_defs}\n);"
        print(f"Criando tabela: {table_name}")
        cursor.execute(create_sql)
    
    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"Banco de dados {DB_NAME} inicializado com sucesso.")
    print("Estrutura montada conforme Schema.csv.")

def populate_from_csv():
    """Lê o arquivo Schema BQ - TABELAS.csv e popula o banco de dados."""
    CSV_FILE = "Schema BQ - TABELAS.csv"
    if not os.path.exists(CSV_FILE):
        print(f"Erro: Arquivo {CSV_FILE} não encontrado.")
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
