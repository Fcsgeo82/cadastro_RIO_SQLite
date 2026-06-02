# =============================================================
# mod_cadastro_ref.py — Cadastro das Tabelas de Referência
# Tabelas: AreaGeograficaOperacao, AreaOperacional, GrupamentoBRS,
#          Oficio, ParametroFuncional, Servico, TipoSistema,
#          TipoVeiculo, operador
# =============================================================

import uuid
from datetime import datetime, timezone

import streamlit as st

from models.config import get_connection
from models.db import listar_tabela


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


def _excluir(table: str, pk_col: str, pk_val: str) -> tuple[bool, str]:
    """Exclui um registro no SQLite."""
    conn = get_connection()
    try:
        conn.execute(f"DELETE FROM {table} WHERE {pk_col} = ?", (pk_val,))
        conn.commit()
        conn.close()
        return True, "Registro excluído com sucesso!"
    except Exception as e:
        conn.close()
        return False, f"Erro ao excluir: {e}"


def _atualizar(table: str, pk_col: str, pk_val: str, new_values: dict) -> tuple[bool, str]:
    """Atualiza um registro no SQLite."""
    if not new_values: return True, "Sem alterações."
    conn = get_connection()
    sets = ", ".join([f"{k} = ?" for k in new_values.keys()])
    sql = f"UPDATE {table} SET {sets} WHERE {pk_col} = ?"
    try:
        conn.execute(sql, list(new_values.values()) + [pk_val])
        conn.commit()
        conn.close()
        return True, "Registro atualizado com sucesso!"
    except Exception as e:
        conn.close()
        return False, f"Erro ao atualizar: {e}"


def _feedback(sucesso: bool, mensagem: str):
    if sucesso:
        st.success(f"✅ {mensagem}")
        st.cache_data.clear()
    else:
        st.error(f"❌ {mensagem}")


# ------------------------------------------------------------------
# FORMULÁRIOS — um por tabela
# ------------------------------------------------------------------

def _form_parametro():
    st.markdown("**Campos:** Descrição do parâmetro.")
    with st.form("form_parametro", clear_on_submit=True):
        descricao = st.text_input("Descrição *", placeholder="Ex: Polarizada")
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          width='stretch')

    if submitted:
        if not descricao.strip():
            st.error("⚠️ O campo Descrição é obrigatório.")
            return
        row = {
            "parametroID": str(uuid.uuid4()),
            "descricao":   descricao.strip(),
        }
        _feedback(*_inserir("Parametro", row))


def _form_caracteristica():
    st.markdown("**Campos:** Descrição da característica.")
    with st.form("form_caracteristica", clear_on_submit=True):
        descricao = st.text_input("Descrição *", placeholder="Ex: Alimentadora")
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          width='stretch')

    if submitted:
        if not descricao.strip():
            st.error("⚠️ O campo Descrição é obrigatório.")
            return
        row = {
            "caracteristicaID": str(uuid.uuid4()),
            "descricao":        descricao.strip(),
        }
        _feedback(*_inserir("Caracteristica", row))


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
                                          width='stretch')

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
                                          width='stretch')

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
                                          width='stretch')

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


# _form_parametro_funcional removido (substituído por _form_parametro)


def _form_servico():
    st.markdown("**Campos:** Descrição e Prefixo do serviço.")
    with st.form("form_servico", clear_on_submit=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            prefixo   = st.text_input("Prefixo *", placeholder="Ex: BRT")
        with col2:
            descricao = st.text_input("Descrição *", placeholder="Ex: Bus Rapid Transit")
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          width='stretch')

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
                                          width='stretch')

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
                                          width='stretch')

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
                                          width='stretch')

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


def _form_tipo_propulsao():
    st.markdown("**Campos:** Descrição do tipo de propulsão.")
    with st.form("form_tipo_propulsao", clear_on_submit=True):
        descricao = st.text_input("Descrição *", placeholder="Ex: Diesel, Elétrico, Híbrido")
        submitted = st.form_submit_button("💾 Salvar", type="primary",
                                          width='stretch')

    if submitted:
        if not descricao.strip():
            st.error("⚠️ O campo Descrição é obrigatório.")
            return
        row = {
            "tipoPropulsaoID": str(uuid.uuid4()),
            "descricao":       descricao.strip(),
        }
        _feedback(*_inserir("TipoPropulsao", row))


def _form_tipologia_rede():
    st.markdown("**Campos:** Descrição da tipologia de rede.")
    with st.form("form_tipologia", clear_on_submit=True):
        descricao = st.text_input("Descrição *", placeholder="Ex: Dia Útil")
        submitted = st.form_submit_button("💾 Salvar", type="primary", width='stretch')

    if submitted:
        if not descricao.strip():
            st.error("⚠️ O campo Descrição é obrigatório.")
            return
        row = {
            "tipologiaID": str(uuid.uuid4()),
            "descricao":   descricao.strip(),
        }
        _feedback(*_inserir("TipologiaRede", row))


