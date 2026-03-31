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
        "exclusaoLinha": [
            "exclusaoLinhaID TEXT PRIMARY KEY",
            "linha INTEGER",
            "servico TEXT",
            "oficio TEXT",
            "dataExclusao TIMESTAMP",
            "linhaID TEXT"
        ],
        "operador": [
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

if __name__ == "__main__":
    # Remover DB antigo para garantir limpeza, se necessário (opcional)
    # if os.path.exists(DB_NAME):
    #     os.remove(DB_NAME)
    
    init_db()
