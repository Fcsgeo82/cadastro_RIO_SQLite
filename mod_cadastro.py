# =============================================================
# mod_cadastro.py — Cadastro de Linhas
# Campos baseados no schema real: CGR_Cadastro_Sistema_RIO.Linha
# =============================================================

import streamlit as st
from db import (
    inserir_linha, opcoes,
    carregar_servicos, carregar_operadores,
    carregar_areas_operacionais, carregar_areas_geograficas,
    carregar_tipos_sistema, carregar_tipos_veiculo,
    carregar_parametros, carregar_grupamentos, carregar_oficios,
)


@st.cache_data(ttl=300, show_spinner=False)
def _carregar_todas_referencias():
    """Carrega todas as tabelas de referência de uma vez (cache 5 min)."""
    return {
        "servicos":        opcoes(carregar_servicos()),
        "operadores":      opcoes(carregar_operadores()),
        "areas_op":        opcoes(carregar_areas_operacionais()),
        "areas_geo":       opcoes(carregar_areas_geograficas()),
        "tipos_sistema":   opcoes(carregar_tipos_sistema()),
        "tipos_veiculo":   opcoes(carregar_tipos_veiculo()),
        "parametros":      opcoes(carregar_parametros()),
        "grupamentos":     opcoes(carregar_grupamentos()),
        "oficios":         opcoes(carregar_oficios()),
    }


def _selectbox(label: str, opcoes_dict: dict, obrigatorio: bool = False) -> str | None:
    """Renderiza selectbox com opção vazia e retorna o ID selecionado."""
    sufixo  = " *" if obrigatorio else ""
    rotulos = ["— selecione —"] + list(opcoes_dict.keys())
    sel     = st.selectbox(label + sufixo, rotulos)
    return opcoes_dict.get(sel)  # None se "— selecione —"


