# =============================================================
# App.py — Cadastro de Linhas com SQLite
# =============================================================

import os
import base64
import io
import pandas as pd
from datetime import datetime
import streamlit as st
import mimetypes

# --- Fix para Windows/Pinggy: Garante que arquivos JS sejam servidos com o MIME type correto ---
# Sem isso, o browser pode recusar o carregamento de módulos dinâmicos (TypeError)
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/javascript', '.js')

from views import mod_cadastro
from views import mod_cadastro_ref
from views import mod_consulta
from views import mod_ficha
from views import mod_edicao
from views import mod_historico
from views import mod_usuarios
from views import mod_gtfs
from models import db

from views.mod_consulta import _refs_consulta

# --- Configuração da página ---
st.set_page_config(
    page_title="Linhas de Ônibus",
    page_icon="🚌",
    layout="wide",
)

# --- Logo no Header (caixa azul) ---

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
    logo_dir = os.path.dirname(os.path.abspath(__file__))
    logo_svg = os.path.join(logo_dir, "logo_rio.svg")
    logo_png = os.path.join(logo_dir, "logo_rio.png")
    
    logo_img = ""
    if os.path.exists(logo_svg):
        with open(logo_svg, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        logo_img = f'<img src="data:image/svg+xml;base64,{logo_data}" style="width:230px;height:auto;display:block;margin:0 auto;">'
    elif os.path.exists(logo_png):
        with open(logo_png, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        logo_img = f'<img src="data:image/png;base64,{logo_data}" style="width:230px;height:auto;display:block;margin:0 auto;">'
    
    st.markdown(f"""
    <style>
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
        <div class="logo-box">{logo_img}</div>
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
                submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            with col_btn2:
                public_access = st.form_submit_button("Acesso Público", type="secondary", use_container_width=True)
                
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
        username = st.text_input("Usuário")
        col_f1, col_f2 = st.columns([4,1])
        with col_f1:
            if st.button("Enviar Link de Reset", type="secondary", width='stretch'):
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

/* Header simples */
.header-logo {
    width: 50px;
    height: auto;
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
logo_dir = os.path.dirname(os.path.abspath(__file__))
logo_svg = os.path.join(logo_dir, "logo_rio.svg")
logo_png = os.path.join(logo_dir, "logo_rio.png")

logo_img = ""
if os.path.exists(logo_svg):
    with open(logo_svg, "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    logo_img = f'<img src="data:image/svg+xml;base64,{logo_data}" style="width:230px;height:auto;display:block;margin:0 auto;">'
elif os.path.exists(logo_png):
    with open(logo_png, "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    logo_img = f'<img src="data:image/png;base64,{logo_data}" style="width:200px;height:auto;display:block;margin:0 auto;">'

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
    <div class="logo-box">{logo_img}</div>
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
    tab_labels = ["🔍  Consultar Linhas"]
    if st.session_state.role in ["admin", "editor"]:
        tab_labels += ["➕  Cadastrar Linha", "📜  Histórico de Linhas", "🗂️  Tabelas de Referência", "📦  GTFS"]
    if st.session_state.role == "admin":
        tab_labels += ["👥  Usuários"]
    
    tabs = st.tabs(tab_labels)
    
    with tabs[0]:
        mod_consulta.render()
    
    if st.session_state.role in ["admin", "editor"]:
        with tabs[1]:
            mod_cadastro.render()
        
        with tabs[2]:
            from models.db import consultar_historico
            
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
                    df = consultar_historico(numero=filtro_num)
                    st.session_state["resultado_historico"] = df
            
            if "resultado_historico" not in st.session_state or st.button("🔄 Atualizar", key="atualizar_historico"):
                df = consultar_historico()
                st.session_state["resultado_historico"] = df
            
            df = st.session_state.get("resultado_historico", pd.DataFrame())
            
            # Filter by tipo if multiselect has multiple values (create copy to avoid index issues)
            df_exibir = df.copy() if df.empty else df.copy()
            if filtro_tipo and len(filtro_tipo) < 3 and not df.empty:
                df_exibir = df[df['Tipo'].isin(filtro_tipo)]
            
            if df_exibir.empty:
                st.info("Nenhum registro de histórico encontrado.")
            else:
                st.markdown(f"**{len(df_exibir)}** {'evento' if len(df_exibir) == 1 else 'eventos'}")
                
                # Hide technical columns from display but keep in df for selection
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
                    linha_id = linha_selecionada["linhaID"]
                    status = linha_selecionada.get("status", "ativa")
                    
                    st.markdown("---")
                    col_btn1, col_btn2 = st.columns([1, 4])
                    with col_btn1:
                        if st.button("👁️ Ver Ficha", width='stretch', key="ver_ficha_historico"):
                            st.session_state["linha_acao_id"] = linha_id
                            # Determine which view to show based on status
                            if status == "excluida":
                                st.session_state["aba_ativa"] = "FichaExcluida"
                            else:
                                st.session_state["aba_ativa"] = "Ficha"
                            st.rerun()
                
                buf = io.StringIO()
                df_exibir.to_csv(buf, index=False, encoding="utf-8-sig")
                st.download_button(
                    label="⬇️ Exportar CSV",
                    data=buf.getvalue().encode("utf-8-sig"),
                    file_name="historico_linhas.csv",
                    mime="text/csv",
                )

        with tabs[3]:
            mod_cadastro_ref.render()
        with tabs[4]:
            mod_gtfs.render()
    
    # Usuários (só admin)
    if st.session_state.role == "admin" and len(tab_labels) > 5:
        with tabs[5]:
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

elif aba == "FichaExcluida":
    from models.db import obter_linha_excluida_por_id, carregar_oficios, carregar_assuntos_oficios
    from views.mod_cadastro import _carregar_todas_referencias
    
    refs = _carregar_todas_referencias()
    oficios_info = carregar_assuntos_oficios()
    
    def _obter_label(dicionario_inverso, chave_busca):
        if not chave_busca:
            return "-"
        # Try to find in the dictionary (id_ -> label)
        for label, id_ in dicionario_inverso.items():
            if str(id_) == str(chave_busca):
                return label
        return str(chave_busca)
    
    def _of_html(of_id):
        if not of_id: return "-"
        lbl = _obter_label(refs.get('oficios', {}), of_id)
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
        v_servico = _obter_label(refs.get('servicos', {}), dados.get('servico'))
        v_vista = dados.get('vista') or '-'
        v_via = dados.get('via') or '-'
        v_operador = _obter_label(refs.get('operadores', {}), dados.get('operador'))
        v_criacao = dados.get('dataCriacaoLinha') or '-'
        v_tipo = _obter_label(refs.get('tipos_sistema', {}), dados.get('tipoSistema'))
        v_caracteristica = _obter_label(refs.get('caracteristicas', {}), dados.get('caracteristica'))
        v_area_op = _obter_label(refs.get('areas_op', {}), dados.get('areaOperacional'))
        v_grupamento = _obter_label(refs.get('grupamentos', {}), dados.get('grupamentoBRS'))
        v_parametro = _obter_label(refs.get('parametros', {}), dados.get('parametro_novo'))
        v_km_ida = str(dados.get('kmIDA')).replace('.',',') if dados.get('kmIDA') else '-'
        v_km_volta = str(dados.get('kmVOLTA')).replace('.',',') if dados.get('kmVOLTA') else '-'
        v_obs = dados.get('observacao') or '-'
        
        v_frota_tipo = _obter_label(refs.get('tipos_veiculo', {}), dados.get('frotaTipoVeiculo'))
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
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**Característica:**", v_caracteristica)
            with col2:
                st.write("**Grupamento BRS:**", v_grupamento)
            with col3:
                st.write("**Ofício Principal:**",unsafe_allow_html=True)
                st.markdown(v_oficio_prin, unsafe_allow_html=True)
        
        with st.expander("Informações de Frota"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**Frota Tipo Veículo:**", v_frota_tipo)
            with col2:
                st.write("**Frota Último Ofício:**", unsafe_allow_html=True)
                st.markdown(v_frota_of, unsafe_allow_html=True)
            with col3:
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
        
        col_voltar = st.columns([1])
        with col_voltar[0]:
            if st.button("⬅️ Voltar", key="voltar_ficha_excluida"):
                st.session_state["aba_ativa"] = "Principal"
                st.rerun()

elif aba == "Excluir":
    from models.db import carregar_oficios, opcoes
    
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
            from models.db import excluir_linha
            oficio_id = opcoes(oficios).get(oficio_selecionado)
            sucesso, msg = excluir_linha(linha_id, oficio_id)
            if sucesso:
                st.session_state["_mensagem_sucesso"] = msg
                st.session_state.pop("resultado_consulta", None)
                st.session_state.pop("resultado_excluidas", None)
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
