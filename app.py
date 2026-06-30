# =============================================================
# App.py — Cadastro de Linhas com SQLite
# =============================================================

import os
import io
import mimetypes
from datetime import datetime

import pandas as pd
import streamlit as st

# --- Fix para Windows/Pinggy: Garante que arquivos JS sejam servidos com o MIME type correto ---
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/javascript', '.js')

# --- Imports do Projeto ---
from models import db
from models.db import (
    consultar_historico, 
    obter_linha_excluida_por_id, 
    carregar_oficios, 
    carregar_assuntos_oficios,
    opcoes,
    excluir_linha
)
from views import (
    mod_cadastro, 
    mod_cadastro_ref, 
    mod_consulta, 
    mod_ficha, 
    mod_edicao, 
    mod_historico, 
    mod_usuarios, 
    mod_gtfs
)
from views.mod_cadastro import _carregar_todas_referencias
from utils.ui_components import render_logo, obter_label

# --- Configuração da página ---
st.set_page_config(
    page_title="Linhas de Ônibus",
    page_icon="🚌",
    layout="wide",
)

# --- Configuração da Página de Rosto ---
# URL da foto de ônibus (substitua pela URL da foto desejada)
FOTO_ONIBUS_URL = "https://prefeitura.rio/wp-content/uploads/2025/12/obinus-paes.jpg"

# --- Auth & Session init ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None
if 'show_login' not in st.session_state:
    st.session_state.show_login = False

# Roteamento de ações via parâmetros de URL
action = st.query_params.get('action')
if action == 'public':
    st.session_state.update({'logged_in': True, 'user': 'Visitante', 'role': 'user'})
    st.query_params.clear()
    st.rerun()
elif action == 'login':
    st.session_state.show_login = True
    st.query_params.clear()
    st.rerun()
elif action == 'landing':
    st.session_state.show_login = False
    st.query_params.clear()
    st.rerun()

