# =============================================================
# db.py — Operações com SQLite
# Base: database_RIO.db
# =============================================================

import uuid
from datetime import datetime, timezone

import pandas as pd
import sqlite3
from config import get_connection


def _query_df(sql: str, params: list = None) -> pd.DataFrame:
    """Executa query e retorna DataFrame. Retorna vazio em caso de erro."""
    try:
        conn = get_connection()
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        print(f"Erro na query: {e}")
        return pd.DataFrame()


def listar_tabela(table_name: str) -> pd.DataFrame:
    """Retorna todos os registros de uma tabela."""
    return _query_df(f"SELECT * FROM {table_name}")


# ------------------------------------------------------------------
# LOADERS — tabelas de referência para dropdowns
# ------------------------------------------------------------------

def carregar_servicos() -> pd.DataFrame:
    df = _query_df(f"""
        SELECT servicoID, Prefixo, descricao
        FROM Servico
        ORDER BY descricao
    """)
    if df.empty:
        return df
    # No SQLite, fillna pode ser feito via COALESCE ou no pandas
    df["Prefixo"] = df["Prefixo"].fillna("")
    df["label"] = df["Prefixo"].str.strip() + " — " + df["descricao"].str.strip()
    return df[["servicoID", "label"]].rename(columns={"servicoID": "id"})


def carregar_operadores() -> pd.DataFrame:
    df = _query_df(f"""
        SELECT operadorID, nomeFantasia
        FROM operador
        ORDER BY nomeFantasia
    """)
    if df.empty:
        return df
    return df.rename(columns={"operadorID": "id", "nomeFantasia": "label"})


def carregar_areas_operacionais() -> pd.DataFrame:
    df = _query_df(f"""
        SELECT areaOperacionalID, descricao
        FROM AreaOperacional
        ORDER BY descricao
    """)
    if df.empty:
        return df
    return df.rename(columns={"areaOperacionalID": "id", "descricao": "label"})


def carregar_areas_geograficas() -> pd.DataFrame:
    df = _query_df(f"""
        SELECT areaGeograficaOperacaoID, area
        FROM AreaGeograficaOperacao
        ORDER BY area
    """)
    if df.empty:
        return df
    return df.rename(columns={"areaGeograficaOperacaoID": "id", "area": "label"})


def carregar_tipos_sistema() -> pd.DataFrame:
    df = _query_df(f"""
        SELECT tipoSistemaID, descricao
        FROM TipoSistema
        ORDER BY descricao
    """)
    if df.empty:
        return df
    return df.rename(columns={"tipoSistemaID": "id", "descricao": "label"})


def carregar_tipos_veiculo() -> pd.DataFrame:
    df = _query_df(f"""
        SELECT tipoVeiculoID, descricao
        FROM TipoVeiculo
        ORDER BY descricao
    """)
    if df.empty:
        return df
    return df.rename(columns={"tipoVeiculoID": "id", "descricao": "label"})


def carregar_parametros() -> pd.DataFrame:
    df = _query_df(f"""
        SELECT parametroFuncionalID, parametro
        FROM ParametroFuncional
        ORDER BY parametro
    """)
    if df.empty:
        return df
    return df.rename(columns={"parametroFuncionalID": "id", "parametro": "label"})


def carregar_grupamentos() -> pd.DataFrame:
    df = _query_df(f"""
        SELECT grupamentoBRSID, CAST(descricao AS TEXT) AS descricao
        FROM GrupamentoBRS
        ORDER BY descricao
    """)
    if df.empty:
        return df
    return df.rename(columns={"grupamentoBRSID": "id", "descricao": "label"})


def carregar_oficios() -> pd.DataFrame:
    # No SQLite use || para concatenar
    df = _query_df(f"""
        SELECT oficioID,
               (CAST(numeroOficio AS TEXT) || ' — ' || COALESCE(assunto, '')) AS label
        FROM Oficio
        ORDER BY numeroOficio DESC
    """)
    if df.empty:
        return df
    return df.rename(columns={"oficioID": "id"})


# Função genérica para montar dict {label -> id} usado nos selectboxes
def opcoes(df: pd.DataFrame) -> dict:
    """Converte DataFrame {id, label} em dict {label: id} para st.selectbox."""
    if df.empty:
        return {}
    return dict(zip(df["label"], df["id"]))


# ------------------------------------------------------------------
# INSERÇÃO — tabela Linha
# ------------------------------------------------------------------

