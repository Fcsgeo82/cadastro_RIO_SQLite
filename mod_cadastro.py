# =============================================================
# mod_cadastro.py — Cadastro de Linhas
# Campos baseados no schema real: CGR_Cadastro_Sistema_RIO.Linha
# =============================================================

import streamlit as st
import pandas as pd
from db import (
    inserir_linha, opcoes,
    carregar_servicos, carregar_operadores,
    carregar_areas_operacionais, 
    carregar_parametros_novos, carregar_caracteristicas,
    carregar_tipos_sistema, carregar_tipos_veiculo,
    carregar_grupamentos, carregar_oficios, carregar_assuntos_oficios
)


@st.cache_data(ttl=300, show_spinner=False)
def _carregar_todas_referencias():
    # Cache refresh: 2026-04-08 19:10
    """Carrega todas as tabelas de referência de uma vez (cache 5 min)."""
    return {
        "servicos":        opcoes(carregar_servicos()),
        "operadores":      opcoes(carregar_operadores()),
        "areas_op":        opcoes(carregar_areas_operacionais()),
        "tipos_sistema":   opcoes(carregar_tipos_sistema()),
        "tipos_veiculo":   opcoes(carregar_tipos_veiculo()),
        "parametros":      opcoes(carregar_parametros_novos()),
        "caracteristicas": opcoes(carregar_caracteristicas()),
        "grupamentos":     opcoes(carregar_grupamentos()),
        "oficios":         opcoes(carregar_oficios()),
        "assuntos_oficios": carregar_assuntos_oficios(),
    }


def _selectbox(label: str, opcoes_dict: dict, obrigatorio: bool = False) -> str | None:
    """Renderiza selectbox com opção vazia e retorna o ID selecionado."""
    sufixo  = " *" if obrigatorio else ""
    rotulos = ["— selecione —"] + list(opcoes_dict.keys())
    sel     = st.selectbox(label + sufixo, rotulos)
    return opcoes_dict.get(sel)  # None se "— selecione —"


