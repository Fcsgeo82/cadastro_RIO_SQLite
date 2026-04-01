import streamlit as st
from db import obter_linha_por_id

# Reutilizar carregadores do cadastro para cruzar IDs com Nomes/Labels
from mod_cadastro import _carregar_todas_referencias

def _obter_label(dicionario_inverso, chave_busca):
    """Encontra a label de um ID pesquisando num dicionário {Label: ID}."""
    if not chave_busca:
        return "-"
    # dicionario_inverso é {Label: ID}
    for label, id_ in dicionario_inverso.items():
        if str(id_) == str(chave_busca):
            return label
    return chave_busca

def render(linha_id: str):
    if not linha_id:
        st.error("Nenhuma linha selecionada.")
        if st.button("⬅️ Voltar"):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()
        return

    dados = obter_linha_por_id(linha_id)
    if not dados:
        st.error("Linha não encontrada no banco de dados.")
        if st.button("⬅️ Voltar"):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()
        return

    refs = _carregar_todas_referencias()

    # --- Header Ficha ---
    col_back, _ = st.columns([1, 8])
    with col_back:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()
            
    st.markdown("---")
    st.markdown(f"## 🚌 Ficha Cadastral da Linha: **{dados.get('numeroLinha', 'N/A')}**")
    st.markdown(f"*{dados.get('vista', 'Sem Vista')}*")

    # --- Container principal estilizado ---
    st.markdown('<div style="background-color: #f7f9fc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 24px;">', unsafe_allow_html=True)

    # 1. Identificação
    st.subheader("📋 Identificação Básica")
    c1, c2, c3 = st.columns(3)
    c1.metric("Serviço", _obter_label(refs["servicos"], dados.get("servico")))
    c2.metric("Operador", _obter_label(refs["operadores"], dados.get("operador")))
    c3.metric("Data Criação da Linha", dados.get("dataCriacaoLinha") or "-")

    # 2. Classificação Geral
    st.markdown("---")
    st.subheader("🗂️ Classificação")
    c4, c5, c6 = st.columns(3)
    c4.write(f"**Área Operacional:** {_obter_label(refs['areas_op'], dados.get('areaOperacional'))}")
    c5.write(f"**Área Geográfica:** {_obter_label(refs['areas_geo'], dados.get('areaGeografica'))}")
    c6.write(f"**Tipo Sistema:** {_obter_label(refs['tipos_sistema'], dados.get('tipoSistema'))}")
    
    c7, c8, c9 = st.columns(3)
    c7.write(f"**Grupamento BRS:** {_obter_label(refs['grupamentos'], dados.get('grupamentoBRS'))}")
    c8.write(f"**Parâmetro:** {_obter_label(refs['parametros'], dados.get('parametro'))}")
    c9.write(f"**Classif. Espacial:** {dados.get('classificacaoEspacial') or '-'}")
    
    # 3. Ofícios & Registro
    st.markdown("---")
    st.subheader("📄 Relatório de Ofícios Oficiais")
    
    def _of_box(title, of_id):
        lbl = _obter_label(refs['oficios'], of_id)
        if of_id:
             assunto = refs.get('assuntos_oficios', {}).get(of_id, 'Sem assunto')
             return f"**{title}**\n\n{lbl}\n\n*Assunto:* {assunto}"
        return f"**{title}**\n\n{lbl}"

    c10, c11, c12 = st.columns(3)
    c10.info(_of_box("Ofício Principal:", dados.get('oficio')))
    c11.info(_of_box("Primeiro Histórico:", dados.get('oficioprimeiroHistorico')))
    c12.error(_of_box("Última Alteração:", dados.get('oficioUltimaAlteracao')))

    # 4. Operacional
    st.markdown("---")
    st.subheader("📏 Operação, Frota e Itinerário")
    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Dados do Trecho de Ida**")
        st.write(f"- KM Ida: `{dados.get('kmIDA') or '0'}`")
        st.write(f"- Ofício Itin. Ida: `{_obter_label(refs['oficios'], dados.get('itinerarioIdaOficio'))}`")
        if dados.get('itinerarioIdaOficio'):
             st.caption(f"Assunto: {refs.get('assuntos_oficios', {}).get(dados.get('itinerarioIdaOficio'))}")
        st.write(f"- Data: `{dados.get('itinerarioIdaData') or '-'}`")
        st.caption(f"**Itinerário:** {dados.get('itinerarioIDA') or '-'}")
    with colB:
        st.markdown("**Dados do Trecho de Volta**")
        st.write(f"- KM Volta: `{dados.get('kmVOLTA') or '0'}`")
        st.write(f"- Ofício Itin. Volta: `{_obter_label(refs['oficios'], dados.get('itinerarioVoltaOficio'))}`")
        if dados.get('itinerarioVoltaOficio'):
             st.caption(f"Assunto: {refs.get('assuntos_oficios', {}).get(dados.get('itinerarioVoltaOficio'))}")
        st.write(f"- Data: `{dados.get('itinerarioVoltaData') or '-'}`")
        st.caption(f"**Itinerário:** {dados.get('itinerarioVOLTA') or '-'}")

    st.markdown('<br>', unsafe_allow_html=True)
    c13, c14, c15 = st.columns(3)
    c13.write(f"**Tipo Veículo Fronteira:** {_obter_label(refs['tipos_veiculo'], dados.get('frotaTipoVeiculo'))}")
    with c14:
        st.write(f"**Últ. Ofício Frota:** {_obter_label(refs['oficios'], dados.get('frotaUltimoOficio'))}")
        if dados.get('frotaUltimoOficio'):
            st.caption(f"Assunto: {refs.get('assuntos_oficios', {}).get(dados.get('frotaUltimoOficio'))}")
    c15.write(f"**Data Ofício Frota:** {dados.get('frotaDataOficio') or '-'}")
    
    # 5. Outros
    st.markdown("---")
    st.write("**Observações:**")
    st.text(dados.get("observacao") or "Nenhuma observação registrada.")
    
    st.caption(f"Registrado no sistema em: {dados.get('dataCadastro')} | Última Atualização: {dados.get('ultimaAtualizacao')}")
    st.markdown('</div>', unsafe_allow_html=True)
