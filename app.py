# =============================================================
# App.py — Cadastro de Linhas com SQLite
# =============================================================

import os
import streamlit as st

import mod_cadastro
import mod_cadastro_ref
import mod_consulta
import mod_ficha
import mod_edicao

# --- Configuração da página ---
st.set_page_config(
    page_title="Linhas de Ônibus",
    page_icon="🚌",
    layout="wide",
)

# --- CSS customizado ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

h1, h2, h3, .stTabs [data-baseweb="tab"], .stButton > button {
    font-family: 'Manrope', sans-serif !important;
}

h1, h2, h3 {
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
}

/* Header */
.app-header {
    background: linear-gradient(135deg, #1a3a5c 0%, #2d6a9f 100%);
    padding: 24px 32px;
    border-radius: 12px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 18px;
}
.app-header h1 {
    color: white !important;
    font-size: 1.8rem !important;
    margin: 0 !important;
}
.app-header p {
    color: rgba(255,255,255,0.75);
    margin: 4px 0 0;
    font-size: 0.9rem;
}
.header-icon { font-size: 2.5rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 2px solid #dde3ec;
}
.stTabs [data-baseweb="tab"] {
    font-weight: 600;
    font-size: 0.95rem;
    padding: 10px 22px;
    border-radius: 8px 8px 0 0;
    color: #6b7a99;
}
.stTabs [aria-selected="true"] {
    color: #1a3a5c !important;
    border-bottom: 3px solid #f07d00 !important;
}

/* Botão primário */
.stButton > button[kind="primary"] {
    background: #1a3a5c;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 10px 24px;
    transition: background 0.2s;
}
.stButton > button[kind="primary"]:hover {
    background: #2d6a9f !important;
}

/* Inputs */
.stTextInput input, .stNumberInput input, .stSelectbox select {
    border-radius: 7px !important;
    border: 1px solid #dde3ec !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #2d6a9f !important;
    box-shadow: 0 0 0 3px rgba(45,106,159,0.15) !important;
}

/* Dataframe */
.stDataFrame { border-radius: 10px; overflow: hidden; }

/* Footer */
footer { visibility: hidden; }
.custom-footer {
    text-align: center;
    color: #6b7a99;
    font-size: 0.8rem;
    margin-top: 40px;
    padding-top: 16px;
    border-top: 1px solid #dde3ec;
}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="app-header">
    <span class="header-icon">🚌</span>
    <div>
        <h1>Sistema de Linhas de Ônibus</h1>
        <p>Cadastro e Consulta via SQLite</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Rotas Dinâmicas ---
aba = st.session_state.get("aba_ativa", "Principal")

if aba == "Principal":
    # --- Abas principais ---
    aba_consulta, aba_cadastro, aba_ref = st.tabs([
        "🔍  Consultar Linhas",
        "➕  Cadastrar Linha",
        "🗂️  Tabelas de Referência",
    ])

    with aba_consulta:
        mod_consulta.render()

    with aba_cadastro:
        mod_cadastro.render()

    with aba_ref:
        mod_cadastro_ref.render()

elif aba == "Ficha":
    linha_id = st.session_state.get("linha_acao_id")
    mod_ficha.render(linha_id)

elif aba == "Editar":
    linha_id = st.session_state.get("linha_acao_id")
    mod_edicao.render(linha_id)

elif aba == "Excluir":
    numero = st.session_state.get("linha_numero_excluir")
    linha_id = st.session_state.get("linha_acao_id")
    
    st.markdown(f"### 🗑️ Excluir Linha {numero}")
    st.warning("Tem certeza que deseja excluir esta linha permanentemente? Esta ação não pode ser desfeita.")
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ Confirmar Exclusão", type="primary", use_container_width=True):
            from db import excluir_linha
            sucesso, msg = excluir_linha(linha_id)
            if sucesso:
                st.session_state["_mensagem_sucesso"] = msg
            else:
                st.session_state["_mensagem_erro"] = msg
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()
    with col_no:
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()

# ── Feedback global ──
if "_mensagem_sucesso" in st.session_state:
    st.success(f"✅ {st.session_state.pop('_mensagem_sucesso')}")
if "_mensagem_erro" in st.session_state:
    st.error(f"❌ {st.session_state.pop('_mensagem_erro')}")

# --- Sidebar info ---
with st.sidebar:
    st.markdown("## 📊 Status")
    st.success("✅ Conectado ao SQLite")
    st.caption("Arquivo: `database_RIO.db`")
    st.divider()
    if st.button("🔄 Recarregar App"):
        st.rerun()

# --- Footer ---
st.markdown(
    '<div class="custom-footer">Sistema de Linhas de Ônibus • Streamlit + SQLite</div>',
    unsafe_allow_html=True
)