def _itinerario_editor(titulo: str, key: str):
    """Renderiza um st.data_editor configurado para pontos de itinerário."""
    df_init = pd.DataFrame(columns=["Logradouro", "Complemento", "Bairro"])
    st.markdown(f"**{titulo}**")
    return st.data_editor(
        df_init,
        num_rows="dynamic",
        use_container_width=True,
        key=key,
        column_config={
            "Logradouro": st.column_config.TextColumn("Logradouro", width="large", required=True),
            "Complemento": st.column_config.TextColumn("Complemento", width="medium"),
            "Bairro": st.column_config.TextColumn("Bairro", width="medium"),
        }
    )


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

        colV1, colV2 = st.columns(2)
        with colV1:
            via = st.text_input("Via", placeholder="Via principal do trajeto")

        col4, col5 = st.columns(2)
        with col4:
            servico_label    = _selectbox("Serviço", refs["servicos"], obrigatorio=True)
        with col5:
            operador_label   = _selectbox("Operador", refs["operadores"], obrigatorio=True)

        # ── Classificação ────────────────────────────────────────
        st.divider()
        st.markdown("#### 🗂️ Classificação")

        col6, col7 = st.columns(2)
        with col6:
            area_op_id       = _selectbox("Área Operacional", refs["areas_op"])
        with col7:
            tipo_sistema_id  = _selectbox("Tipo de Sistema", refs["tipos_sistema"])

        col8, col9, col10 = st.columns(3)
        with col8:
            parametro_id     = _selectbox("Parâmetro", refs["parametros"])
        with col9:
            caracteristica_id = _selectbox("Característica", refs["caracteristicas"])
        with col10:
            grupamento_label = _selectbox("Grupamento BRS", refs["grupamentos"])

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
        st.info("ℹ️ O Ofício selecionado abaixo será registrado automaticamente como o **Primeiro Histórico** e como a **Última Alteração** desta linha inicialmente.")

        oficio_id = _selectbox("Ofício de Criação", refs["oficios"])
        if oficio_id:
            st.info(f"ℹ️ **Assunto:** {refs['assuntos_oficios'].get(oficio_id, 'Sem assunto')}")

        # ── Frota ────────────────────────────────────────────────
        st.divider()
        st.markdown("#### 🚍 Frota")

        col17, col18, col19 = st.columns(3)
        with col17:
            frota_tipo_veiculo_id  = _selectbox("Tipo de Veículo da Frota", refs["tipos_veiculo"])
        with col18:
            frota_ultimo_oficio_id = _selectbox("Último Ofício da Frota", refs["oficios"])
            if frota_ultimo_oficio_id:
                st.caption(f"**Assunto:** {refs['assuntos_oficios'].get(frota_ultimo_oficio_id, 'Sem assunto')}")
        with col19:
            frotaDataOficio = st.date_input("Data do Ofício da Frota", value=None)

        # ── Itinerários ──────────────────────────────────────────
        st.divider()
        st.markdown("#### 🗺️ Itinerários")
        st.info("💡 Preencha as tabelas com os pontos do itinerário. 'Complemento' será salvo como observação do ponto.")
        
        tabR, tabA = st.tabs(["Itinerário Regular", "Itinerário Alternativo"])
        
        with tabR:
            it_reg_oficio_id = _selectbox("Ofício de Autorização (Regular)", refs["oficios"])
            if it_reg_oficio_id:
                 st.caption(f"**Assunto:** {refs['assuntos_oficios'].get(it_reg_oficio_id, 'Sem assunto')}")
            df_reg_ida = _itinerario_editor("Ida", "reg_ida")
            st.write("") # Espaçador
            df_reg_volta = _itinerario_editor("Volta", "reg_volta")
                
        with tabA:
            it_alt_oficio_id = _selectbox("Ofício de Autorização (Alternativo)", refs["oficios"])
            if it_alt_oficio_id:
                 st.caption(f"**Assunto:** {refs['assuntos_oficios'].get(it_alt_oficio_id, 'Sem assunto')}")
            df_alt_ida = _itinerario_editor("Ida", "alt_ida")
            st.write("") # Espaçador
            df_alt_volta = _itinerario_editor("Volta", "alt_volta")

        # ── Observação ───────────────────────────────────────────
        st.divider()
        observacao = st.text_area("📝 Observação Geral", height=80,
                                   placeholder="Observações gerais sobre a linha")

        # ── Submit ───────────────────────────────────────────────
        submitted = st.form_submit_button(
            "💾 Salvar Linha",
            width='stretch',
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
            "via":                      via,
            "areaOperacional":          area_op_id,
            "oficio":                   oficio_id,
            "oficioprimeiroHistorico":  oficio_id,
            "oficioUltimaAlteracao":    oficio_id,
            "tipoSistema":              tipo_sistema_id,
            "kmIDA":                    kmIDA,
            "kmVOLTA":                  kmVOLTA,
            "parametro_novo":           parametro_id,
            "caracteristica":           caracteristica_id,
            "grupamentoBRS":            grupamento_label,
            "frotaUltimoOficio":        frota_ultimo_oficio_id,
            "frotaDataOficio":          str(frotaDataOficio) if frotaDataOficio else None,
            "observacao":               observacao,
            "itinerarios":              [], # Será preenchido abaixo
            "itinerarios_oficios": {
                "R": it_reg_oficio_id,
                "A": it_alt_oficio_id
            }
        }

        # Processar Itinerários das tabelas
        all_itinerarios = []
        
        def processar_df(df, tipo, sentido):
            if df is not None and not df.empty:
                for idx, row in df.iterrows():
                    if row.get("Logradouro"): # Só adiciona se tiver logradouro
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
        processar_df(df_alt_ida, "A", "0")
        processar_df(df_alt_volta, "A", "1")
        
        dados["itinerarios"] = all_itinerarios

        with st.spinner("Salvando no SQLite..."):
            sucesso, mensagem = inserir_linha(dados)

        if sucesso:
            st.success(f"✅ {mensagem}")
            st.cache_data.clear()  # limpa cache para recarregar listas
        else:
            st.error(f"❌ {mensagem}")
