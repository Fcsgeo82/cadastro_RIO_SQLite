# =============================================================
# mod_cadastro_ref.py — Cadastro das Tabelas de Referência
# Tabelas: AreaGeograficaOperacao, AreaOperacional, GrupamentoBRS,
#          Oficio, ParametroFuncional, Servico, TipoSistema,
#          TipoVeiculo, operador
# =============================================================

import uuid
from datetime import datetime, timezone

import streamlit as st

from config import get_connection
from db import listar_tabela


# ------------------------------------------------------------------
# HELPER — inserção genérica
# ------------------------------------------------------------------

def _inserir(table: str, row: dict) -> tuple[bool, str]:
    """Insere um registro no SQLite. Retorna (sucesso, mensagem)."""
    conn = get_connection()
    cols = ", ".join(row.keys())
    placeholders = ", ".join(["?" for _ in row])
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    try:
        conn.execute(sql, list(row.values()))
        conn.commit()
        conn.close()
        return True, "Registro cadastrado com sucesso!"
    except Exception as e:
        conn.close()
        return False, f"Erro no SQLite: {e}"


def _feedback(sucesso: bool, mensagem: str):
    if sucesso:
        st.success(f"✅ {mensagem}")
        st.cache_data.clear()
    else:
        st.error(f"❌ {mensagem}")


# ------------------------------------------------------------------
# FORMULÁRIOS — um por tabela
# ------------------------------------------------------------------

def _form_area_geografica():
    st.markdown("**Campos:** Área (nome), Número Inicial e Número Final do intervalo.")
    with st.form("form_area_geo", clear_on_submit=True):
        area          = st.text_input("Área *", placeholder="Ex: Zona Norte")
        col1, col2    = st.columns(2)
        with col1:
            num_inicial = st.number_input("Número Inicial", min_value=0, value=None)
        with col2:
            num_final   = st.number_input("Número Final",   min_value=0, value=None)
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          use_container_width=True)

    if submitted:
        if not area.strip():
            st.error("⚠️ O campo Área é obrigatório.")
            return
        row = {
            "areaGeograficaOperacaoID": str(uuid.uuid4()),
            "area":          area.strip(),
            "numeroInicial": int(num_inicial) if num_inicial is not None else None,
            "numeroFinal":   int(num_final)   if num_final   is not None else None,
        }
        _feedback(*_inserir("AreaGeograficaOperacao", row))


def _form_area_operacional():
    st.markdown("**Campos:** Descrição, Tipo e Cor de Referência.")
    with st.form("form_area_op", clear_on_submit=True):
        descricao     = st.text_input("Descrição *", placeholder="Ex: Área Central")
        col1, col2    = st.columns(2)
        with col1:
            tipo      = st.text_input("Tipo", placeholder="Ex: Urbano")
        with col2:
            cor       = st.text_input("Cor de Referência", placeholder="Ex: #FF5733 ou Vermelho")
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          use_container_width=True)

    if submitted:
        if not descricao.strip():
            st.error("⚠️ O campo Descrição é obrigatório.")
            return
        row = {
            "areaOperacionalID": str(uuid.uuid4()),
            "descricao":         descricao.strip(),
            "tipo":              tipo.strip() or None,
            "CorReferencia":     cor.strip()  or None,
        }
        _feedback(*_inserir("AreaOperacional", row))


def _form_grupamento_brs():
    st.markdown("**Campos:** Descrição (código numérico do grupamento BRS).")
    with st.form("form_grupamento", clear_on_submit=True):
        descricao = st.number_input("Descrição (número) *", min_value=0, value=None,
                                    placeholder="Ex: 101")
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          use_container_width=True)

    if submitted:
        if descricao is None:
            st.error("⚠️ O campo Descrição é obrigatório.")
            return
        row = {
            "grupamentoBRSID": str(uuid.uuid4()),
            "descricao":       int(descricao),
        }
        _feedback(*_inserir("GrupamentoBRS", row))