def _form_abrangencia_territorial():
    st.markdown("**Campos:** Descrição da abrangência territorial.")
    with st.form("form_abrangencia", clear_on_submit=True):
        descricao = st.text_input("Descrição *", placeholder="Ex: Serviço Local")
        submitted = st.form_submit_button("💾 Salvar", type="primary", width='stretch')

    if submitted:
        if not descricao.strip():
            st.error("⚠️ O campo Descrição é obrigatório.")
            return
        row = {
            "abrangenciaID": str(uuid.uuid4()),
            "descricao":     descricao.strip(),
        }
        _feedback(*_inserir("AbrangenciaTerritorial", row))


def _form_geometria_tracado():
    st.markdown("**Campos:** Classificação da geometria do traçado.")
    with st.form("form_geometria", clear_on_submit=True):
        classificacao = st.text_input("Classificação *", placeholder="Ex: Serviço Radial")
        submitted = st.form_submit_button("💾 Salvar", type="primary", width='stretch')

    if submitted:
        if not classificacao.strip():
            st.error("⚠️ O campo Classificação é obrigatório.")
            return
        row = {
            "geometriaID":   str(uuid.uuid4()),
            "classificacao": classificacao.strip(),
        }
        _feedback(*_inserir("GeometriaTracado", row))


def _form_hierarquia_atendimento():
    st.markdown("**Campos:** Classificação da hierarquia de atendimento.")
    with st.form("form_hierarquia", clear_on_submit=True):
        classificacao = st.text_input("Classificação *", placeholder="Ex: Distribuidora")
        submitted = st.form_submit_button("💾 Salvar", type="primary", width='stretch')

    if submitted:
        if not classificacao.strip():
            st.error("⚠️ O campo Classificação é obrigatório.")
            return
        row = {
            "hierarquiaID":  str(uuid.uuid4()),
            "classificacao": classificacao.strip(),
        }
        _feedback(*_inserir("HierarquiaAtendimento", row))


# ------------------------------------------------------------------
# MAPA DE TABELAS
# ------------------------------------------------------------------

TABELAS = {
    "Área Operacional": {
        "form":     _form_area_operacional,
        "icone":    "📍",
        "tabela":   "AreaOperacional",
        "pk":       "areaOperacionalID",
    },
    "Característica": {
        "form":     _form_caracteristica,
        "icone":    "✨",
        "tabela":   "Caracteristica",
        "pk":       "caracteristicaID",
    },
    "Grupamento BRS": {
        "form":     _form_grupamento_brs,
        "icone":    "🔢",
        "tabela":   "GrupamentoBRS",
        "pk":       "grupamentoBRSID",
    },
    "Ofício": {
        "form":     _form_oficio,
        "icone":    "📄",
        "tabela":   "Oficio",
        "pk":       "oficioID",
    },
    "Operador": {
        "form":     _form_operador,
        "icone":    "🏢",
        "tabela":   "operador",
        "pk":       "operadorID",
    },
    "Parâmetro": {
        "form":     _form_parametro,
        "icone":    "⚙️",
        "tabela":   "Parametro",
        "pk":       "parametroID",
    },
    "Serviço": {
        "form":     _form_servico,
        "icone":    "🚍",
        "tabela":   "Servico",
        "pk":       "servicoID",
    },
    "Tipo de Sistema": {
        "form":     _form_tipo_sistema,
        "icone":    "🏷️",
        "tabela":   "TipoSistema",
        "pk":       "tipoSistemaID",
    },
    "Tipo de Veículo": {
        "form":     _form_tipo_veiculo,
        "icone":    "🚌",
        "tabela":   "TipoVeiculo",
        "pk":       "tipoVeiculoID",
    },
    "Tipo de Propulsão": {
        "form":     _form_tipo_propulsao,
        "icone":    "⚡",
        "tabela":   "TipoPropulsao",
        "pk":       "tipoPropulsaoID",
    },
    "Tipologia de Rede": {
        "form":     _form_tipologia_rede,
        "icone":    "🕸️",
        "tabela":   "TipologiaRede",
        "pk":       "tipologiaID",
    },
    "Abrangência Territorial": {
        "form":     _form_abrangencia_territorial,
        "icone":    "🌍",
        "tabela":   "AbrangenciaTerritorial",
        "pk":       "abrangenciaID",
    },
    "Geometria do Traçado": {
        "form":     _form_geometria_tracado,
        "icone":    "📏",
        "tabela":   "GeometriaTracado",
        "pk":       "geometriaID",
    },
    "Hierarquia de Atendimento": {
        "form":     _form_hierarquia_atendimento,
        "icone":    "🪜",
        "tabela":   "HierarquiaAtendimento",
        "pk":       "hierarquiaID",
    },
}


# ------------------------------------------------------------------
# RENDER PRINCIPAL
# ------------------------------------------------------------------

