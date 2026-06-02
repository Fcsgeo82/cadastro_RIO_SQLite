import streamlit as st
import datetime
import pandas as pd
from models.db import obter_linha_por_id, atualizar_linha
from views.mod_cadastro import _carregar_todas_referencias
from utils.ui_components import obter_label

def _get_index(dict_opcoes: dict, valor_id: str) -> int:
    """Retorna o índice da opção salva para usar no st.selectbox(index=...)."""
    if not valor_id:
        return 0 # '— selecione —'
    # dict_opcoes -> {"Label1": "ID1", ...}
    for i, (_, v) in enumerate(dict_opcoes.items()):
        if str(v) == str(valor_id):
            return i + 1 # +1 por causa do '— selecione —'
    return 0

def _selectbox(label: str, opcoes_dict: dict, valor_db: str, obrigatorio: bool = False, disabled: bool = False):
    sufixo  = " *" if obrigatorio else ""
    rotulos = ["— selecione —"] + list(opcoes_dict.keys())
    idx = _get_index(opcoes_dict, valor_db)
    
    # Previne erro caso o ID cadastrado não exista mais na lista
    if idx >= len(rotulos): 
        idx = 0
        
    sel = st.selectbox(label + sufixo, rotulos, index=idx, disabled=disabled)
    return None if disabled else opcoes_dict.get(sel)

def _load_itinerario_df(itinerarios_list, tipo, sentido):
    """Filtra e prepara DataFrame para o data_editor."""
    pts = [it for it in itinerarios_list if it.get("tipo") == tipo and str(it.get("sentido")) == str(sentido)]
    data = []
    for p in sorted(pts, key=lambda x: x.get("ordem", 0)):
        data.append({
            "Logradouro": p.get("logradouro", ""),
            "Complemento": p.get("observacao", ""),
            "Bairro": p.get("bairro", "")
        })
    return pd.DataFrame(data, columns=["Logradouro", "Complemento", "Bairro"])

def _itinerario_editor_edicao(titulo: str, key: str, df_dados):
    """Renderiza um st.data_editor configurado para edição de pontos."""
    st.markdown(f"**{titulo}**")
    return st.data_editor(
        df_dados,
        num_rows="dynamic",
        width='stretch',
        key=key,
        column_config={
            "Logradouro": st.column_config.TextColumn("Logradouro", width="large", required=True),
            "Complemento": st.column_config.TextColumn("Complemento", width="medium"),
            "Bairro": st.column_config.TextColumn("Bairro", width="medium"),
        }
    )

