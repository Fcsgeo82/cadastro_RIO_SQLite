# =============================================================
# db.py — Operações com SQLite
# Base: database_RIO.db
# =============================================================

import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import smtplib
from email.mime.text import MIMEText

import pandas as pd
import sqlite3
from models.config import get_connection
import streamlit as st


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
        SELECT areaOperacionalID, codigo, corReferencia
        FROM AreaOperacional
        ORDER BY codigo
    """)
    if df.empty:
        return df
    
    # Montar label: (codigo - corReferencia)
    df['label'] = (
        df['codigo'].astype(str) + " - " + 
        df['corReferencia'].fillna("Sem Cor")
    )
    
    return df[['areaOperacionalID', 'label']].rename(columns={"areaOperacionalID": "id"})


def carregar_parametros_novos() -> pd.DataFrame:
    df = _query_df(f"""
        SELECT parametroID, descricao
        FROM Parametro
        ORDER BY descricao
    """)
    if df.empty:
        return df
    return df.rename(columns={"parametroID": "id", "descricao": "label"})


def carregar_caracteristicas() -> pd.DataFrame:
    df = _query_df(f"""
        SELECT caracteristicaID, descricao
        FROM Caracteristica
        ORDER BY descricao
    """)
    if df.empty:
        return df
    return df.rename(columns={"caracteristicaID": "id", "descricao": "label"})


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


# Deprecated: carregar_parametros e carregar_areas_geograficas removidos.


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
    df = _query_df("""
        SELECT oficioID, numeroOficio, dataOficio
        FROM Oficio
        ORDER BY dataOficio DESC, numeroOficio DESC
    """)
    if df.empty:
        return df
        
    df['numeroOficio'] = pd.to_numeric(df['numeroOficio'], errors='coerce').fillna(0).astype(int)
    df['ano'] = pd.to_datetime(df['dataOficio'], errors='coerce').dt.strftime('%Y').fillna('XXXX')
    
    df['label'] = "Ofício SMTR-RIO " + df['numeroOficio'].apply(lambda x: f"{x:02d}") + "/" + df['ano']
    
    return df[['oficioID', 'label', 'dataOficio']].rename(columns={"oficioID": "id"})

def carregar_assuntos_oficios() -> dict:
    """Retorna um dicionário mapeando oficioID -> assunto."""
    df = _query_df("SELECT oficioID, assunto FROM Oficio")
    if df.empty:
        return {}
    df['assunto'] = df['assunto'].fillna("Sem assunto")
    return dict(zip(df['oficioID'], df['assunto']))

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
        "via":                   dados.get("via", "").strip() or None,
        "areaOperacional":       dados.get("areaOperacional") or None,
        "oficio":                dados.get("oficio") or None,
        "oficioprimeiroHistorico": dados.get("oficioprimeiroHistorico") or None,
        "oficioUltimaAlteracao": dados.get("oficioUltimaAlteracao") or None,
        "tipoSistema":           dados.get("tipoSistema") or None,
        "kmIDA":                 float(dados["kmIDA"]) if dados.get("kmIDA") else None,
        "kmVOLTA":               float(dados["kmVOLTA"]) if dados.get("kmVOLTA") else None,
        "parametro_novo":        dados.get("parametro_novo") or None,
        "caracteristica":        dados.get("caracteristica") or None,
        "grupamentoBRS":         dados.get("grupamentoBRS"),
        "frotaTipoVeiculo":      dados.get("frotaTipoVeiculo") or None,
        "frotaUltimoOficio":     dados.get("frotaUltimoOficio") or None,
        "frotaDataOficio":       dados.get("frotaDataOficio") or None,
        "observacao":            dados.get("observacao", "").strip() or None,
        "dataCadastro":          agora,
        "ultimaAtualizacao":     agora,
    }

    cols = ", ".join(row.keys())
    placeholders = ", ".join(["?" for _ in row])
    sql = f"INSERT INTO Linha ({cols}) VALUES ({placeholders})"

    try:
        cursor = conn.cursor()
        cursor.execute(sql, list(row.values()))
        
        # Inserir Itinerários se fornecidos
        itinerarios = dados.get("itinerarios", [])
        oficios_it  = dados.get("itinerarios_oficios", {})
        if itinerarios:
            salvar_itinerarios(cursor, row["linhaID"], itinerarios, oficios_it)
            
        conn.commit()
        
        # Registrar evento de criação
        numero_linha = row["numeroLinha"]
        linha_id = row["linhaID"]
        oficio_id = dados.get("oficio")
        
        conn.close()
        
        # Log after commit (connection closed, so we use _exec which opens its own connection)
        registrar_log(linha_id, numero_linha, "Criação", None, oficio_id, None)
        
        return True, f"Linha {row['numeroLinha']} cadastrada com sucesso!"
    except Exception as e:
        conn.rollback()
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
    termo_geral: str = "",
    caracteristica_id: str = "",
    parametro_id: str = "",
    frota_tipo_veiculo_id: str = "",
    grupamento_brs_id: str = "",
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
    if caracteristica_id:
        condicoes.append("l.caracteristica = ?")
        params.append(caracteristica_id)
    if parametro_id:
        condicoes.append("l.parametro_novo = ?")
        params.append(parametro_id)
    if frota_tipo_veiculo_id:
        condicoes.append("l.frotaTipoVeiculo = ?")
        params.append(frota_tipo_veiculo_id)
    if grupamento_brs_id:
        condicoes.append("l.grupamentoBRS = ?")
        params.append(grupamento_brs_id)
        
    if termo_geral.strip():
        termo = f"%{termo_geral.strip()}%"
        # Busca abrangente em múltiplos campos (inclusive via JOINs)
        cond_geral = """
            (l.numeroLinha LIKE ? OR 
             l.vista LIKE ? OR 
             l.via LIKE ? OR 
             l.observacao LIKE ? OR 
             l.areaGeografica LIKE ? OR 
             l.classificacaoEspacial LIKE ? OR 
             l.parametro LIKE ? OR
             s.descricao LIKE ? OR
             op.nomeFantasia LIKE ? OR
             ao.descricao LIKE ? OR
             ts.descricao LIKE ? OR
             p.descricao LIKE ? OR
             c.descricao LIKE ?)
        """
        condicoes.append(cond_geral)
        params.extend([termo] * 13)

    where = " AND ".join(condicoes)

    # Nota: FORMAT_DATE e FORMAT_TIMESTAMP do BQ não existem no SQLite.
    # Usaremos strftime ou trataremos no pandas.
    # Como as datas foram inseridas como strings ISO, podemos usar substr ou strftime.
    
    query = f"""
        SELECT
            l.linhaID,
            l.numeroLinha                                                       AS `Número`,
            l.vista                                                             AS `Vista`,
            l.via                                                               AS `Via`,
            s.descricao                                                         AS `Serviço`,
            op.nomeFantasia                                                     AS `Operador`,
            ao.descricao                                                        AS `Área Operacional`,
            ts.descricao                                                        AS `Tipo Sistema`,
            p.descricao                                                         AS `Parâmetro`,
            c.descricao                                                         AS `Característica`,
            l.kmIDA                                                             AS `KM Ida`,
            l.kmVOLTA                                                           AS `KM Volta`,
            l.dataCriacaoLinha                                                  AS `Data Criação`,
            l.dataCadastro                                                      AS `Cadastrado em`
        FROM Linha l
        LEFT JOIN Servico                s  ON l.servico         = s.servicoID
        LEFT JOIN operador               op ON l.operador        = op.operadorID
        LEFT JOIN AreaOperacional        ao ON l.areaOperacional = ao.areaOperacionalID
        LEFT JOIN TipoSistema            ts ON l.tipoSistema     = ts.tipoSistemaID
        LEFT JOIN Parametro              p  ON l.parametro_novo  = p.parametroID
        LEFT JOIN Caracteristica         c  ON l.caracteristica  = c.caracteristicaID
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

