# =============================================================
# mod_usuarios.py — Gerenciamento de Usuários (Admin)
# =============================================================

import streamlit as st
import uuid
import bcrypt
from datetime import datetime, timezone
from models.db import get_connection, validate_password_strength


def _query_df(sql: str, params: list = None):
    import pandas as pd
    conn = get_connection()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def render():
    st.markdown("### 👥 Gerenciamento de Usuários")
    st.markdown("Crie, edite ou desative usuários do sistema.")
    
    tab_cadastro, tab_lista = st.tabs(["Cadastrar Novo", "Lista de Usuários"])
    
    with tab_cadastro:
        with st.form("form_novo_usuario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                novo_username = st.text_input("Username (login)", placeholder="ex: joao")
            with col2:
                novo_email = st.text_input("Email", placeholder="ex: joao@empresa.com")
            
            nova_senha = st.text_input("Senha", type="password", help="Mínimo 8 caracteres, 1 maiúscula, 1 número, 1 símbolo")
            confirmar_senha = st.text_input("Confirmar Senha", type="password")
            
            col_role, col_submit = st.columns([2, 1])
            with col_role:
                novo_role = st.selectbox("Permissão", ["user", "editor", "admin"])
            
            submitted = st.form_submit_button("Cadastrar Usuário", type="primary", use_container_width=True)
            
            if submitted:
                if not novo_username or not novo_email or not nova_senha:
                    st.error("Preencha todos os campos.")
                elif nova_senha != confirmar_senha:
                    st.error("As senhas não conferem.")
                else:
                    valido, msg = validate_password_strength(nova_senha)
                    if not valido:
                        st.error(msg)
                    else:
                        df_check = _query_df("SELECT username FROM Usuarios WHERE username = ?", [novo_username])
                        if not df_check.empty:
                            st.error("Username já existe.")
                        else:
                            conn = get_connection()
                            user_id = str(uuid.uuid4())
                            pwd_hash = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
                            created = datetime.now(timezone.utc).isoformat()
                            
                            try:
                                conn.execute("""
                                    INSERT INTO Usuarios (userID, username, password_hash, role, email, reset_token, reset_expiry, failed_attempts, lockout_until)
                                    VALUES (?, ?, ?, ?, ?, NULL, NULL, 0, NULL)
                                """, (user_id, novo_username, pwd_hash, novo_role, novo_email))
                                conn.commit()
                                conn.close()
                                st.success(f"✅ Usuário '{novo_username}' criado com sucesso!")
                                st.rerun()
                            except Exception as e:
                                conn.close()
                                st.error(f"Erro ao criar usuário: {e}")
    
    with tab_lista:
        df_users = _query_df("SELECT username, role, email FROM Usuarios ORDER BY username")
        
        if df_users.empty:
            st.info("Nenhum usuário cadastrado.")
        else:
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("#### Alterar Senha de Usuário")
            
            with st.form("form_alt_senha"):
                col_user, col_nova = st.columns(2)
                with col_user:
                    user_selecionado = st.selectbox("Usuário", df_users["username"].tolist())
                with col_nova:
                    nova_senha_alt = st.text_input("Nova Senha", type="password")
                
                alt_senha_submit = st.form_submit_button("Alterar Senha", type="primary", use_container_width=True)
                
                if alt_senha_submit:
                    if not nova_senha_alt:
                        st.error("Informe a nova senha.")
                    else:
                        valido, msg = validate_password_strength(nova_senha_alt)
                        if not valido:
                            st.error(msg)
                        else:
                            conn = get_connection()
                            new_hash = bcrypt.hashpw(nova_senha_alt.encode(), bcrypt.gensalt()).decode()
                            try:
                                conn.execute("UPDATE Usuarios SET password_hash = ? WHERE username = ?", (new_hash, user_selecionado))
                                conn.commit()
                                conn.close()
                                st.success(f"✅ Senha do usuário '{user_selecionado}' alterada!")
                                st.rerun()
                            except Exception as e:
                                conn.close()
                                st.error(f"Erro ao alterar senha: {e}")
            
            st.markdown("---")
            st.markdown("#### Excluir Usuário")
            
            with st.form("form_excluir"):
                col_del, col_btn = st.columns([3, 1])
                with col_del:
                    user_excluir = st.selectbox("Selecione o usuário a excluir", df_users["username"].tolist())
                with col_btn:
                    excl_submit = st.form_submit_button("Excluir", type="primary", use_container_width=True)
                
                if excl_submit:
                    if user_excluir == st.session_state.get("user"):
                        st.error("Não é possível excluir seu próprio usuário.")
                    else:
                        conn = get_connection()
                        try:
                            conn.execute("DELETE FROM Usuarios WHERE username = ?", (user_excluir,))
                            conn.commit()
                            conn.close()
                            st.success(f"✅ Usuário '{user_excluir}' excluído!")
                            st.rerun()
                        except Exception as e:
                            conn.close()
                            st.error(f"Erro ao excluir: {e}")