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
    df = _query_df("""
        SELECT oficioID, numeroOficio, dataOficio
        FROM Oficio
        ORDER BY dataOficio DESC, numeroOficio DESC
    """)
    if df.empty:
        return df
        
    df['numeroOficio'] = pd.to_numeric(df['numeroOficio'], errors='coerce').fillna(0).astype(int)
    df['ano'] = pd.to_datetime(df['dataOficio'], errors='coerce').dt.strftime('%Y').fillna('XXXX')
    
    df['label'] = "Ofício SMTR-A " + df['numeroOficio'].apply(lambda x: f"{x:02d}") + "/" + df['ano']
    
    return df[['oficioID', 'label']].rename(columns={"oficioID": "id"})

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
        "areaGeografica":        dados.get("areaGeografica") or None,
        "classificacaoEspacial": (dados.get("classificacaoEspacial") or "").strip() or None,
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
            l.linhaID,
            l.numeroLinha                                                       AS `Número`,
            l.vista                                                             AS `Vista`,
            l.via                                                               AS `Via`,
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
            return dict(row)
        return {}
    except Exception as e:
        print(f"Erro ao obter linha: {e}")
        return {}

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
        "areaGeografica":        dados.get("areaGeografica") or None,
        "classificacaoEspacial": (dados.get("classificacaoEspacial") or "").strip() or None,
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
        "ultimaAtualizacao":     agora,
    }

    set_clause = ", ".join([f"{k} = ?" for k in row.keys()])
    values = list(row.values())
    values.append(linha_id)
    
    sql = f"UPDATE Linha SET {set_clause} WHERE linhaID = ?"
    
    try:
        conn.execute(sql, values)
        conn.commit()
        conn.close()
        return True, f"Linha {row['numeroLinha']} atualizada com sucesso!"
    except Exception as e:
        conn.close()
        return False, f"Erro ao atualizar no SQLite: {e}"

def excluir_linha(linha_id: str) -> tuple[bool, str]:
    """Exclui uma linha pelo ID."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM Linha WHERE linhaID = ?", (linha_id,))
        conn.commit()
        conn.close()
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


def verify_login(username: str, password: str) -> dict:
    """Verifica login com rate limiting. Retorna user dict ou {}."""
    df = _query_df("SELECT * FROM Usuarios WHERE username = ?", [username])
    if df.empty:
        return {}
    user_row = df.iloc[0]
    
    # Check lockout
    lockout_until = user_row.get("lockout_until")
    if lockout_until:
        lockout_time = datetime.fromisoformat(lockout_until.replace('Z', '+00:00'))
        if datetime.now(timezone.utc) < lockout_time:
            remaining = (lockout_time - datetime.now(timezone.utc)).seconds // 60
            return {"error": "locked", "message": f"Conta bloqueada. Tente novamente em {remaining} minuto(s)."}
    
    # Verify password
    if bcrypt.checkpw(password.encode(), user_row["password_hash"].encode()):
        # Reset failed attempts on success
        _exec("UPDATE Usuarios SET failed_attempts = 0, lockout_until = NULL WHERE userID = ?", [user_row["userID"]])
        user_dict = user_row.to_dict()
        user_dict.pop("password_hash", None)
        return user_dict
    
    # Increment failed attempts
    failed = user_row.get("failed_attempts", 0) + 1
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