# ------------------------------------------------------------------
# CRUD - Linha (Leitura Única, Atualização, Exclusão)
# ------------------------------------------------------------------

def obter_linha_por_id(linha_id: str) -> dict:
    """Retorna os dados completos de uma linha pelo ID em formato de dicionário."""
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Linha WHERE linhaID = ?", (linha_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            d = dict(row)
            # Buscar itinerários associados
            d["itinerarios"] = obter_itinerarios(linha_id)
            return d
        return {}
    except Exception as e:
        print(f"Erro ao obter linha: {e}")
        return {}

def obter_itinerarios(linha_id: str) -> list[dict]:
    """Retorna lista de dicionários com os pontos do itinerário da linha."""
    df = _query_df("SELECT * FROM Itinerario WHERE linhaRefID = ? ORDER BY tipo, sentido, ordem", [linha_id])
    return df.to_dict("records")

def obter_oficios_itinerarios(linha_id: str) -> list[dict]:
    """Retorna os ofícios únicos vinculados aos itinerários de uma linha para o histórico."""
    sql = """
        SELECT DISTINCT i.oficio, i.tipo, o.dataOficio
        FROM Itinerario i
        JOIN Oficio o ON i.oficio = o.oficioID
        WHERE i.linhaRefID = ? AND i.oficio IS NOT NULL
    """
    df = _query_df(sql, [linha_id])
    return df.to_dict("records")