def render():
    user_role = st.session_state.get("role", "user")
    is_vis = (user_role == "visualizador")
    can_edit = (user_role in ["admin", "editor"])

    st.markdown("### 🗂️ Tabelas de Referência")
    
    if is_vis:
        st.markdown("Consulta de registros autorizados.")
        # Visualizador vê apenas Ofício
        nomes = ["Ofício"]
    else:
        st.markdown("Selecione a tabela que deseja cadastrar e preencha o formulário.")
        nomes = list(TABELAS.keys())

    # Seletor de tabela
    labels  = [f"{TABELAS[n]['icone']}  {n}" for n in nomes]
    
    if len(nomes) == 1:
        nome_sel = nomes[0]
        st.info(f"Visualizando: **{labels[0]}**")
    else:
        escolha = st.selectbox("**Tabela**", labels, index=0)
        nome_sel = nomes[labels.index(escolha)]
    
    config = TABELAS[nome_sel]

    st.divider()
    st.markdown(f"#### {config['icone']} {nome_sel}")

    # Chama o formulário correspondente (apenas se NÃO for visualizador)
    if not is_vis:
        config["form"]()
    else:
        st.info("ℹ️ Você tem permissão apenas para **visualizar** os registros desta tabela.")

    # --- Listagem dos dados já cadastrados ---
    st.divider()
    st.markdown(f"#### 📊 Registros em {nome_sel}")
    
    df_lista = listar_tabela(config["tabela"])
    
    # 1. Filtro Global (Excepcional para Ofícios)
    if nome_sel == "Ofício":
        filtro_oficio = st.text_input("🔍 Filtrar Ofícios (Número, Assunto ou Processo)", placeholder="Digite para buscar...")
        if filtro_oficio:
             termo = filtro_oficio.lower()
             import pandas as pd
             # Busca em todas as colunas convertendo para string
             mask = df_lista.astype(str).apply(lambda row: row.str.lower().str.contains(termo, regex=False).any(), axis=1)
             # Se o apply falhar por algum motivo de tipo, tentamos coluna por coluna
             if mask.empty or not mask.any():
                 mask = pd.Series(False, index=df_lista.index)
                 for col in df_lista.columns:
                     mask |= df_lista[col].astype(str).str.lower().str.contains(termo, regex=False)
             df_lista = df_lista[mask]

    if df_lista.empty:
        st.info("Nenhum registro encontrado nesta tabela.")
    else:
        if can_edit:
            st.info("💡 **Dica:** Você pode editar os valores diretamente na tabela e clicar em 'Salvar Alterações'.")
            
            # 2. Edição via data_editor
            edited_df = st.data_editor(
                df_lista,
                width='stretch',
                hide_index=True,
                num_rows="fixed", # Edição apenas, exclusão via botão abaixo
                key=f"editor_{config['tabela']}"
            )
            
            # Botão para salvar edições
            if not edited_df.equals(df_lista):
                if st.button("💾 Salvar Alterações na Tabela", type="primary", key="btn_save_ref"):
                    pks_originais = set(df_lista[config["pk"]].astype(str))
                    for _, row in edited_df.iterrows():
                        pk_val = str(row[config["pk"]])
                        if pk_val in pks_originais:
                            orig_row = df_lista[df_lista[config["pk"]].astype(str) == pk_val].iloc[0]
                            cambios = {}
                            for col in df_lista.columns:
                                if str(row[col]) != str(orig_row[col]):
                                    cambios[col] = row[col]
                            if cambios:
                                _atualizar(config["tabela"], config["pk"], pk_val, cambios)
                    
                    st.success("✅ Alterações salvas com sucesso!")
                    st.cache_data.clear()
                    st.rerun()

            # 3. Exclusão explícita
            st.markdown("---")
            st.markdown("#### 🗑️ Excluir Registro")
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                # Busca uma coluna amigável para o label
                cols_possiveis = ['descricao', 'nomeFantasia', 'classificacao', 'numeroOficio', 'numero']
                label_col = next((c for c in df_lista.columns if c in cols_possiveis), df_lista.columns[0])
                
                # Cria dicionário de opções
                dict_excluir = {
                    f"{row[label_col]} (ID: {str(row[config['pk']])[:8]}...)": row[config['pk']]
                    for _, row in df_lista.iterrows()
                }
                selecionado = st.selectbox("Selecione o item para remover", options=list(dict_excluir.keys()), key=f"sel_del_{config['tabela']}")
            
            with col_btn:
                st.write("##") # Espaçamento para alinhar com o selectbox
                if st.button("🗑️ Excluir", type="primary", width='stretch', key=f"btn_del_ref_{config['tabela']}"):
                    pk_para_deletar = dict_excluir[selecionado]
                    sucesso, msg = _excluir(config["tabela"], config["pk"], pk_para_deletar)
                    _feedback(sucesso, msg)
                    st.rerun()

        else:
            # Visualização simples para Visualizador
            st.dataframe(df_lista, width='stretch', hide_index=True)