def render(linha_id: str):
    if not linha_id:
        st.error("Nenhuma linha selecionada.")
        if st.button("⬅️ Voltar"):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()
        return

    dados_bd = obter_linha_por_id(linha_id)
    if not dados_bd:
        st.error("Linha não encontrada no banco de dados.")
        if st.button("⬅️ Voltar"):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()
        return

    refs = _carregar_todas_referencias()

    # Cabeçalho da edição
    col_back, _ = st.columns([1, 8])
    with col_back:
        if st.button("⬅️ Voltar / Cancelar", width='stretch'):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()

    st.markdown("### ✏️ Alterar Cadastro da Linha")
    st.markdown(f"Você está editando a linha: **{dados_bd.get('numeroLinha', 'N/A')}**")

    # ----- Form -----
    with st.form("form_edicao", clear_on_submit=False):
        
        # ── Identificação ────────────────────────────────────────
        st.markdown("#### 📋 Identificação")
        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            numeroLinha = st.text_input("Número da Linha *", value=dados_bd.get("numeroLinha") or "", disabled=False)
        with col2:
            vista = st.text_input("Vista *", value=dados_bd.get("vista") or "", disabled=False)
        with col3:
            dt = None
            if dados_bd.get("dataCriacaoLinha"):
                try:
                    dt = datetime.datetime.strptime(dados_bd["dataCriacaoLinha"], "%Y-%m-%d").date()
                except:
                    dt = None
            dataCriacaoLinha = st.date_input("Data de Criação *", value=dt, disabled=True)

        colV1, colV2 = st.columns(2)
        with colV1:
            via = st.text_input("Via", value=dados_bd.get("via") or "", disabled=False)

        col4, col5 = st.columns(2)
        with col4:
            servico_label  = _selectbox("Serviço", refs.get("servicos", {}), dados_bd.get("servico"), obrigatorio=True, disabled=True)
        with col5:
            operador_label = _selectbox("Operador", refs.get("operadores", {}), dados_bd.get("operador"), obrigatorio=True, disabled=False)

        # ── Classificação ────────────────────────────────────────
        st.divider()
        st.markdown("#### 🗂️ Classificação")
        col6, col7 = st.columns(2)
        with col6:
            area_op_id       = _selectbox("Área Operacional", refs.get("areas_op", {}), dados_bd.get("areaOperacional"))
        with col7:
            tipo_sistema_id  = _selectbox("Tipo de Operação", refs.get("tipos_sistema", {}), dados_bd.get("tipoSistema"))

        col11, col12 = st.columns(2)
        with col11:
            tipologia_id = _selectbox("Tipologia de Rede", refs.get("tipologia", {}), dados_bd.get("tipologiaRede"))
        with col12:
            abrangencia_id   = _selectbox("Abrangência Territorial", refs.get("abrangencia", {}), dados_bd.get("abrangenciaTerritorial"))
        
        col13, col14 = st.columns(2)
        with col13:
            geometria_id     = _selectbox("Geometria do Traçado", refs.get("geometria", {}), dados_bd.get("geometriaTracado"))
        with col14:
            hierarquia_id    = _selectbox("Hierarquia de Atendimento", refs.get("hierarquia", {}), dados_bd.get("hierarquiaAtendimento"))

        col15, col16 = st.columns(2)
        with col15:
            grupamento_id    = str(dados_bd.get("grupamentoBRS")) if dados_bd.get("grupamentoBRS") else None
            grupamento_label = _selectbox("Grupamento BRS", refs.get("grupamentos", {}), grupamento_id)
        with col16:
            pass # Espaçador

        # ── Quilometragem ────────────────────────────────────────
        st.divider()
        st.markdown("#### 📏 Quilometragem")
        col12, col13 = st.columns(2)
        with col12:
            kmIDA   = st.number_input("KM Ida", min_value=0.0, step=0.1, value=float(dados_bd.get("kmIDA") or 0.0))
        with col13:
            kmVOLTA = st.number_input("KM Volta", min_value=0.0, step=0.1, value=float(dados_bd.get("kmVOLTA") or 0.0))

        # ── Ofícios ──────────────────────────────────────────────
        st.divider()
        st.markdown("#### 📄 Ofícios")
        st.info("ℹ️ A Atualização da *Última Alteração* será feita automaticamente caso novos ofícios sejam associados à frota, ao itinerário ou à alteração especial nesta modificação.")
        col15, col16 = st.columns(2)
        with col15:
            # Primeiro histórico não pode ser alterado
            st.text_input("Ofício — Primeiro Histórico", value=obter_label(refs.get("oficios", {}), dados_bd.get("oficioprimeiroHistorico")), disabled=True)
            oficio_prim_hist_id = dados_bd.get("oficioprimeiroHistorico")
            if oficio_prim_hist_id:
                st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(oficio_prim_hist_id, 'Sem assunto')}")
        with col16:
            # Mostra o status atual
            st.text_input("Ofício — Última Alteração (Automático)", value=obter_label(refs.get("oficios", {}), dados_bd.get("oficioUltimaAlteracao")), disabled=True)
            oficio_ult_alt_id = dados_bd.get("oficioUltimaAlteracao")
            if oficio_ult_alt_id:
                 st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(oficio_ult_alt_id, 'Sem assunto')}")

        # Nova linha para Alteração Especial
        row_esp1, _ = st.columns([1, 1])
        with row_esp1:
            oficio_especial_id = _selectbox("Ofício — Alteração Especial (Opcional)", refs.get("oficios", {}), None)
            if oficio_especial_id:
                st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(oficio_especial_id, 'Sem assunto')}")

        # ── Frota ────────────────────────────────────────────────
        st.divider()
        st.markdown("#### 🚍 Frota")
        col17, col18, col19, col20 = st.columns(4)
        with col17:
            frota_tipo_veiculo_id  = _selectbox("Tipo de Veículo da Frota", refs.get("tipos_veiculo", {}), dados_bd.get("frotaTipoVeiculo"))
        with col18:
            frota_tipo_propulsao_id = _selectbox("Propulsão", refs.get("tipos_propulsao", {}), dados_bd.get("frotaTipoPropulsao"))
        with col19:
            frota_ultimo_oficio_id = _selectbox("Ofício de Autorização da Frota", refs.get("oficios", {}), dados_bd.get("frotaUltimoOficio"))
            if frota_ultimo_oficio_id:
                st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(frota_ultimo_oficio_id, 'Sem assunto')}")
        with col20:
            dtf = None
            if dados_bd.get("frotaDataOficio"):
                try: dtf = datetime.datetime.strptime(dados_bd["frotaDataOficio"], "%Y-%m-%d").date()
                except: pass
            frotaDataOficio = st.date_input("Data do Ofício da Frota", value=dtf)

        # ── Itinerários ──────────────────────────────────────────
        st.divider()
        st.markdown("#### 🗺️ Itinerários")
        st.info("💡 Edite as tabelas abaixo. 'Complemento' será salvo como observação do ponto.")
        
        it_lista = dados_bd.get("itinerarios", [])
        tabR, tabA1, tabA2, tabA3 = st.tabs(["Itinerário Regular", "Alternativo 1", "Alternativo 2", "Alternativo 3"])
        
        with tabR:
            it_reg_oficio_db = next((it.get("oficio") for it in it_lista if it.get("tipo") == "R"), None)
            it_reg_oficio_id = _selectbox("Ofício de Autorização (Regular)", refs.get("oficios", {}), it_reg_oficio_db)
            if it_reg_oficio_id:
                 st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(it_reg_oficio_id, 'Sem assunto')}")
            df_reg_ida = _itinerario_editor_edicao("Ida", "edit_reg_ida", _load_itinerario_df(it_lista, "R", "0"))
            st.write("") # Espaçador
            df_reg_volta = _itinerario_editor_edicao("Volta", "edit_reg_volta", _load_itinerario_df(it_lista, "R", "1"))
                
        with tabA1:
            it_a1_oficio_db = next((it.get("oficio") for it in it_lista if it.get("tipo") == "A1" or it.get("tipo") == "A"), None)
            it_a1_oficio_id = _selectbox("Ofício de Autorização (Alt 1)", refs.get("oficios", {}), it_a1_oficio_db)
            if it_a1_oficio_id:
                 st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(it_a1_oficio_id, 'Sem assunto')}")
            df_a1_ida = _itinerario_editor_edicao("Ida", "edit_a1_ida", _load_itinerario_df(it_lista, "A1" if any(it.get("tipo")=="A1" for it in it_lista) else "A", "0"))
            st.write("") # Espaçador
            df_a1_volta = _itinerario_editor_edicao("Volta", "edit_a1_volta", _load_itinerario_df(it_lista, "A1" if any(it.get("tipo")=="A1" for it in it_lista) else "A", "1"))

        with tabA2:
            it_a2_oficio_db = next((it.get("oficio") for it in it_lista if it.get("tipo") == "A2"), None)
            it_a2_oficio_id = _selectbox("Ofício de Autorização (Alt 2)", refs.get("oficios", {}), it_a2_oficio_db)
            if it_a2_oficio_id:
                 st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(it_a2_oficio_id, 'Sem assunto')}")
            df_a2_ida = _itinerario_editor_edicao("Ida", "edit_a2_ida", _load_itinerario_df(it_lista, "A2", "0"))
            st.write("") # Espaçador
            df_a2_volta = _itinerario_editor_edicao("Volta", "edit_a2_volta", _load_itinerario_df(it_lista, "A2", "1"))

        with tabA3:
            it_a3_oficio_db = next((it.get("oficio") for it in it_lista if it.get("tipo") == "A3"), None)
            it_a3_oficio_id = _selectbox("Ofício de Autorização (Alt 3)", refs.get("oficios", {}), it_a3_oficio_db)
            if it_a3_oficio_id:
                 st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(it_a3_oficio_id, 'Sem assunto')}")
            df_a3_ida = _itinerario_editor_edicao("Ida", "edit_a3_ida", _load_itinerario_df(it_lista, "A3", "0"))
            st.write("") # Espaçador
            df_a3_volta = _itinerario_editor_edicao("Volta", "edit_a3_volta", _load_itinerario_df(it_lista, "A3", "1"))

        # ── Observação ───────────────────────────────────────────
        st.divider()
        observacao = st.text_area("📝 Observação Geral", height=80, value=dados_bd.get("observacao") or "")

        # ── Submit ───────────────────────────────────────────────
        submitted = st.form_submit_button("💾 Salvar Alterações", width='stretch', type="primary")

        if submitted:
            # Campos obrigatórios - usar valores do BD para campos disabled
            if not servico_label:
                servico_label = dados_bd.get("servico")
            if not operador_label:
                operador_label = dados_bd.get("operador")
                
            obrigatorios = {"Número": numeroLinha, "Vista": vista, "Data Criação": dataCriacaoLinha, "Serviço": servico_label, "Operador": operador_label}
            faltando = [k for k, v in obrigatorios.items() if not v]
            
            if faltando:
                st.error(f"⚠️ Preencha os obrigatórios: {', '.join(faltando)}")
                return

            # ---- LÓGICA DE ÚLTIMA ALTERAÇÃO AUTOMÁTICA ----
            oficios_alterados = []
            
            if frota_ultimo_oficio_id and str(frota_ultimo_oficio_id) != str(dados_bd.get("frotaUltimoOficio") or ""):
                oficios_alterados.append(str(frota_ultimo_oficio_id))

            if oficio_especial_id and str(oficio_especial_id) != str(dados_bd.get("oficio") or ""):
                oficios_alterados.append(str(oficio_especial_id))
                
            if it_reg_oficio_id and str(it_reg_oficio_id) != str(it_reg_oficio_db or ""):
                oficios_alterados.append(str(it_reg_oficio_id))

            if it_a1_oficio_id and str(it_a1_oficio_id) != str(it_a1_oficio_db or ""):
                oficios_alterados.append(str(it_a1_oficio_id))

            if it_a2_oficio_id and str(it_a2_oficio_id) != str(it_a2_oficio_db or ""):
                oficios_alterados.append(str(it_a2_oficio_id))

            if it_a3_oficio_id and str(it_a3_oficio_id) != str(it_a3_oficio_db or ""):
                oficios_alterados.append(str(it_a3_oficio_id))

            if oficios_alterados:
                # Achar o ofício mais recente entre os alterados
                oficio_mais_recente_id = None
                for of_id in refs.get("oficios", {}).values():
                    if str(of_id) in oficios_alterados:
                        oficio_mais_recente_id = of_id
                        break
                
                if oficio_mais_recente_id:
                    oficio_ult_alt_id = oficio_mais_recente_id

            # Resolvendo Grupamento para passar pro DB (pode ser o label ou ID dependendo do salvamento)
            dados = {
                "numeroLinha":              numeroLinha,
                "dataCriacaoLinha":         dataCriacaoLinha,
                "servico":                  servico_label,
                "operador":                 operador_label,
                "vista":                    vista,
                "via":                      via,
                "areaOperacional":          area_op_id,
                "oficio":                   dados_bd.get("oficio"), # Imutável após o cadastro
                "oficioprimeiroHistorico":  oficio_prim_hist_id,
                "oficioUltimaAlteracao":    oficio_ult_alt_id,
                "tipoSistema":              tipo_sistema_id,
                "kmIDA":                    kmIDA if kmIDA else None,
                "kmVOLTA":                  kmVOLTA if kmVOLTA else None,
                "parametro_novo":           None,
                "caracteristica":           None,
                "grupamentoBRS":            grupamento_label,
                "tipologiaRede":            tipologia_id,
                "abrangenciaTerritorial":   abrangencia_id,
                "geometriaTracado":         geometria_id,
                "hierarquiaAtendimento":    hierarquia_id,
                "frotaTipoVeiculo":         frota_tipo_veiculo_id,
                "frotaTipoPropulsao":       frota_tipo_propulsao_id,
                "frotaUltimoOficio":        frota_ultimo_oficio_id,
                "frotaDataOficio":          str(frotaDataOficio) if frotaDataOficio else None,
                "observacao":               observacao,
                "itinerarios":              [], # Será preenchido abaixo
                "itinerarios_oficios": {
                    "R": it_reg_oficio_id,
                    "A1": it_a1_oficio_id,
                    "A2": it_a2_oficio_id,
                    "A3": it_a3_oficio_id
                }
            }

            # Processar Itinerários
            all_itinerarios = []
            def processar_df(df, tipo, sentido):
                if df is not None and not df.empty:
                    for idx, row in df.iterrows():
                        if row.get("Logradouro"):
                            all_itinerarios.append({
                                "tipo": tipo,
                                "sentido": sentido,
                                "ordem": idx,
                                "logradouro": row["Logradouro"],
                                "bairro": row.get("Bairro", ""),
                                "observacao": row.get("Complemento", "")
                            })

            processar_df(df_reg_ida, "R", "0")
            processar_df(df_reg_volta, "R", "1")
            processar_df(df_a1_ida, "A1", "0")
            processar_df(df_a1_volta, "A1", "1")
            processar_df(df_a2_ida, "A2", "0")
            processar_df(df_a2_volta, "A2", "1")
            processar_df(df_a3_ida, "A3", "0")
            processar_df(df_a3_volta, "A3", "1")
            
            dados["itinerarios"] = all_itinerarios

            with st.spinner("Atualizando registros no SQLite..."):
                sucesso, msg = atualizar_linha(linha_id, dados)
                
            if sucesso:
                st.session_state["_mensagem_sucesso"] = msg
                st.cache_data.clear()
                st.session_state["aba_ativa"] = "Principal"
                st.rerun()
            else:
                st.error(f"❌ {msg}")