def salvar_itinerarios(cursor, linha_id: str, itinerarios: list[dict], oficios_tipos: dict = None):
    """Helper para salvar (deletar e inserir) itinerários de uma linha em uma transação."""
    # oficios_tipos -> {"R": "id_oficio_regular", "A": "id_oficio_alternativo"}
    if oficios_tipos is None:
        oficios_tipos = {}
        
    # Deleta existentes primeiro
    cursor.execute("DELETE FROM Itinerario WHERE linhaRefID = ?", (linha_id,))
    
    # Inserir novos
    for i, it in enumerate(itinerarios):
        # Campos: itinerarioID, linhaRefID, sentido, ordem, logradouro, bairro, observacao, tipo, oficio
        tipo = it.get("tipo", "R")
        sql_it = """
            INSERT INTO Itinerario (itinerarioID, linhaRefID, sentido, ordem, logradouro, bairro, observacao, tipo, oficio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql_it, (
            str(uuid.uuid4()),
            linha_id,
            str(it.get("sentido", "0")),
            it.get("ordem", i),
            it.get("logradouro", ""),
            it.get("bairro", ""),
            it.get("observacao", ""),
            tipo,
            oficios_tipos.get(tipo)
        ))

def atualizar_linha(linha_id: str, dados: dict) -> tuple[bool, str]:
    """Atualiza uma linha existente e atualiza_ultimaAtualizacao."""
    conn = get_connection()
    agora = datetime.now(tz=timezone.utc).isoformat()
    
    # Criar dict de atualização. Não atualizamos linhaID nem dataCadastro.
    row = {
        "numeroLinha":           dados.get("numeroLinha", "").strip(),
        "dataCriacaoLinha":      str(dados["dataCriacaoLinha"]) if dados.get("dataCriacaoLinha") else None,
        "servico":               dados.get("servico") or None,
        "operador":              dados.get("operador") or None,
        "vista":                 dados.get("vista", "").strip() or None,
        "via":                   dados.get("via", "").strip() or None,
        "areaOperacional":       dados.get("areaOperacional") or None,
        "oficio":                dados.get("oficio") or None,
        "oficioprimeiroHistorico": dados.get("oficioprimeiroHistorico") or None,
        "oficioUltimaAlteracao": dados.get("oficioUltimaAlteracao") or None,
        "tipoSistema":           dados.get("tipoSistema") or None,
        "kmIDA":                 float(dados["kmIDA"]) if dados.get("kmIDA") else None,
        "kmVOLTA":               float(dados["kmVOLTA"]) if dados.get("kmVOLTA") else None,
        "parametro_novo":        dados.get("parametro_novo") or None,
        "caracteristica":        dados.get("caracteristica") or None,
        "grupamentoBRS":         dados.get("grupamentoBRS"),
        "frotaTipoVeiculo":      dados.get("frotaTipoVeiculo") or None,
        "frotaUltimoOficio":     dados.get("frotaUltimoOficio") or None,
        "frotaDataOficio":       dados.get("frotaDataOficio") or None,
        "observacao":            dados.get("observacao", "").strip() or None,
        "ultimaAtualizacao":     agora,
    }

    set_clause = ", ".join([f"{k} = ?" for k in row.keys()])
    values = list(row.values())
    values.append(linha_id)
    
    sql = f"UPDATE Linha SET {set_clause} WHERE linhaID = ?"
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, values)
        
        # Atualizar Itinerários
        if "itinerarios" in dados:
            oficios_it = dados.get("itinerarios_oficios", {})
            salvar_itinerarios(cursor, linha_id, dados["itinerarios"], oficios_it)
            
        conn.commit()
        
        # Registrar evento de alteração
        numero_linha = row["numeroLinha"]
        oficio_id = dados.get("oficioUltimaAlteracao") or dados.get("oficio")
        
        conn.close()
        
        # Log after commit
        registrar_log(linha_id, numero_linha, "Alteração", None, oficio_id, None)
        
        return True, f"Linha {row['numeroLinha']} atualizada com sucesso!"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Erro ao atualizar no SQLite: {e}"

def excluir_linha(linha_id: str, oficio_exclusao: str = None) -> tuple[bool, str]:
    """Exclui uma linha movendo para LinhaExcluida."""
    conn = get_connection()
    agora = datetime.now(tz=timezone.utc).isoformat()
    usuario = st.session_state.get("user", "sistema")
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Linha WHERE linhaID = ?", (linha_id,))
        linha = cursor.fetchone()
        if not linha:
            conn.close()
            return False, "Linha não encontrada."
        
        colunas_linha = [desc[0] for desc in cursor.description]
        linha_dict = dict(zip(colunas_linha, linha))
        
        linhas_cols = ["linhaID", "numeroLinha", "dataCriacaoLinha", "servico", "operador", "vista", "via",
                       "areaOperacional", "oficio", "oficioprimeiroHistorico", "oficioUltimaAlteracao",
                       "tipoSistema", "kmIDA", "kmVOLTA", "parametro_novo", "caracteristica", "grupamentoBRS",
                       "frotaTipoVeiculo", "frotaUltimoOficio", "frotaDataOficio", "observacao", "dataCadastro",
                       "ultimaAtualizacao", "areaGeografica", "classificacaoEspacial", "parametro"]
        
        valores = [linha_dict.get(c) for c in linhas_cols]
        valores.extend([oficio_exclusao, agora, usuario])
        
        insert_sql = f"""
            INSERT INTO LinhaExcluida ({', '.join(linhas_cols)}, oficioExclusao, dataExclusao, usuarioExclusao)
            VALUES ({', '.join(['?'] * len(valores))})
        """
        cursor.execute(insert_sql, valores)
        
        cursor.execute("DELETE FROM Linha WHERE linhaID = ?", (linha_id,))
        
        conn.commit()
        
        # Registrar evento de exclusão
        numero_linha = linha_dict.get("numeroLinha", "")
        
        conn.close()
        
        # Log after commit
        registrar_log(linha_id, numero_linha, "Exclusão", usuario, oficio_exclusao, None)
        
        return True, "Linha excluída com sucesso!"
    except Exception as e:
        conn.close()
        return False, f"Erro ao excluir linha: {e}"


def _exec(sql: str, params: list = None) -> bool:
    """Executa comando non-query (INSERT/UPDATE/DELETE)."""
    conn = get_connection()
    try:
        conn.execute(sql, params or [])
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB exec error: {e}")
        conn.close()
        return False


# ------------------------------------------------------------------
# LOGS — Tabela LogEventos (Audit Trail)
# ------------------------------------------------------------------

def registrar_log(linha_id: str, numero_linha: str, tipo_evento: str, usuario: str = None, oficio_id: str = None, detalhes: str = None) -> bool:
    """Registra um evento na tabela de auditoria LogEventos."""
    if usuario is None:
        try:
            usuario = st.session_state.get("user", "sistema")
        except:
            usuario = "sistema"
    
    log_id = str(uuid.uuid4())
    data_evento = datetime.now(tz=timezone.utc).isoformat()
    
    sql = """
        INSERT INTO LogEventos (logID, linhaID, numeroLinha, tipoEvento, dataEvento, usuario, oficioID, detalhes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = [log_id, linha_id, numero_linha, tipo_evento, data_evento, usuario, oficio_id, detalhes]
    
    return _exec(sql, params)


def consultar_historico(
    tipo_evento: str = "",
    numero: str = "",
    data_inicio: str = None,
    data_fim: str = None,
) -> pd.DataFrame:
    """Consulta o histórico de eventos (LogEventos) com filtros."""
    condicoes = ["1=1"]
    params = []
    
    if tipo_evento and tipo_evento != "Todos":
        condicoes.append("l.tipoEvento = ?")
        params.append(tipo_evento)
    
    if numero.strip():
        condicoes.append("CAST(l.numeroLinha AS TEXT) LIKE ?")
        params.append(f"%{numero.strip()}%")
    
    if data_inicio:
        condicoes.append("l.dataEvento >= ?")
        params.append(data_inicio)
    
    if data_fim:
        condicoes.append("l.dataEvento <= ?")
        params.append(data_fim)
    
    where = " AND ".join(condicoes)
    
    # Subquery to check if line still exists in Linha (active) table
    linha_existe = "(SELECT COUNT(*) FROM Linha WHERE Linha.linhaID = l.linhaID) > 0"

    query = f"""
        SELECT
            l.dataEvento                                    AS `Data`,
            l.tipoEvento                                    AS `Tipo`,
            l.numeroLinha                                   AS `Linha`,
            l.linhaID,
            COALESCE(CAST(o.numeroOficio AS TEXT), '-')     AS `Ofício`,
            COALESCE(o.assunto, '-')                        AS `Assunto`,
            l.usuario                                       AS `Usuário`,
            CASE WHEN {linha_existe} THEN 'ativa' ELSE 'excluida' END AS `status`
        FROM LogEventos l
        LEFT JOIN Oficio o ON l.oficioID = o.oficioID
        WHERE {where}
        ORDER BY l.dataEvento DESC
        LIMIT 500
    """
    
    df = _query_df(query, params=params)
    if df.empty:
        return df
    
    try:
        df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%d/%m/%Y %H:%M')
    except:
        pass
    
    return df


def verify_login(username: str, password: str) -> dict:
    """Verifica login com rate limiting. Retorna user dict ou {}."""
    df = _query_df("SELECT * FROM Usuarios WHERE username = ?", [username])
    if df.empty:
        return {}
    user_row = df.iloc[0]
    
    # Check lockout
    lockout_until = user_row.get("lockout_until")
    if isinstance(lockout_until, bytes):
        lockout_until = lockout_until.decode("utf-8", errors="ignore")
    if lockout_until:
        lockout_time = datetime.fromisoformat(str(lockout_until).replace('Z', '+00:00'))
        if datetime.now(timezone.utc) < lockout_time:
            remaining = (lockout_time - datetime.now(timezone.utc)).seconds // 60
            return {"error": "locked", "message": f"Conta bloqueada. Tente novamente em {remaining} minuto(s)."}
    
    # Verify password
    stored_hash = user_row["password_hash"]
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode()
    if bcrypt.checkpw(password.encode(), stored_hash):
        # Reset failed attempts on success
        _exec("UPDATE Usuarios SET failed_attempts = 0, lockout_until = NULL WHERE userID = ?", [user_row["userID"]])
        user_dict = user_row.to_dict()
        user_dict.pop("password_hash", None)
        return user_dict
    
    # Increment failed attempts
    raw_failed = user_row.get("failed_attempts", 0)
    if isinstance(raw_failed, bytes):
        failed = int.from_bytes(raw_failed, byteorder="little") + 1
    else:
        failed = int(raw_failed or 0) + 1
    if failed >= 5:
        lockout = datetime.now(timezone.utc) + timedelta(minutes=15)
        _exec("UPDATE Usuarios SET failed_attempts = ?, lockout_until = ? WHERE userID = ?", [failed, lockout.isoformat(), user_row["userID"]])
        return {"error": "locked", "message": "Muitas tentativas falhas. Conta bloqueada por 15 minutos."}
    else:
        _exec("UPDATE Usuarios SET failed_attempts = ? WHERE userID = ?", [failed, user_row["userID"]])
        return {"error": "failed", "message": f"Usuário ou senha incorretos. Tentativas: {failed}/5"}


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Valida força da senha: mínimo 8 chars, 1 maiúscula, 1 número, 1 símbolo."""
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres."
    if not any(c.isupper() for c in password):
        return False, "Senha deve conter pelo menos 1 letra maiúscula."
    if not any(c.isdigit() for c in password):
        return False, "Senha deve conter pelo menos 1 número."
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Senha deve conter pelo menos 1 símbolo."
    return True, "OK"


def generate_reset_token(username: str) -> tuple[bool, str]:
    """Gera token reset para user, retorna (success, token or msg)."""
    df = _query_df("SELECT userID FROM Usuarios WHERE username = ?", [username])
    if df.empty:
        return False, "User not found"
    user_id = df.iloc[0]["userID"]
    token = str(uuid.uuid4())
    expiry = datetime.now(timezone.utc) + timedelta(hours=24)
    expiry_str = expiry.isoformat()
    if _exec("UPDATE Usuarios SET reset_token = ?, reset_expiry = ? WHERE userID = ?", [token, expiry_str, user_id]):
        return True, token
    return False, "Token generation failed"


def validate_reset_token(token: str) -> str:
    """Valida token, retorna userID or empty string."""
    now_str = datetime.now(timezone.utc).isoformat()
    df = _query_df("SELECT userID FROM Usuarios WHERE reset_token = ? AND reset_expiry > ?", [token, now_str])
    if df.empty:
        return ""
    return df.iloc[0]["userID"]


def reset_password(user_id: str, new_password: str) -> tuple[bool, str]:
    """Reseta senha, limpa token."""
    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    if _exec("UPDATE Usuarios SET password_hash = ?, reset_token = NULL, reset_expiry = NULL WHERE userID = ?", [new_hash, user_id]):
        return True, "Password updated"
    return False, "Reset failed"


def send_reset_email(email: str, token: str, email_user: str, email_pass: str, app_url: str) -> bool:
    """Envia email de reset usando Gmail creds."""
    try:
        msg = MIMEText(f"Clique para resetar senha: {app_url}/?reset_token={token}\nExpira em 24h.")
        msg['Subject'] = 'Reset Senha - Sistema Linhas RIO'
        msg['From'] = email_user
        msg['To'] = email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_user, email_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False


def get_user_email(username: str) -> str:
    """Pega email do user."""
    df = _query_df("SELECT email FROM Usuarios WHERE username = ?", [username])
    return df.iloc[0]["email"] if not df.empty else ""


def consultar_linhas_excluidas(
    numero: str = "",
    area_operacional_id: str = "",
    operador_id: str = "",
) -> pd.DataFrame:
    """Consulta linhas excluídas."""
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
    
    where = " AND ".join(condicoes)
    
    query = f"""
        SELECT
            l.linhaID,
            l.numeroLinha                                                       AS `Número`,
            l.vista                                                             AS `Vista`,
            l.via                                                               AS `Via`,
            s.descricao                                                         AS `Serviço`,
            op.nomeFantasia                                                     AS `Operador`,
            ao.descricao                                                        AS `Área Operacional`,
            ts.descricao                                                        AS `Tipo Sistema`,
            l.oficioExclusao                                                    AS `Ofício Exclusão`,
            l.dataExclusao                                                      AS `Data Exclusão`,
            l.usuarioExclusao                                                   AS `Usuário`
        FROM LinhaExcluida l
        LEFT JOIN Servico                s  ON l.servico         = s.servicoID
        LEFT JOIN operador               op ON l.operador        = op.operadorID
        LEFT JOIN AreaOperacional        ao ON l.areaOperacional = ao.areaOperacionalID
        LEFT JOIN TipoSistema            ts ON l.tipoSistema     = ts.tipoSistemaID
        WHERE {where}
        ORDER BY l.dataExclusao DESC
        LIMIT 500
    """
    
    df = _query_df(query, params=params)
    if df.empty:
        return df
    
    try:
        if 'Data Exclusão' in df.columns:
            df['Data Exclusão'] = pd.to_datetime(df['Data Exclusão']).dt.strftime('%d/%m/%Y %H:%M')
    except:
        pass
    
    return df


def obter_linha_excluida_por_id(linha_id: str) -> dict:
    """Retorna os dados completos de uma linha excluída pelo ID."""
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM LinhaExcluida WHERE linhaID = ?", (linha_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {}
        
        dados = dict(row)
        
        cursor.execute("""
            SELECT numeroOficio, dataOficio, assunto 
            FROM Oficio 
            WHERE oficioID = ?
        """, (dados.get("oficioExclusao"),))
        oficio_row = cursor.fetchone()
        conn.close()
        
        if oficio_row:
            dados["oficioExclusaoInfo"] = dict(oficio_row)
        
        return dados
    except Exception as e:
        print(f"Erro ao obter linha excluída: {e}")
        return {}
