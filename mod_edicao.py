import streamlit as st
import datetime
from db import obter_linha_por_id, atualizar_linha
from mod_cadastro import _carregar_todas_referencias

def _get_index(dict_opcoes: dict, valor_id: str) -> int:
    """Retorna o índice da opção salva para usar no st.selectbox(index=...)."""
    if not valor_id:
        return 0 # '— selecione —'
    # dict_opcoes -> {"Label1": "ID1", ...}
    for i, (_, v) in enumerate(dict_opcoes.items()):
        if str(v) == str(valor_id):
            return i + 1 # +1 por causa do '— selecione —'
    return 0

def _obter_label(dicionario_inverso, chave_busca):
    if not chave_busca: return None
    for label, id_ in dicionario_inverso.items():
        if str(id_) == str(chave_busca): return label
    return None

def _selectbox(label: str, opcoes_dict: dict, valor_db: str, obrigatorio: bool = False):
    sufixo  = " *" if obrigatorio else ""
    rotulos = ["— selecione —"] + list(opcoes_dict.keys())
    idx = _get_index(opcoes_dict, valor_db)
    
    # Previne erro caso o ID cadastrado não exista mais na lista
    if idx >= len(rotulos): 
        idx = 0
        
    sel = st.selectbox(label + sufixo, rotulos, index=idx)
    return opcoes_dict.get(sel)

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
        if st.button("⬅️ Voltar / Cancelar", use_container_width=True):
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
            numeroLinha = st.text_input("Número da Linha *", value=dados_bd.get("numeroLinha") or "")
        with col2:
            vista = st.text_input("Vista *", value=dados_bd.get("vista") or "")
        with col3:
            dt = None
            if dados_bd.get("dataCriacaoLinha"):
                try:
                    dt = datetime.datetime.strptime(dados_bd["dataCriacaoLinha"], "%Y-%m-%d").date()
                except:
                    dt = None
            dataCriacaoLinha = st.date_input("Data de Criação *", value=dt)

        colV1, colV2 = st.columns(2)
        with colV1:
            via = st.text_input("Via", value=dados_bd.get("via") or "")

        col4, col5 = st.columns(2)
        with col4:
            servico_label  = _selectbox("Serviço", refs.get("servicos", {}), dados_bd.get("servico"), obrigatorio=True)
        with col5:
            operador_label = _selectbox("Operador", refs.get("operadores", {}), dados_bd.get("operador"), obrigatorio=True)

        # ── Classificação ────────────────────────────────────────
        st.divider()
        st.markdown("#### 🗂️ Classificação")
        col6, col7, col8 = st.columns(3)
        with col6:
            area_op_id       = _selectbox("Área Operacional", refs.get("areas_op", {}), dados_bd.get("areaOperacional"))
        with col7:
            area_geo_id      = _selectbox("Área Geográfica", refs.get("areas_geo", {}), dados_bd.get("areaGeografica"))
        with col8:
            tipo_sistema_id  = _selectbox("Tipo de Sistema", refs.get("tipos_sistema", {}), dados_bd.get("tipoSistema"))

        col9, col10, col11 = st.columns(3)
        with col9:
            parametro_id     = _selectbox("Parâmetro Funcional", refs.get("parametros", {}), dados_bd.get("parametro"))
        with col10:
            grupamento_id    = str(dados_bd.get("grupamentoBRS")) if dados_bd.get("grupamentoBRS") else None
            grupamento_label = _selectbox("Grupamento BRS", refs.get("grupamentos", {}), grupamento_id)
        with col11:
            classificacaoEspacial = _selectbox("Classificação Espacial", refs.get("classificacoes_espaciais", {}), dados_bd.get("classificacaoEspacial"))

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
        st.info("ℹ️ A Atualização da *Última Alteração* será feita automaticamente caso novos ofícios sejam associados à frota ou ao itinerário nesta modificação.")
        col14, col15, col16 = st.columns(3)
        with col14:
            oficio_id         = _selectbox("Ofício", refs.get("oficios", {}), dados_bd.get("oficio"))
            if oficio_id:
                st.info(f"ℹ️ **Assunto:** {refs.get('assuntos_oficios', {}).get(oficio_id, 'Sem assunto')}")
        with col15:
            oficio_prim_hist_id = _selectbox("Ofício — Primeiro Histórico", refs.get("oficios", {}), dados_bd.get("oficioprimeiroHistorico"))
            if oficio_prim_hist_id:
                st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(oficio_prim_hist_id, 'Sem assunto')}")
        with col16:
            # Mostra o status atual
            st.text_input("Ofício — Última Alteração (Automático)", value=_obter_label(refs.get("oficios", {}), dados_bd.get("oficioUltimaAlteracao")) or "-", disabled=True)
            oficio_ult_alt_id = dados_bd.get("oficioUltimaAlteracao")
            if oficio_ult_alt_id:
                 st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(oficio_ult_alt_id, 'Sem assunto')}")

        # ── Frota ────────────────────────────────────────────────
        st.divider()
        st.markdown("#### 🚍 Frota")
        col17, col18, col19 = st.columns(3)
        with col17:
            frota_tipo_veiculo_id  = _selectbox("Tipo de Veículo da Frota", refs.get("tipos_veiculo", {}), dados_bd.get("frotaTipoVeiculo"))
        with col18:
            frota_ultimo_oficio_id = _selectbox("Último Ofício da Frota", refs.get("oficios", {}), dados_bd.get("frotaUltimoOficio"))
            if frota_ultimo_oficio_id:
                st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(frota_ultimo_oficio_id, 'Sem assunto')}")
        with col19:
            dtf = None
            if dados_bd.get("frotaDataOficio"):
                try: dtf = datetime.datetime.strptime(dados_bd["frotaDataOficio"], "%Y-%m-%d").date()
                except: pass
            frotaDataOficio = st.date_input("Data do Ofício da Frota", value=dtf)

        # ── Itinerário ───────────────────────────────────────────
        st.divider()
        st.markdown("#### 🗺️ Itinerário")
        col20, col21, col22 = st.columns(3)
        with col20:
            itinerarioIDA        = st.text_area("Itinerário IDA", height=80, value=dados_bd.get("itinerarioIDA") or "")
        with col21:
            itIda_oficio_id      = _selectbox("Ofício do Itin. IDA", refs.get("oficios", {}), dados_bd.get("itinerarioIdaOficio"))
            if itIda_oficio_id:
                 st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(itIda_oficio_id, 'Sem assunto')}")
        with col22:
            dti = None
            if dados_bd.get("itinerarioIdaData"):
                try: dti = datetime.datetime.strptime(dados_bd["itinerarioIdaData"], "%Y-%m-%d").date()
                except: pass
            itIda_data           = st.date_input("Data Itin. IDA", value=dti)

        col23, col24, col25 = st.columns(3)
        with col23:
            itinerarioVOLTA      = st.text_area("Itinerário VOLTA", height=80, value=dados_bd.get("itinerarioVOLTA") or "")
        with col24:
            itVolta_oficio_id    = _selectbox("Ofício do Itin. VOLTA", refs.get("oficios", {}), dados_bd.get("itinerarioVoltaOficio"))
            if itVolta_oficio_id:
                 st.caption(f"**Assunto:** {refs.get('assuntos_oficios', {}).get(itVolta_oficio_id, 'Sem assunto')}")
        with col25:
            dtv = None
            if dados_bd.get("itinerarioVoltaData"):
                try: dtv = datetime.datetime.strptime(dados_bd["itinerarioVoltaData"], "%Y-%m-%d").date()
                except: pass
            itVolta_data         = st.date_input("Data Itin. VOLTA", value=dtv)

        # ── Observação ───────────────────────────────────────────
        st.divider()
        observacao = st.text_area("📝 Observação", height=80, value=dados_bd.get("observacao") or "")

        # ── Submit ───────────────────────────────────────────────
        submitted = st.form_submit_button("💾 Salvar Alterações", use_container_width=True, type="primary")

    if submitted:
        obrigatorios = {"Número": numeroLinha, "Vista": vista, "Data Criação": dataCriacaoLinha, "Serviço": servico_label, "Operador": operador_label}
        faltando = [k for k, v in obrigatorios.items() if not v]
        
        if faltando:
            st.error(f"⚠️ Preencha os obrigatórios: {', '.join(faltando)}")
            return

        # ---- LÓGICA DE ÚLTIMA ALTERAÇÃO AUTOMÁTICA ----
        # Se os ofícios atuais do form forem diferentes do BD E não forem vazios.
        # Os ofícios da referência já estão ordenados por data descrescente e número descrescente (graças a query do db.py)
        # Então, se tivermos vários ofícios novos, pegamos o primeiro que aparecer nos values de refs["oficios"]
        
        oficios_alterados = []
        
        if frota_ultimo_oficio_id and str(frota_ultimo_oficio_id) != str(dados_bd.get("frotaUltimoOficio") or ""):
            oficios_alterados.append(str(frota_ultimo_oficio_id))
                
        if itIda_oficio_id and str(itIda_oficio_id) != str(dados_bd.get("itinerarioIdaOficio") or ""):
            oficios_alterados.append(str(itIda_oficio_id))
                
        if itVolta_oficio_id and str(itVolta_oficio_id) != str(dados_bd.get("itinerarioVoltaOficio") or ""):
            oficios_alterados.append(str(itVolta_oficio_id))
            
        if oficio_id and str(oficio_id) != str(dados_bd.get("oficio") or ""):
            oficios_alterados.append(str(oficio_id))

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
        # mod_cadastro passava o dict. DB espera o ID do grupamento (int) convertido.
        
        dados = {
            "numeroLinha":              numeroLinha,
            "dataCriacaoLinha":         dataCriacaoLinha,
            "servico":                  servico_label,
            "operador":                 operador_label,
            "vista":                    vista,
            "via":                      via,
            "areaOperacional":          area_op_id,
            "oficio":                   oficio_id,
            "oficioprimeiroHistorico":  oficio_prim_hist_id,
            "oficioUltimaAlteracao":    oficio_ult_alt_id,
            "tipoSistema":              tipo_sistema_id,
            "kmIDA":                    kmIDA if kmIDA else None,
            "kmVOLTA":                  kmVOLTA if kmVOLTA else None,
            "areaGeografica":           area_geo_id,
            "classificacaoEspacial":    classificacaoEspacial,
            "parametro":                parametro_id,
            "grupamentoBRS":            grupamento_label,
            "frotaTipoVeiculo":         frota_tipo_veiculo_id,
            "frotaUltimoOficio":        frota_ultimo_oficio_id,
            "frotaDataOficio":          str(frotaDataOficio) if frotaDataOficio else None,
            "itinerarioIDA":            itinerarioIDA,
            "itinerarioIdaOficio":      itIda_oficio_id,
            "itinerarioIdaData":        str(itIda_data) if itIda_data else None,
            "itinerarioVOLTA":          itinerarioVOLTA,
            "itinerarioVoltaOficio":    itVolta_oficio_id,
            "itinerarioVoltaData":      str(itVolta_data) if itVolta_data else None,
            "observacao":               observacao,
        }

        with st.spinner("Atualizando registros no SQLite..."):
            sucesso, msg = atualizar_linha(linha_id, dados)
            
        if sucesso:
            st.session_state["_mensagem_sucesso"] = msg
            st.cache_data.clear()
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()
        else:
            st.error(f"❌ {msg}")