def render():
    st.markdown("### 🚌 Cadastrar Nova Linha")
    st.markdown("Preencha os dados da linha. Campos marcados com * são obrigatórios.")

    refs = _carregar_todas_referencias()

    with st.form("form_cadastro", clear_on_submit=True):

        # ── Identificação ────────────────────────────────────────
        st.markdown("#### 📋 Identificação")
        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            numeroLinha = st.text_input("Número da Linha *", placeholder="Ex: 001, 474-A")
        with col2:
            vista = st.text_input("Vista *", placeholder="Ex: CENTRAL - MÉIER")
        with col3:
            dataCriacaoLinha = st.date_input("Data de Criação *", value=None)

        col4, col5 = st.columns(2)
        with col4:
            servico_label    = _selectbox("Serviço", refs["servicos"], obrigatorio=True)
        with col5:
            operador_label   = _selectbox("Operador", refs["operadores"], obrigatorio=True)

        # ── Classificação ────────────────────────────────────────
        st.divider()
        st.markdown("#### 🗂️ Classificação")

        col6, col7, col8 = st.columns(3)
        with col6:
            area_op_id       = _selectbox("Área Operacional", refs["areas_op"])
        with col7:
            area_geo_id      = _selectbox("Área Geográfica", refs["areas_geo"])
        with col8:
            tipo_sistema_id  = _selectbox("Tipo de Sistema", refs["tipos_sistema"])

        col9, col10, col11 = st.columns(3)
        with col9:
            parametro_id     = _selectbox("Parâmetro Funcional", refs["parametros"])
        with col10:
            grupamento_label = _selectbox("Grupamento BRS", refs["grupamentos"])
        with col11:
            classificacaoEspacial = st.text_input("Classificação Espacial",
                                                   placeholder="Ex: Urbano, Suburbano")

        # ── Quilometragem ────────────────────────────────────────
        st.divider()
        st.markdown("#### 📏 Quilometragem")

        col12, col13 = st.columns(2)
        with col12:
            kmIDA   = st.number_input("KM Ida",   min_value=0.0, step=0.1, value=None,
                                       placeholder="Ex: 12.5")
        with col13:
            kmVOLTA = st.number_input("KM Volta", min_value=0.0, step=0.1, value=None,
                                       placeholder="Ex: 12.5")

        # ── Ofícios ──────────────────────────────────────────────
        st.divider()
        st.markdown("#### 📄 Ofícios")

        col14, col15, col16 = st.columns(3)
        with col14:
            oficio_id              = _selectbox("Ofício", refs["oficios"])
        with col15:
            oficio_primeiro_id     = _selectbox("Ofício — Primeiro Histórico", refs["oficios"])
        with col16:
            oficio_ult_alt_id      = _selectbox("Ofício — Última Alteração", refs["oficios"])

        # ── Frota ────────────────────────────────────────────────
        st.divider()
        st.markdown("#### 🚍 Frota")

        col17, col18, col19 = st.columns(3)
        with col17:
            frota_tipo_veiculo_id  = _selectbox("Tipo de Veículo da Frota", refs["tipos_veiculo"])
        with col18:
            frota_ultimo_oficio_id = _selectbox("Último Ofício da Frota", refs["oficios"])
        with col19:
            frotaDataOficio = st.date_input("Data do Ofício da Frota", value=None)

        # ── Itinerário ───────────────────────────────────────────
        st.divider()
        st.markdown("#### 🗺️ Itinerário")

        col20, col21, col22 = st.columns(3)
        with col20:
            itinerarioIDA        = st.text_area("Itinerário IDA",   height=80,
                                                 placeholder="Descrição do itinerário de ida")
        with col21:
            itIda_oficio_id      = _selectbox("Ofício do Itin. IDA", refs["oficios"])
        with col22:
            itIda_data           = st.date_input("Data Itin. IDA", value=None)

        col23, col24, col25 = st.columns(3)
        with col23:
            itinerarioVOLTA      = st.text_area("Itinerário VOLTA", height=80,
                                                 placeholder="Descrição do itinerário de volta")
        with col24:
            itVolta_oficio_id    = _selectbox("Ofício do Itin. VOLTA", refs["oficios"])
        with col25:
            itVolta_data         = st.date_input("Data Itin. VOLTA", value=None)

        # ── Observação ───────────────────────────────────────────
        st.divider()
        observacao = st.text_area("📝 Observação", height=80,
                                   placeholder="Observações gerais sobre a linha")

        # ── Submit ───────────────────────────────────────────────
        submitted = st.form_submit_button(
            "💾 Salvar Linha",
            use_container_width=True,
            type="primary"
        )

    # ── Validação e gravação ─────────────────────────────────────
    if submitted:
        obrigatorios = {
            "Número da Linha": numeroLinha,
            "Vista":           vista,
            "Data de Criação": dataCriacaoLinha,
            "Serviço":         servico_label,
            "Operador":        operador_label,
        }
        faltando = [k for k, v in obrigatorios.items() if not v]

        if faltando:
            st.error(f"⚠️ Campos obrigatórios não preenchidos: {', '.join(faltando)}")
            return

        dados = {
            "numeroLinha":              numeroLinha,
            "dataCriacaoLinha":         dataCriacaoLinha,
            "servico":                  servico_label,
            "operador":                 operador_label,
            "vista":                    vista,
            "areaOperacional":          area_op_id,
            "oficio":                   oficio_id,
            "oficioprimeiroHistorico":  oficio_primeiro_id,
            "oficioUltimaAlteracao":    oficio_ult_alt_id,
            "tipoSistema":              tipo_sistema_id,
            "kmIDA":                    kmIDA,
            "kmVOLTA":                  kmVOLTA,
            "areaGeografica":           area_geo_id,
            "classificacaoEspacial":    classificacaoEspacial,
            "parametro":                parametro_id,
            "grupamentoBRS":            refs["grupamentos"].get(
                                            next((k for k, v in refs["grupamentos"].items()
                                                  if v == grupamento_label), ""), None
                                        ) if grupamento_label else None,
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

        with st.spinner("Salvando no SQLite..."):
            sucesso, mensagem = inserir_linha(dados)

        if sucesso:
            st.success(f"✅ {mensagem}")
            st.cache_data.clear()  # limpa cache para recarregar listas
        else:
            st.error(f"❌ {mensagem}")