# Logout via query
if st.query_params.get('logout'):
    st.session_state.pop('logged_in', None)
    st.session_state.pop('user', None)
    st.session_state.pop('role', None)
    st.session_state.show_login = False
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
    if not st.session_state.get('show_login', False):
        logo_html = render_logo("400px")
        
        # Define o conteúdo da esquerda dependendo da presença de imagem
        if FOTO_ONIBUS_URL:
            left_side_html = f'<img src="{FOTO_ONIBUS_URL}" class="landing-img" alt="Ônibus Rio"/>'
        else:
            left_side_html = """
            <div class="landing-placeholder">
                <div class="placeholder-icon">🚌</div>
                <div class="placeholder-title">Rede Integrada de Ônibus</div>
                <div class="placeholder-subtitle">Prefeitura do Rio</div>
            </div>
            """
        
        st.markdown(f"""
        <style>
        html, body, .stApp {{
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            height: 100dvh !important;
            background-color: #f4f6f9 !important;
        }}

        [data-testid="collapsedControl"] {{ display: none !important; }}
        section[data-testid="stSidebar"] {{ display: none !important; }}
        header {{ display: none !important; }}
        footer {{ display: none !important; }}

        .stApp > header {{ display: none !important; }}
        .stApp > footer {{ display: none !important; }}

        .block-container {{
            padding: 0 !important;
            max-width: 100% !important;
            height: 100dvh !important;
        }}

        .element-container:has(.landing-container) {{
            height: 100dvh !important;
        }}

        .landing-container {{
            background-color: #ffdc00;
            display: flex;
            height: 100dvh;
            width: 100%;
            overflow: hidden;
            padding: 0;
            box-sizing: border-box;
            border: 10px solid #ffffff;
            border-radius: 20px;
        }}

        .landing-left {{
            flex: 1.4;
            overflow: hidden;
            position: relative;
            border: 12px solid #ffdc00;
            border-radius: 50px;
            box-sizing: border-box;
        }}

        .landing-img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}

        .landing-placeholder {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100%;
            width: 100%;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #ffffff;
            font-family: 'Manrope', sans-serif;
            text-align: center;
            padding: 30px;
            box-sizing: border-box;
        }}

        .placeholder-icon {{
            font-size: clamp(48px, 5vw, 96px);
            margin-bottom: clamp(12px, 2vh, 24px);
            animation: float 3s ease-in-out infinite;
        }}

        .placeholder-title {{
            font-size: clamp(18px, 2.2vw, 32px);
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: clamp(4px, 1vh, 10px);
            color: #ffffff !important;
        }}

        .placeholder-subtitle {{
            font-size: clamp(11px, 1.2vw, 16px);
            color: #94a3b8;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        @keyframes float {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
            100% {{ transform: translateY(0px); }}
        }}

        .landing-right {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: clamp(12px, 2vh, 28px) clamp(20px, 3vw, 50px);
            box-sizing: border-box;
            gap: clamp(60px, 1.5vh, 24px);
        }}

        .landing-logo-box {{
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }}

        .landing-logo-box img {{
            width: 100%;
            max-width: min(440px, 34vw);
            height: auto;
        }}

        .landing-buttons-box {{
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: clamp(12px, 1.5vh, 20px);
            align-items: center;
        }}

        .btn-landing-main, .btn-landing-secondary {{
            background-color: #000000;
            color: #ffdc00 !important;
            text-decoration: none !important;
            font-family: 'Manrope', sans-serif;
            font-weight: 800;
            font-size: clamp(13px, 1.3vw, 18px);
            letter-spacing: 0.05em;
            text-align: center;
            padding: clamp(14px, 1.8vh, 22px) clamp(16px, 2vw, 28px);
            border-radius: 6px;
            width: 100%;
            max-width: min(440px, 34vw);
            display: block;
            box-sizing: border-box;
            transition: all 0.2s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
            border: none;
            cursor: pointer;
        }}

        .btn-landing-main:hover, .btn-landing-secondary:hover {{
            background-color: #222222;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.25);
        }}

        .btn-landing-internal {{
            background-color: #444444;
            color: #ffffff !important;
            text-decoration: none !important;
            font-family: 'Manrope', sans-serif;
            font-weight: 800;
            font-size: clamp(13px, 1.3vw, 18px);
            letter-spacing: 0.05em;
            text-align: center;
            padding: clamp(14px, 1.8vh, 22px) clamp(16px, 2vw, 28px);
            border-radius: 6px;
            width: 100%;
            max-width: min(440px, 34vw);
            display: block;
            box-sizing: border-box;
            transition: all 0.2s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
            border: none;
            cursor: pointer;
        }}

        .btn-landing-internal:hover {{
            background-color: #222222;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.25);
        }}

        .landing-top {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: clamp(18px, 2.5vh, 36px);
            width: 100%;
        }}

        .landing-welcome {{
            font-family: 'Manrope', sans-serif;
            font-size: clamp(14px, 1.4vw, 20px);
            font-weight: 600;
            color: #000000;
            text-align: center;
        }}

        .landing-bottom {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: clamp(14px, 2vh, 28px);
            width: 100%;
        }}

        .landing-welcome {{
            font-family: 'Manrope', sans-serif;
            font-size: clamp(20px, 1.4vw, 30px);
            font-weight: 600;
            color: #000000;
            text-align: center;
        }}

        .landing-bottom {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: clamp(6px, 0.8vh, 12px);
            width: 100%;
        }}

        .landing-conditions {{
            font-family: 'Manrope', sans-serif;
            font-size: clamp(9px, 0.8vw, 12px);
            color: #555555;
            text-align: justify;
            max-width: min(440px, 34vw);
            line-height: 1.5;
        }}

        .landing-footer {{
            font-family: 'Manrope', sans-serif;
            font-size: clamp(10px, 0.9vw, 13px);
            font-weight: 700;
            color: #000000;
            text-align: center;
        }}

        .landing-footer a {{
            color: #000000;
            text-decoration: underline;
        }}

        .landing-footer a:hover {{
            color: #333333;
        }}

        @media (max-width: 768px) {{
            html, body, .stApp {{
                overflow: auto !important;
            }}
            .landing-container {{
                flex-direction: column;
                height: auto;
                min-height: 100dvh;
            }}
            .landing-left {{
                flex: none;
                height: 35vh;
                min-height: 200px;
            }}
            .landing-right {{
                padding: 24px 16px;
            }}
            .landing-logo-box {{
                margin-top: 24px;
            }}
            .landing-logo-box img {{
                max-width: 280px;
            }}
            .btn-landing-main, .btn-landing-secondary {{
                width: 100%;
                max-width: 100%;
            }}
            .landing-logo-box img {{
                max-width: 260px;
            }}
            .btn-landing-main, .btn-landing-secondary {{
                width: 100%;
                max-width: 100%;
            }}
            .landing-conditions {{
                max-width: 100%;
            }}
        }}
        </style>
        
        <div class="landing-container">
            <div class="landing-left">
                {left_side_html}
            </div>
            <div class="landing-right">
                <div class="landing-top">
                    <div class="landing-logo-box">
                        {logo_html}
                    </div>
                    <div class="landing-welcome">Seja Bem-vindo!</div>
                </div>
                <div class="landing-buttons-box">
                    <a href="?action=public" target="_self" class="btn-landing-main">CONSULTA DE LINHAS</a>
                    <a href="https://siurb.rio/portal/apps/webappviewer/index.html?id=e928b21ba61b430582eb3557d615a2f3" target="_blank" class="btn-landing-secondary">CONSULTA MAPA</a>
                    <a href="?action=login" target="_self" class="btn-landing-internal" style="margin-top: 30px;">🔒 ACESSO INTERNO</a>
                </div>
                <div class="landing-bottom">
                    <div class="landing-conditions">
                        <strong>Condições de Uso:</strong><br>
                        Todas as informações apresentadas pelo aplicativo têm caráter meramente informativo, não substituindo documentos oficiais, e podem ser utilizadas livremente desde que se faça referência à SMTR como fonte de informação.
                    </div>
                    <div class="landing-footer">
                        PREFEITURA DO RIO | <a href="https://transportes.prefeitura.rio/" target="_blank">SMTR</a>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    else:
        # --- Tela de Login Tradicional ---
        logo_html = render_logo("230px")
        
        st.markdown(f"""
        <style>
        /* Esconde elementos padrão do Streamlit */
        [data-testid="collapsedControl"] {{ display: none !important; }}
        section[data-testid="stSidebar"] {{ display: none !important; }}
        header {{ visibility: hidden !important; }}
        footer {{ visibility: hidden !important; }}

        .login-header {{
            background: linear-gradient(135deg, #ffdc00 0%, #ffdc00 100%);
            padding: 25px 30px;
            border-radius: 12px;
            margin: 1rem 0 2rem;
            text-align: center;
        }}
        .login-header h2 {{
            color: #000000 !important;
            font-size: 1.8rem !important;
            margin: 15px 0 5px !important;
        }}
        .login-header p {{
            color: #000000;
            margin: 0;
            font-size: 1rem;
        }}
        </style>
        <div class="login-header">
            <div class="logo-box">{logo_html}</div>
            <h2>Acesso ao Sistema Rede Integrada de Ônibus</h2>
            <p>Faça login para continuar</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_forgot = st.tabs(["Login", "Esqueci Senha"])
        
        with tab_login:
            with st.form(key="login_form", clear_on_submit=True):
                username = st.text_input("Usuário", placeholder="admin ou user")
                password = st.text_input("Senha", type="password")
                col_btn1, col_btn2 = st.columns([1,1])
                with col_btn1:
                    submitted = st.form_submit_button("Entrar", type="primary", width='stretch')
                with col_btn2:
                    public_access = st.form_submit_button("Acesso Público", type="secondary", width='stretch')
                    
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
                
                if public_access:
                    st.session_state.update({'logged_in': True, 'user': 'Visitante', 'role': 'user'})
                    st.success("Acessando como visitante...")
                    st.rerun()
        
        with tab_forgot:
            username_forgot = st.text_input("Usuário", key="forgot_user")
            if st.button("Enviar Link de Reset", type="secondary", width='stretch'):
                success, result = db.generate_reset_token(username_forgot)
                if success:
                    email = db.get_user_email(username_forgot)
                    if email:
                        try:
                            eu = st.secrets.get("GMAIL_USER")
                            ep = st.secrets.get("GMAIL_APP_PASS")
                            au = st.secrets.get("APP_URL", "http://localhost:8501")
                        except Exception:
                            eu = ep = None
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
        
        # Botão de voltar para a página de rosto
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ Voltar para a Página Inicial", key="voltar_landing", use_container_width=True):
            st.session_state.show_login = False
            st.rerun()
            
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
    background: #000000;
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

# --- Header com Logo ---
logo_html_header = render_logo("230px")
subtitle = "Cadastro e Consulta"

st.markdown(f"""
<style>
.header-wrapper {{
    background: linear-gradient(135deg, #ffdc00 0%, #ffdc00 100%);
    padding: 14px 20px;
    border-radius: 12px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 25px;
}}
.header-wrapper h1 {{
    color: #000000 !important;
    font-size: 2rem !important;
    margin: 0 !important;
}}
.header-wrapper p {{
    color: #000000;
    margin: 2px 0 0;
    font-size: 1rem;
}}
.logo-box {{
    background: linear-gradient(135deg, #ffdc00 0%, #ffdc00 100%);
    padding: 10px;
    border-radius: 8px;
    text-align: center;
}}
</style>
<div class="header-wrapper">
    <div class="logo-box">{logo_html_header}</div>
    <div>
        <h1>Rede Integrada de Ônibus</h1>
        <p>{subtitle}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Rotas Dinâmicas ---
aba = st.session_state.get("aba_ativa", "Principal")

if aba == "Principal":
    # --- Abas principais ---
    tab_configs = [
        {"label": "🔍  Consultar Linhas", "render": mod_consulta.render, "roles": ["admin", "editor", "user", "visualizador"]},
        {"label": "➕  Cadastrar Linha", "render": mod_cadastro.render, "roles": ["admin", "editor"]},
        {"label": "📜  Histórico de Linhas", "render": None, "roles": ["admin", "editor"]}, # Custom render below
        {"label": "🗂️  Tabelas de Referência", "render": mod_cadastro_ref.render, "roles": ["admin", "editor", "visualizador"]},
        {"label": "📦  GTFS", "render": mod_gtfs.render, "roles": ["admin", "editor"]},
        {"label": "👥  Usuários", "render": mod_usuarios.render, "roles": ["admin"]},
    ]
    
    # Filter tabs by role
    user_role = st.session_state.role
    active_tabs_configs = [t for t in tab_configs if user_role in t["roles"]]
    tab_labels = [t["label"] for t in active_tabs_configs]
    
    tabs = st.tabs(tab_labels)
    
    for i, config in enumerate(active_tabs_configs):
        with tabs[i]:
            if config["label"] == "📜  Histórico de Linhas":
                # Renderização customizada do Histórico
                st.markdown("### 📜 Histórico de Linhas")
                
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    filtro_tipo = st.multiselect(
                        "Tipo de Evento",
                        options=["Criação", "Alteração", "Exclusão"],
                        default=["Criação", "Alteração", "Exclusão"],
                        key="filtro_tipo_historico"
                    )
                with col2:
                    filtro_num = st.text_input("Buscar linha", placeholder="Ex: 474", key="filtro_num_historico")
                with col3:
                    if st.button("🔍 Buscar", type="primary", width='stretch', key="buscar_historico"):
                        df_hist = consultar_historico(numero=filtro_num)
                        st.session_state["resultado_historico"] = df_hist
                
                if "resultado_historico" not in st.session_state or st.button("🔄 Atualizar", key="atualizar_historico"):
                    df_hist = consultar_historico()
                    st.session_state["resultado_historico"] = df_hist
                
                df_hist = st.session_state.get("resultado_historico", pd.DataFrame())
                
                df_exibir = df_hist.copy()
                if filtro_tipo and len(filtro_tipo) < 3 and not df_hist.empty:
                    df_exibir = df_hist[df_hist['Tipo'].isin(filtro_tipo)]
                
                if df_exibir.empty:
                    st.info("Nenhum registro de histórico encontrado.")
                else:
                    st.markdown(f"**{len(df_exibir)}** {'evento' if len(df_exibir) == 1 else 'eventos'}")
                    cols_visiveis = [c for c in df_exibir.columns if c not in ("linhaID", "status")]
                    evento = st.dataframe(
                        df_exibir[cols_visiveis],
                        width='stretch',
                        hide_index=True,
                        on_select="rerun",
                        selection_mode="single-row",
                    )
                    
                    if evento and len(evento.selection.rows) > 0:
                        idx = evento.selection.rows[0]
                        linha_selecionada = df_exibir.iloc[idx]
                        linha_id_sel = linha_selecionada["linhaID"]
                        status_sel = linha_selecionada.get("status", "ativa")
                        
                        st.markdown("---")
                        if st.button("👁️ Ver Ficha", width='stretch', key="ver_ficha_historico"):
                            st.session_state["linha_acao_id"] = linha_id_sel
                            st.session_state["aba_ativa"] = "FichaExcluida" if status_sel == "excluida" else "Ficha"
                            st.rerun()
                    
                    buf = io.StringIO()
                    df_exibir.to_csv(buf, index=False, encoding="utf-8-sig")
                    st.download_button(
                        label="⬇️ Exportar CSV",
                        data=buf.getvalue().encode("utf-8-sig"),
                        file_name="historico_linhas.csv",
                        mime="text/csv",
                    )
            elif config["render"]:
                config["render"]()

elif aba == "Ficha":
    linha_id = st.session_state.get("linha_acao_id")
    mod_ficha.render(linha_id)

elif aba == "Editar":
    linha_id = st.session_state.get("linha_acao_id")
    mod_edicao.render(linha_id)

elif aba == "Historico":
    linha_id = st.session_state.get("linha_acao_id")
    mod_historico.render(linha_id)

elif aba == "FichaExcluida":
    refs = _carregar_todas_referencias()
    oficios_info = carregar_assuntos_oficios()
    
    def _of_html(of_id):
        if not of_id: return "-"
        lbl = obter_label(refs.get('oficios', {}), of_id)
        ass = oficios_info.get(of_id, '')
        if ass and ass != "Sem assunto":
             return f"{lbl}<br><span style='font-size:10.5px; font-weight:normal; color:#555;'>Assunto: {ass}</span>"
        return lbl
    
    linha_id = st.session_state.get("linha_acao_id")
    dados = obter_linha_excluida_por_id(linha_id)
    
    st.markdown("### 📄 Ficha da Linha Excluída")
    
    if not dados:
        st.error("Linha não encontrada.")
    else:
        v_linha = dados.get('numeroLinha', '-')
        v_servico = obter_label(refs.get('servicos', {}), dados.get('servico'))
        v_vista = dados.get('vista') or '-'
        v_via = dados.get('via') or '-'
        v_operador = obter_label(refs.get('operadores', {}), dados.get('operador'))
        v_criacao = dados.get('dataCriacaoLinha') or '-'
        v_tipo = obter_label(refs.get('tipos_sistema', {}), dados.get('tipoSistema'))
        v_caracteristica = obter_label(refs.get('caracteristicas', {}), dados.get('caracteristica'))
        v_area_op = obter_label(refs.get('areas_op', {}), dados.get('areaOperacional'))
        v_parametro = obter_label(refs.get('parametros', {}), dados.get('parametro_novo'))
        v_km_ida = str(dados.get('kmIDA')).replace('.',',') if dados.get('kmIDA') else '-'
        v_km_volta = str(dados.get('kmVOLTA')).replace('.',',') if dados.get('kmVOLTA') else '-'
        v_obs = dados.get('observacao') or '-'
        
        v_frota_tipo = obter_label(refs.get('tipos_veiculo', {}), dados.get('frotaTipoVeiculo'))
        v_frota_propulsao = obter_label(refs.get('tipos_propulsao', {}), dados.get('frotaTipoPropulsao'))
        v_frota_of = _of_html(dados.get('frotaUltimoOficio'))
        
        v_oficio_prin = _of_html(dados.get('oficio'))
        v_oficio_prim = _of_html(dados.get('oficioprimeiroHistorico'))
        v_oficio_ult = _of_html(dados.get('oficioUltimaAlteracao'))
        
        with st.expander("Dados Gerais", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**Número:**", v_linha)
                st.write("**Serviço:**", v_servico)
                st.write("**Via:**", v_via)
            with col2:
                st.write("**Operador:**", v_operador)
                st.write("**Área Operacional:**", v_area_op)
                st.write("**Vista:**", v_vista)
            with col3:
                st.write("**Tipo Sistema:**", v_tipo)
                st.write("**Parâmetro:**", v_parametro)
                st.write("**Data Criação:**", v_criacao)
        
        with st.expander("Características"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Característica:**", v_caracteristica)
            with col2:
                st.write("**Ofício Principal:**",unsafe_allow_html=True)
                st.markdown(v_oficio_prin, unsafe_allow_html=True)
        
        with st.expander("Informações de Frota"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.write("**Frota Tipo Veículo:**", v_frota_tipo)
            with col2:
                st.write("**Propulsão:**", v_frota_propulsao)
            with col3:
                st.write("**Frota Último Ofício:**", unsafe_allow_html=True)
                st.markdown(v_frota_of, unsafe_allow_html=True)
            with col4:
                st.write("**Ofício Primeiro Histórico:**", unsafe_allow_html=True)
                st.markdown(v_oficio_prim, unsafe_allow_html=True)
        
        with st.expander("Observações"):
            st.write(v_obs)
        
        with st.expander("Dados da Exclusão", expanded=True):
            oficio_excl_id = dados.get("oficioExclusao")
            oficio_excl = _of_html(oficio_excl_id)
            
            data_excl = dados.get("dataExclusao", "")
            if data_excl:
                try:
                    dt = datetime.fromisoformat(data_excl.replace('Z', '+00:00'))
                    data_excl_fmt = dt.strftime('%d/%m/%Y %H:%M')
                except:
                    data_excl_fmt = data_excl
            else:
                data_excl_fmt = "-"
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**Ofício de Exclusão:**", unsafe_allow_html=True)
                st.markdown(oficio_excl, unsafe_allow_html=True)
            with col2:
                st.write("**Data da Exclusão:**", data_excl_fmt)
            with col3:
                st.write("**Usuário:**", dados.get("usuarioExclusao", "-"))
        
        if st.button("⬅️ Voltar", key="voltar_ficha_excluida"):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()

elif aba == "Excluir":
    numero = st.session_state.get("linha_numero_excluir")
    linha_id = st.session_state.get("linha_acao_id")
    
    st.markdown(f"### 🗑️ Excluir Linha {numero}")
    st.warning("Tem certeza que deseja excluir esta linha permanentemente? Esta ação não pode ser desfeita.")
    
    oficios = carregar_oficios()
    oficios_labels = ["Selecione..."] + list(opcoes(oficios).keys())
    oficio_selecionado = st.selectbox("Ofício de Exclusão", oficios_labels)
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ Confirmar Exclusão", type="primary", width='stretch', disabled=(oficio_selecionado == "Selecione..."), key="confirmar_exclusao"):
            oficio_id = opcoes(oficios).get(oficio_selecionado)
            sucesso, msg = excluir_linha(linha_id, oficio_id)
            if sucesso:
                st.session_state["_mensagem_sucesso"] = msg
                st.session_state.pop("resultado_consulta", None)
                st.session_state.pop("resultado_historico", None)
            else:
                st.session_state["_mensagem_erro"] = msg
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()
    with col_no:
        if st.button("❌ Cancelar", width='stretch'):
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
            st.session_state.show_login = False
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
