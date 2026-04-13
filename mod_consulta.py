# =============================================================
# mod_consulta.py — Consulta de Linhas
# =============================================================

import io
import streamlit as st
from db import (
    consultar_linhas, opcoes,
    carregar_areas_operacionais, carregar_operadores, carregar_tipos_sistema,
    carregar_caracteristicas, carregar_parametros_novos, carregar_tipos_veiculo,
    carregar_grupamentos
)


@st.cache_data(ttl=300, show_spinner=False)
def _refs_consulta():
    # Force refresh: 2026-04-08 20:00
    return {
        "areas_op":       opcoes(carregar_areas_operacionais()),
        "operadores":     opcoes(carregar_operadores()),
        "tipos_sistema":  opcoes(carregar_tipos_sistema()),
        "caracteristicas": opcoes(carregar_caracteristicas()),
        "parametros":     opcoes(carregar_parametros_novos()),
        "tipos_veiculo":  opcoes(carregar_tipos_veiculo()),
        "grupamentos":    opcoes(carregar_grupamentos()),
    }


def render():
    st.markdown("### 🔍 Consultar Linhas")
    st.markdown("Filtre por número, área operacional, operador ou tipo de operação.")

    refs = _refs_consulta()

    # ── Filtros ──────────────────────────────────────────────────
    col_busca, _ = st.columns([2, 1])
    with col_busca:
        filtro_geral = st.text_input("🔍 Busca Geral (Qualquer campo)", placeholder="Ex: nome de rua, bairro, operador...")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filtro_numero = st.text_input("Número da Linha", placeholder="Ex: 474")
    with col2:
        area_op_labels  = ["Todas"] + list(refs["areas_op"].keys())
        sel_area        = st.selectbox("Área Operacional", area_op_labels)
        area_op_id      = refs["areas_op"].get(sel_area, "")
    with col3:
        op_labels       = ["Todos"] + list(refs["operadores"].keys())
        sel_op          = st.selectbox("Operador", op_labels)
        operador_id     = refs["operadores"].get(sel_op, "")
    with col4:
        ts_labels       = ["Todos"] + list(refs["tipos_sistema"].keys())
        sel_ts          = st.selectbox("Tipo de Operação", ts_labels)
        tipo_sistema_id = refs["tipos_sistema"].get(sel_ts, "")

    # Segunda linha de filtros
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        param_labels    = ["Todos"] + list(refs["parametros"].keys())
        sel_param       = st.selectbox("Parâmetro", param_labels)
        parametro_id    = refs["parametros"].get(sel_param, "")
    with col6:
        char_labels     = ["Todas"] + list(refs["caracteristicas"].keys())
        sel_char        = st.selectbox("Característica", char_labels)
        caracteristica_id = refs["caracteristicas"].get(sel_char, "")
    with col7:
        tv_labels       = ["Todos"] + list(refs["tipos_veiculo"].keys())
        sel_tv          = st.selectbox("Frota Autorizada", tv_labels)
        frota_v_id      = refs["tipos_veiculo"].get(sel_tv, "")
    with col8:
        grup_labels     = ["Todos"] + list(refs["grupamentos"].keys())
        sel_grup        = st.selectbox("Grupamento BRS", grup_labels)
        grupamento_id   = refs["grupamentos"].get(sel_grup, "")

    col_b1, col_b2, _ = st.columns([1, 1, 4])
    with col_b1:
        buscar       = st.button("🔍 Buscar", type="primary", width='stretch')
    with col_b2:
        listar_todas = st.button("📋 Listar Todas", width='stretch')

    st.divider()

    # ── Execução ─────────────────────────────────────────────────
    if buscar:
        with st.spinner("Consultando SQLite..."):
            df = consultar_linhas(
                numero              = filtro_numero,
                area_operacional_id = area_op_id,
                operador_id         = operador_id,
                tipo_sistema_id     = tipo_sistema_id,
                termo_geral         = filtro_geral,
                caracteristica_id   = caracteristica_id,
                parametro_id        = parametro_id,
                frota_tipo_veiculo_id = frota_v_id,
                grupamento_brs_id   = grupamento_id,
            )
        st.session_state["resultado_consulta"] = df

    elif listar_todas:
        with st.spinner("Carregando todas as linhas..."):
            df = consultar_linhas()
        st.session_state["resultado_consulta"] = df

    # ── Exibição ─────────────────────────────────────────────────
    if "resultado_consulta" in st.session_state:
        df = st.session_state["resultado_consulta"]

        if df.empty:
            st.info("Nenhuma linha encontrada com os filtros aplicados.")
            return

        total = len(df)
        st.markdown(f"**{total}** {'linha encontrada' if total == 1 else 'linhas encontradas'}")

        evento = st.dataframe(
            df,
            width='stretch',
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "linhaID": None,  # Oculta o ID da UI
                "KM Ida":   st.column_config.NumberColumn("KM Ida",   format="%.1f km"),
                "KM Volta": st.column_config.NumberColumn("KM Volta", format="%.1f km"),
            }
        )

        # ── Ações Customizadas para a Linha Selecionada ──────────
        if evento and len(evento.selection.rows) > 0:
            idx = evento.selection.rows[0]
            linha_selecionada = df.iloc[idx]
            
            if "linhaID" not in linha_selecionada:
                st.warning("⚠️ Cache da sessão desatualizado. Por favor, clique em **Listar Todas** ou **Buscar** novamente para ativar as ações!")
            else:
                linha_id = linha_selecionada["linhaID"]
    
                st.markdown("---")
                st.markdown(f"**Ações para Linha: {linha_selecionada.get('Número', '')}**")
    
                user_role = st.session_state.get("role", "user")
                
                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1.5, 1.5, 1.6, 1.5])
                
                with col_btn1:
                    if st.button("👁️ Ver Ficha", width='stretch', type="primary"):
                        st.session_state["linha_acao_id"] = linha_id
                        st.session_state["aba_ativa"] = "Ficha"
                        st.rerun()
                
                if user_role in ["admin", "editor"]:
                    with col_btn2:
                        if st.button("✏️ Alterar", width='stretch'):
                            st.session_state["linha_acao_id"] = linha_id
                            st.session_state["aba_ativa"] = "Editar"
                            st.rerun()
                
                with col_btn3:
                    if st.button("🕰️ Histórico", width='stretch'):
                        st.session_state["linha_acao_id"] = linha_id
                        st.session_state["aba_ativa"] = "Historico"
                        st.rerun()
                
                if user_role == "admin":
                    with col_btn4:
                        if st.button("🗑️ Excluir", width='stretch'):
                            st.session_state["linha_acao_id"] = linha_id
                            st.session_state["linha_numero_excluir"] = linha_selecionada.get('Número', '')
                            st.session_state["aba_ativa"] = "Excluir"
                            st.rerun()

        # ── Exportar CSV ─────────────────────────────────────────
        buf = io.StringIO()
        df.to_csv(buf, index=False, encoding="utf-8-sig")
        st.download_button(
            label     = "⬇️ Exportar CSV",
            data      = buf.getvalue().encode("utf-8-sig"),
            file_name = "linhas_onibus.csv",
            mime      = "text/csv",
        )
