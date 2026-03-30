# =============================================================
# mod_consulta.py — Consulta de Linhas
# =============================================================

import io
import streamlit as st
from db import (
    consultar_linhas, opcoes,
    carregar_areas_operacionais, carregar_operadores, carregar_tipos_sistema,
)


@st.cache_data(ttl=300, show_spinner=False)
def _refs_consulta():
    return {
        "areas_op":      opcoes(carregar_areas_operacionais()),
        "operadores":    opcoes(carregar_operadores()),
        "tipos_sistema": opcoes(carregar_tipos_sistema()),
    }


def render():
    st.markdown("### 🔍 Consultar Linhas")
    st.markdown("Filtre por número, área operacional, operador ou tipo de sistema.")

    refs = _refs_consulta()

    # ── Filtros ──────────────────────────────────────────────────
    col1, col2 = st.columns([1, 3])
    with col1:
        filtro_numero = st.text_input("Número da Linha", placeholder="Ex: 474")

    col3, col4, col5 = st.columns(3)
    with col3:
        area_op_labels  = ["Todas"] + list(refs["areas_op"].keys())
        sel_area        = st.selectbox("Área Operacional", area_op_labels)
        area_op_id      = refs["areas_op"].get(sel_area, "")
    with col4:
        op_labels       = ["Todos"] + list(refs["operadores"].keys())
        sel_op          = st.selectbox("Operador", op_labels)
        operador_id     = refs["operadores"].get(sel_op, "")
    with col5:
        ts_labels       = ["Todos"] + list(refs["tipos_sistema"].keys())
        sel_ts          = st.selectbox("Tipo de Sistema", ts_labels)
        tipo_sistema_id = refs["tipos_sistema"].get(sel_ts, "")

    col_b1, col_b2, _ = st.columns([1, 1, 4])
    with col_b1:
        buscar       = st.button("🔍 Buscar", type="primary", use_container_width=True)
    with col_b2:
        listar_todas = st.button("📋 Listar Todas", use_container_width=True)

    st.divider()

    # ── Execução ─────────────────────────────────────────────────
    if buscar:
        with st.spinner("Consultando SQLite..."):
            df = consultar_linhas(
                numero              = filtro_numero,
                area_operacional_id = area_op_id,
                operador_id         = operador_id,
                tipo_sistema_id     = tipo_sistema_id,
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

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "KM Ida":   st.column_config.NumberColumn("KM Ida",   format="%.1f km"),
                "KM Volta": st.column_config.NumberColumn("KM Volta", format="%.1f km"),
            }
        )

        # ── Exportar CSV ─────────────────────────────────────────
        buf = io.StringIO()
        df.to_csv(buf, index=False, encoding="utf-8-sig")
        st.download_button(
            label     = "⬇️ Exportar CSV",
            data      = buf.getvalue().encode("utf-8-sig"),
            file_name = "linhas_onibus.csv",
            mime      = "text/csv",
        )