def _form_oficio():
    st.markdown("**Campos:** Número, Data, Assunto, Número do Processo e Linha relacionada.")
    with st.form("form_oficio", clear_on_submit=True):
        col1, col2    = st.columns(2)
        with col1:
            numero    = st.number_input("Número do Ofício *", min_value=1, value=None)
        with col2:
            data      = st.date_input("Data do Ofício *", value=None)

        assunto       = st.text_input("Assunto *", placeholder="Ex: Alteração de itinerário")
        col3, col4    = st.columns(2)
        with col3:
            num_proc  = st.text_input("Número do Processo", placeholder="Ex: 09/001234/2024")
        with col4:
            linha_rel = st.text_input("Linha Relacionada (ID)", placeholder="UUID da linha")
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          use_container_width=True)

    if submitted:
        faltando = []
        if numero  is None:       faltando.append("Número do Ofício")
        if data    is None:       faltando.append("Data do Ofício")
        if not assunto.strip():   faltando.append("Assunto")
        if faltando:
            st.error(f"⚠️ Campos obrigatórios: {', '.join(faltando)}")
            return
        agora = datetime.now(tz=timezone.utc).isoformat()
        row = {
            "oficioID":       str(uuid.uuid4()),
            "numeroOficio":   int(numero),
            "dataOficio":     str(data),
            "assunto":        assunto.strip(),
            "numeroProcesso": num_proc.strip() or None,
            "dataCadastro":   agora,
            "linha":          linha_rel.strip() or None,
        }
        _feedback(*_inserir("Oficio", row))


def _form_parametro_funcional():
    st.markdown("**Campos:** Nome do parâmetro funcional.")
    with st.form("form_parametro", clear_on_submit=True):
        parametro = st.text_input("Parâmetro *", placeholder="Ex: Padrão Básico")
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          use_container_width=True)

    if submitted:
        if not parametro.strip():
            st.error("⚠️ O campo Parâmetro é obrigatório.")
            return
        row = {
            "parametroFuncionalID": str(uuid.uuid4()),
            "parametro":            parametro.strip(),
        }
        _feedback(*_inserir("ParametroFuncional", row))


def _form_servico():
    st.markdown("**Campos:** Descrição e Prefixo do serviço.")
    with st.form("form_servico", clear_on_submit=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            prefixo   = st.text_input("Prefixo *", placeholder="Ex: BRT")
        with col2:
            descricao = st.text_input("Descrição *", placeholder="Ex: Bus Rapid Transit")
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          use_container_width=True)

    if submitted:
        faltando = []
        if not prefixo.strip():   faltando.append("Prefixo")
        if not descricao.strip(): faltando.append("Descrição")
        if faltando:
            st.error(f"⚠️ Campos obrigatórios: {', '.join(faltando)}")
            return
        row = {
            "servicoID":  str(uuid.uuid4()),
            "descricao":  descricao.strip(),
            "Prefixo":    prefixo.strip(),
        }
        _feedback(*_inserir("Servico", row))


def _form_tipo_sistema():
    st.markdown("**Campos:** Descrição e Sentido (número de sentidos da linha).")
    with st.form("form_tipo_sistema", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            descricao = st.text_input("Descrição *", placeholder="Ex: Circular, Radial")
        with col2:
            sentido   = st.number_input("Sentido", min_value=1, max_value=2, value=None,
                                        placeholder="1 ou 2")
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          use_container_width=True)

    if submitted:
        if not descricao.strip():
            st.error("⚠️ O campo Descrição é obrigatório.")
            return
        row = {
            "tipoSistemaID": str(uuid.uuid4()),
            "descricao":     descricao.strip(),
            "sentido":       int(sentido) if sentido is not None else None,
        }
        _feedback(*_inserir("TipoSistema", row))


def _form_tipo_veiculo():
    st.markdown("**Campos:** Descrição e Código do veículo.")
    with st.form("form_tipo_veiculo", clear_on_submit=True):
        col1, col2    = st.columns([3, 1])
        with col1:
            descricao = st.text_input("Descrição *", placeholder="Ex: Articulado, Convencional")
        with col2:
            codigo    = st.number_input("Código do Veículo", min_value=1, value=None)
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          use_container_width=True)

    if submitted:
        if not descricao.strip():
            st.error("⚠️ O campo Descrição é obrigatório.")
            return
        row = {
            "tipoVeiculoID":  str(uuid.uuid4()),
            "descricao":      descricao.strip(),
            "codigoVeiculo":  int(codigo) if codigo is not None else None,
        }
        _feedback(*_inserir("TipoVeiculo", row))


