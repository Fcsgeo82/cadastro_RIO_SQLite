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
import mod_historico

import mod_historico
import mod_usuarios
import db

# --- Configuração da página ---
st.set_page_config(
    page_title="Linhas de Ônibus",
    page_icon="🚌",
    layout="wide",
)

# Auth & Session init
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None

# Logout via query
if st.query_params.get('logout'):
    st.session_state.pop('logged_in', None)
    st.session_state.pop('user', None)
    st.session_state.pop('role', None)
    st.query_params.clear()
    st.rerun()

# Reset token handler
reset_token = st.query_params.get('reset_token')
if reset_token:
    user_id = db.validate_reset_token(reset_token)
    if user_id:
        st.title("Resetar Senha")
        with st.form("reset_form"):
            new_pwd = st.text_input("Nova senha", type="password")
            confirm = st.text_input("Confirmar", type="password")
            if st.form_submit_button("Atualizar Senha", type="primary"):
                if new_pwd == confirm and len(new_pwd) >= 6:
                    success, msg = db.reset_password(user_id, new_pwd)
                    st.query_params.clear()
                    if success:
                        st.success("Senha atualizada! Faça login.")
                    else:
                        st.error(msg)
                else:
                    st.error("Senhas não coincidem ou muito curta.")
        st.stop()
    else:
        st.error("Token inválido ou expirado.")
        st.rerun()

if not st.session_state.get('logged_in'):
    st.markdown('<div style="text-align:center;padding:2rem;background:linear-gradient(135deg,#f5f7fa,#c3cfe2);border-radius:12px;margin:2rem 0"><h2>Acesso ao Sistema</h2><p>Faça login para continuar.</p></div>', unsafe_allow_html=True)
    
    tab_login, tab_forgot = st.tabs(["Login", "Esqueci Senha"])
    
    with tab_login:
        with st.form(key="login_form", clear_on_submit=True):
            username = st.text_input("Usuário", placeholder="admin ou user")
            password = st.text_input("Senha", type="password")
            col_btn1, col_btn2 = st.columns([4,1])
            with col_btn1:
                submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            if submitted:
                user = db.verify_login(username, password)
                if user and "error" not in user:
                    st.session_state.update({'logged_in': True, 'user': user['username'], 'role': user['role']})
                    st.success(f"Bem-vindo, {user['username']} ({user['role']})!")
                    st.rerun()
                elif user.get("error") == "locked":
                    st.error(f"🚫 {user.get('message')}")
                else:
                    st.error("Usuário ou senha incorretos.")
    
    with tab_forgot:
        username = st.text_input("Usuário")
        col_f1, col_f2 = st.columns([4,1])
        with col_f1:
            if st.button("Enviar Link de Reset", type="secondary", use_container_width=True):
                success, result = db.generate_reset_token(username)
                if success:
                    email = db.get_user_email(username)
                    if email:
                        try:
                            eu = st.secrets.get("GMAIL_USER")
                            ep = st.secrets.get("GMAIL_APP_PASS")
                            au = st.secrets.get("APP_URL", "http://localhost:8501")
                        except Exception:
                            eu = None
                            ep = None
                            au = "http://localhost:8501"
                        if not eu or not ep:
                            st.warning("Configure .streamlit/secrets.toml com GMAIL_USER e GMAIL_APP_PASS")
                        elif db.send_reset_email(email, result, eu, ep, au):
                            st.success(f"Link enviado para {email}")
                        else:
                            st.error("Erro ao enviar email.")
                    else:
                        st.error("Usuário não encontrado.")
                else:
                    st.error(result)
    st.stop()

# Session timeout JS (30min inactivity)
st.markdown("""
<script>
let timer;
function resetTimer() {
  clearTimeout(timer);
  timer = setTimeout(() => { window.location.href = '?logout=true'; }, 30*60*1000);
}
['mousemove','mousedown','click','scroll','keypress'].forEach(e => document.addEventListener(e, resetTimer, true));
resetTimer();
</script>
""", unsafe_allow_html=True)

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
    tab_labels = ["🔍  Consultar Linhas"]
    if st.session_state.role in ["admin", "editor"]:
        tab_labels += ["➕  Cadastrar Linha", "🗂️  Tabelas de Referência"]
    if st.session_state.role == "admin":
        tab_labels += ["👥  Usuários"]
    
    tabs = st.tabs(tab_labels)
    
    with tabs[0]:
        mod_consulta.render()
    
    if st.session_state.role in ["admin", "editor"]:
        with tabs[1]:
            mod_cadastro.render()
        with tabs[2]:
            mod_cadastro_ref.render()
    
    if st.session_state.role == "admin" and len(tab_labels) > 3:
        with tabs[3]:
            mod_usuarios.render()

elif aba == "Ficha":
    linha_id = st.session_state.get("linha_acao_id")
    mod_ficha.render(linha_id)

elif aba == "Editar":
    linha_id = st.session_state.get("linha_acao_id")
    mod_edicao.render(linha_id)

elif aba == "Historico":
    linha_id = st.session_state.get("linha_acao_id")
    mod_historico.render(linha_id)

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
    
    if st.session_state.get('logged_in'):
        st.divider()
        st.info(f"**{st.session_state.user}** | {st.session_state.role.upper()}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.pop('user', None)
            st.session_state.pop('role', None)
            st.rerun()
    
    st.divider()
    if st.button("Recarregar App"):
        st.rerun()

# --- Footer ---
st.markdown(
    '<div class="custom-footer">Sistema de Linhas de Ônibus • Streamlit + SQLite</div>',
    unsafe_allow_html=True
)