def inserir_linha(dados: dict) -> tuple[bool, str]:
    """Insere nova linha no SQLite. Retorna (sucesso, mensagem)."""
    conn = get_connection()
    agora = datetime.now(tz=timezone.utc).isoformat()

    row = {
        "linhaID":               str(uuid.uuid4()),
        "numeroLinha":           dados.get("numeroLinha", "").strip(),
        "dataCriacaoLinha":      str(dados["dataCriacaoLinha"]) if dados.get("dataCriacaoLinha") else None,
        "servico":               dados.get("servico") or None,
        "operador":              dados.get("operador") or None,
        "vista":                 dados.get("vista", "").strip() or None,
        "areaOperacional":       dados.get("areaOperacional") or None,
        "oficio":                dados.get("oficio") or None,
        "oficioprimeiroHistorico": dados.get("oficioprimeiroHistorico") or None,
        "oficioUltimaAlteracao": dados.get("oficioUltimaAlteracao") or None,
        "tipoSistema":           dados.get("tipoSistema") or None,
        "kmIDA":                 float(dados["kmIDA"]) if dados.get("kmIDA") else None,
        "kmVOLTA":               float(dados["kmVOLTA"]) if dados.get("kmVOLTA") else None,
        "areaGeografica":        dados.get("areaGeografica") or None,
        "classificacaoEspacial": dados.get("classificacaoEspacial", "").strip() or None,
        "parametro":             dados.get("parametro") or None,
        "grupamentoBRS":         dados.get("grupamentoBRS"),
        "frotaTipoVeiculo":      dados.get("frotaTipoVeiculo") or None,
        "frotaUltimoOficio":     dados.get("frotaUltimoOficio") or None,
        "frotaDataOficio":       dados.get("frotaDataOficio") or None,
        "itinerarioIDA":         dados.get("itinerarioIDA", "").strip() or None,
        "itinerarioIdaOficio":   dados.get("itinerarioIdaOficio") or None,
        "itinerarioIdaData":     dados.get("itinerarioIdaData") or None,
        "itinerarioVOLTA":       dados.get("itinerarioVOLTA", "").strip() or None,
        "itinerarioVoltaOficio": dados.get("itinerarioVoltaOficio") or None,
        "itinerarioVoltaData":   dados.get("itinerarioVoltaData") or None,
        "observacao":            dados.get("observacao", "").strip() or None,
        "dataCadastro":          agora,
        "ultimaAtualizacao":     agora,
    }

    cols = ", ".join(row.keys())
    placeholders = ", ".join(["?" for _ in row])
    sql = f"INSERT INTO Linha ({cols}) VALUES ({placeholders})"

    try:
        conn.execute(sql, list(row.values()))
        conn.commit()
        conn.close()
        return True, f"Linha {row['numeroLinha']} cadastrada com sucesso!"
    except Exception as e:
        conn.close()
        return False, f"Erro ao inserir no SQLite: {e}"


# ------------------------------------------------------------------
# CONSULTA — tabela Linha com JOINs
# ------------------------------------------------------------------

def consultar_linhas(
    numero: str = "",
    area_operacional_id: str = "",
    operador_id: str = "",
    tipo_sistema_id: str = "",
) -> pd.DataFrame:
    """Consulta linhas com filtros e retorna DataFrame enriquecido com JOINs."""
    condicoes = ["1=1"]
    params = []
    if numero.strip():
        condicoes.append("CAST(l.numeroLinha AS TEXT) LIKE ?")
        params.append(f"%{numero.strip()}%")
    if area_operacional_id:
        condicoes.append("l.areaOperacional = ?")
        params.append(area_operacional_id)
    if operador_id:
        condicoes.append("l.operador = ?")
        params.append(operador_id)
    if tipo_sistema_id:
        condicoes.append("l.tipoSistema = ?")
        params.append(tipo_sistema_id)

    where = " AND ".join(condicoes)

    # Nota: FORMAT_DATE e FORMAT_TIMESTAMP do BQ não existem no SQLite.
    # Usaremos strftime ou trataremos no pandas.
    # Como as datas foram inseridas como strings ISO, podemos usar substr ou strftime.
    
    query = f"""
        SELECT
            l.numeroLinha                                                       AS `Número`,
            l.vista                                                             AS `Vista`,
            s.descricao                                                         AS `Serviço`,
            op.nomeFantasia                                                     AS `Operador`,
            ao.descricao                                                        AS `Área Operacional`,
            ts.descricao                                                        AS `Tipo Sistema`,
            ag.area                                                             AS `Área Geográfica`,
            pf.parametro                                                        AS `Parâmetro`,
            tv.descricao                                                        AS `Tipo Veículo`,
            l.kmIDA                                                             AS `KM Ida`,
            l.kmVOLTA                                                           AS `KM Volta`,
            l.classificacaoEspacial                                             AS `Classif. Espacial`,
            l.dataCriacaoLinha                                                  AS `Data Criação`,
            l.dataCadastro                                                      AS `Cadastrado em`
        FROM Linha l
        LEFT JOIN Servico                s  ON l.servico         = s.servicoID
        LEFT JOIN operador               op ON l.operador        = op.operadorID
        LEFT JOIN AreaOperacional        ao ON l.areaOperacional = ao.areaOperacionalID
        LEFT JOIN TipoSistema            ts ON l.tipoSistema     = ts.tipoSistemaID
        LEFT JOIN AreaGeograficaOperacao ag ON l.areaGeografica  = ag.areaGeograficaOperacaoID
        LEFT JOIN ParametroFuncional     pf ON l.parametro       = pf.parametroFuncionalID
        LEFT JOIN TipoVeiculo            tv ON l.frotaTipoVeiculo = tv.tipoVeiculoID
        WHERE {where}
        ORDER BY l.dataCadastro DESC
        LIMIT 500
    """

    df = _query_df(query, params=params)
    if df.empty:
        return df
    
    # Formatação de data no pandas para simular o comportamento original
    try:
        if 'Data Criação' in df.columns:
            df['Data Criação'] = pd.to_datetime(df['Data Criação']).dt.strftime('%d/%m/%Y')
        if 'Cadastrado em' in df.columns:
            df['Cadastrado em'] = pd.to_datetime(df['Cadastrado em']).dt.strftime('%d/%m/%Y %H:%M')
    except:
        pass

    return df