def _form_operador():
    st.markdown("**Campos:** Nome Fantasia, Razão Social, CNPJ, Termo e Data de Cadastro.")
    with st.form("form_operador", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome_fantasia = st.text_input("Nome Fantasia *", placeholder="Ex: Transportes Rio")
        with col2:
            razao_social  = st.text_input("Razão Social *",  placeholder="Ex: Transportes Rio S.A.")

        col3, col4 = st.columns(2)
        with col3:
            cnpj          = st.text_input("CNPJ *", placeholder="Ex: 00000000000100")
        with col4:
            data_cad      = st.date_input("Data de Cadastro", value=None)

        termo = st.text_input("Termo / Contrato", placeholder="Ex: Contrato 001/2020")
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          use_container_width=True)

    if submitted:
        faltando = []
        if not nome_fantasia.strip(): faltando.append("Nome Fantasia")
        if not razao_social.strip():  faltando.append("Razão Social")
        if not cnpj.strip():          faltando.append("CNPJ")
        if faltando:
            st.error(f"⚠️ Campos obrigatórios: {', '.join(faltando)}")
            return

        # Remove formatação do CNPJ e converte para INT64
        cnpj_num = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj_num) != 14:
            st.error("⚠️ CNPJ inválido. Informe 14 dígitos numéricos.")
            return

        row = {
            "operadorID":    str(uuid.uuid4()),
            "cnpj":          cnpj_num,
            "nomeFantasia":  nome_fantasia.strip(),
            "razaoSocial":   razao_social.strip(),
            "termo":         termo.strip() or None,
            "dataCadastro":  str(data_cad) if data_cad else None,
        }
        _feedback(*_inserir("operador", row))


# ------------------------------------------------------------------
# MAPA DE TABELAS
# ------------------------------------------------------------------

TABELAS = {
    "Área Geográfica de Operação": {
        "form":     _form_area_geografica,
        "icone":    "🗺️",
        "tabela":   "AreaGeograficaOperacao",
    },
    "Área Operacional": {
        "form":     _form_area_operacional,
        "icone":    "📍",
        "tabela":   "AreaOperacional",
    },
    "Grupamento BRS": {
        "form":     _form_grupamento_brs,
        "icone":    "🔢",
        "tabela":   "GrupamentoBRS",
    },
    "Ofício": {
        "form":     _form_oficio,
        "icone":    "📄",
        "tabela":   "Oficio",
    },
    "Parâmetro Funcional": {
        "form":     _form_parametro_funcional,
        "icone":    "⚙️",
        "tabela":   "ParametroFuncional",
    },
    "Serviço": {
        "form":     _form_servico,
        "icone":    "🚍",
        "tabela":   "Servico",
    },
    "Tipo de Sistema": {
        "form":     _form_tipo_sistema,
        "icone":    "🏷️",
        "tabela":   "TipoSistema",
    },
    "Tipo de Veículo": {
        "form":     _form_tipo_veiculo,
        "icone":    "🚌",
        "tabela":   "TipoVeiculo",
    },
    "Operador": {
        "form":     _form_operador,
        "icone":    "🏢",
        "tabela":   "operador",
    },
}


# ------------------------------------------------------------------
# RENDER PRINCIPAL
# ------------------------------------------------------------------

def render():
    st.markdown("### 🗂️ Cadastro de Tabelas de Referência")
    st.markdown("Selecione a tabela que deseja cadastrar e preencha o formulário.")

    # Seletor de tabela
    nomes   = list(TABELAS.keys())
    labels  = [f"{TABELAS[n]['icone']}  {n}" for n in nomes]
    escolha = st.selectbox("**Tabela**", labels, index=0)

    # Extrai nome sem ícone
    nome_sel = nomes[labels.index(escolha)]
    config   = TABELAS[nome_sel]

    st.divider()
    st.markdown(f"#### {config['icone']} {nome_sel}")

    # Chama o formulário correspondente
    config["form"]()

    # --- Listagem dos dados já cadastrados ---
    st.divider()
    st.markdown(f"#### 📊 Registros em {nome_sel}")
    
    df_lista = listar_tabela(config["tabela"])
    if df_lista.empty:
        st.info("Nenhum registro encontrado nesta tabela.")
    else:
        st.dataframe(df_lista, use_container_width=True, hide_index=True)
