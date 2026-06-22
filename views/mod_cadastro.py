# =============================================================
# mod_cadastro.py — Cadastro de Linhas
# Campos baseados no schema real: CGR_Cadastro_Sistema_RIO.Linha
# =============================================================

import streamlit as st
import pandas as pd
import datetime
from models.db import (
    inserir_linha, opcoes,
    carregar_servicos, carregar_operadores,
    carregar_areas_operacionais, 
    carregar_parametros_novos, carregar_caracteristicas,
    carregar_tipos_sistema, carregar_tipos_veiculo, carregar_tipos_propulsao,
    carregar_grupamentos, carregar_oficios, carregar_assuntos_oficios,
    carregar_tipologia_rede, carregar_abrangencia_territorial,
    carregar_geometria_tracado, carregar_hierarquia_atendimento
)


@st.cache_data(ttl=300, show_spinner=False)
def _carregar_todas_referencias():
    # Cache refresh: 2026-04-08 19:10
    """Carrega todas as tabelas de referência de uma vez (cache 5 min)."""
    df_of = carregar_oficios()
    tipologia_dict = opcoes(carregar_tipologia_rede())
    tipologia_dict.pop("Noturna", None)
    return {
        "servicos":        opcoes(carregar_servicos()),
        "operadores":      opcoes(carregar_operadores()),
        "areas_op":        opcoes(carregar_areas_operacionais()),
        "tipos_sistema":   opcoes(carregar_tipos_sistema()),
        "tipos_veiculo":   opcoes(carregar_tipos_veiculo()),
        "tipos_propulsao": opcoes(carregar_tipos_propulsao()),
        "grupamentos":     opcoes(carregar_grupamentos()),
        "oficios":         opcoes(df_of),
        "datas_oficios":   dict(zip(df_of["id"], df_of["dataOficio"])) if not df_of.empty else {},
        "assuntos_oficios": carregar_assuntos_oficios(),
        "tipologia":       tipologia_dict,
        "abrangencia":     opcoes(carregar_abrangencia_territorial()),
        "geometria":       opcoes(carregar_geometria_tracado()),
        "hierarquia":      opcoes(carregar_hierarquia_atendimento()),
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
        width='stretch',
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

    # Seleção de Ofício fora do form para permitir a vinculação reativa da data
    st.markdown("#### 📄 Ofício de Criação")
    col_of1, col_of2 = st.columns([2, 1])
    with col_of1:
        oficio_id = _selectbox("Selecione o Ofício que originou a linha", refs["oficios"], obrigatorio=True)
    
    dt_default = None
    if oficio_id and refs["datas_oficios"].get(oficio_id):
        try:
            # Data no DB costuma estar em YYYY-MM-DD
            dt_str = refs["datas_oficios"][oficio_id]
            if dt_str:
                dt_default = datetime.datetime.strptime(dt_str[:10], "%Y-%m-%d").date()
        except Exception as e:
            st.error(f"Erro ao processar data do ofício: {e}")
            dt_default = None

    if oficio_id:
        st.info(f"ℹ️ **Assunto do Ofício:** {refs['assuntos_oficios'].get(oficio_id, 'Sem assunto')}")
        if dt_default:
            st.success(f"📅 A Data de Criação abaixo foi vinculada à data do ofício: **{dt_default.strftime('%d/%m/%Y')}**")

    with st.form("form_cadastro", clear_on_submit=True):

        # ── Identificação ────────────────────────────────────────
        st.markdown("#### 📋 Identificação")
        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            numeroLinha = st.text_input("Número da Linha *", placeholder="Ex: 001, 474-A")
        with col2:
            vista = st.text_input("Vista *", placeholder="Ex: CENTRAL - MÉIER")
        with col3:
            dataCriacaoLinha = st.date_input("Data de Criação *", value=dt_default)

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
            tipo_sistema_id  = _selectbox("Tipo de Operação", refs["tipos_sistema"])

        col11, col12 = st.columns(2)
        with col11:
            dias_op_selecionados = st.multiselect("Dias de Operação", list(refs["tipologia"].keys()))
            tipologia_id = ",".join([refs["tipologia"][d] for d in dias_op_selecionados]) if dias_op_selecionados else None
        with col12:
            abrangencia_id   = _selectbox("Abrangência Territorial", refs["abrangencia"])
        
        col13, col14 = st.columns(2)
        with col13:
            geometria_id     = _selectbox("Geometria do Traçado", refs["geometria"])
        with col14:
            hierarquia_id    = _selectbox("Hierarquia de Atendimento", refs["hierarquia"])

        col15, col16 = st.columns(2)
        with col15:
            grupamento_label = _selectbox("Grupamento BRS", refs["grupamentos"])
        with col16:
            pass # Espaçador

        # ── Quilometragem ────────────────────────────────────────
        st.divider()
        st.markdown("#### 📏 Quilometragem")

        colQ1, colQ2 = st.columns(2)
        with colQ1:
            kmIDA   = st.number_input("KM Ida",   min_value=0.0, step=0.1, value=None,
                                       placeholder="Ex: 12.5")
        with colQ2:
            kmVOLTA = st.number_input("KM Volta", min_value=0.0, step=0.1, value=None,
                                       placeholder="Ex: 12.5")

        # Ofício de criação já selecionado acima
        st.info("ℹ️ O Ofício selecionado no topo será registrado automaticamente como o **Primeiro Histórico** e como a **Última Alteração** desta linha inicialmente.")

        # ── Frota ────────────────────────────────────────────────
        st.divider()
        st.markdown("#### 🚍 Frota")

        col17, col18, col19, col20 = st.columns(4)
        with col17:
            frota_tipo_veiculo_id  = _selectbox("Tipo de Veículo da Frota", refs["tipos_veiculo"])
        with col18:
            frota_tipo_propulsao_id = _selectbox("Propulsão", refs["tipos_propulsao"])
        with col19:
            frota_ultimo_oficio_id = _selectbox("Ofício de Autorização da Frota", refs["oficios"])
            if frota_ultimo_oficio_id:
                st.caption(f"**Assunto:** {refs['assuntos_oficios'].get(frota_ultimo_oficio_id, 'Sem assunto')}")
        with col20:
            frotaDataOficio = st.date_input("Data do Ofício da Frota", value=None)

        # ── Itinerários ──────────────────────────────────────────
        st.divider()
        st.markdown("#### 🗺️ Itinerários")
        st.info("💡 Preencha as tabelas com os pontos do itinerário. 'Complemento' será salvo como observação do ponto.")
        
        tabR, tabA1, tabA2, tabA3 = st.tabs(["Itinerário Regular", "Alternativo 1", "Alternativo 2", "Alternativo 3"])
        
        with tabR:
            it_reg_oficio_id = _selectbox("Ofício de Autorização (Regular)", refs["oficios"])
            if it_reg_oficio_id:
                 st.caption(f"**Assunto:** {refs['assuntos_oficios'].get(it_reg_oficio_id, 'Sem assunto')}")
            df_reg_ida = _itinerario_editor("Ida", "reg_ida")
            st.write("") # Espaçador
            df_reg_volta = _itinerario_editor("Volta", "reg_volta")
                
        with tabA1:
            it_a1_descricao = st.text_input("Descrição (Alt 1)", placeholder="Ex: Via Av. Brasil, etc.")
            df_a1_ida = _itinerario_editor("Ida", "a1_ida")
            st.write("") # Espaçador
            df_a1_volta = _itinerario_editor("Volta", "a1_volta")

        with tabA2:
            it_a2_descricao = st.text_input("Descrição (Alt 2)", placeholder="Ex: Via Linha Amarela, etc.")
            df_a2_ida = _itinerario_editor("Ida", "a2_ida")
            st.write("") # Espaçador
            df_a2_volta = _itinerario_editor("Volta", "a2_volta")

        with tabA3:
            it_a3_descricao = st.text_input("Descrição (Alt 3)", placeholder="Ex: Via Túnel Rebouças, etc.")
            df_a3_ida = _itinerario_editor("Ida", "a3_ida")
            st.write("") # Espaçador
            df_a3_volta = _itinerario_editor("Volta", "a3_volta")

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
            "Ofício de Criação": oficio_id,
            "Número da Linha":   numeroLinha,
            "Vista":             vista,
            "Data de Criação":   dataCriacaoLinha,
            "Serviço":           servico_label,
            "Operador":          operador_label,
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
            "parametro_novo":           None,
            "caracteristica":           None,
            "grupamentoBRS":            grupamento_label,
            "frotaTipoVeiculo":         frota_tipo_veiculo_id,
            "frotaTipoPropulsao":       frota_tipo_propulsao_id,
            "frotaUltimoOficio":        frota_ultimo_oficio_id,
            "frotaDataOficio":          str(frotaDataOficio) if frotaDataOficio else None,
            "observacao":               observacao,
            "tipologiaRede":            tipologia_id,
            "abrangenciaTerritorial":   abrangencia_id,
            "geometriaTracado":         geometria_id,
            "hierarquiaAtendimento":    hierarquia_id,
            "itinerarios":              [], # Será preenchido abaixo
            "itinerarios_oficios": {
                "R": it_reg_oficio_id,
                "A1": it_a1_descricao,
                "A2": it_a2_descricao,
                "A3": it_a3_descricao
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
        processar_df(df_a1_ida, "A1", "0")
        processar_df(df_a1_volta, "A1", "1")
        processar_df(df_a2_ida, "A2", "0")
        processar_df(df_a2_volta, "A2", "1")
        processar_df(df_a3_ida, "A3", "0")
        processar_df(df_a3_volta, "A3", "1")
        
        dados["itinerarios"] = all_itinerarios

        with st.spinner("Salvando no SQLite..."):
            sucesso, mensagem = inserir_linha(dados)

        if sucesso:
            st.success(f"✅ {mensagem}")
            st.cache_data.clear()  # limpa cache para recarregar listas
        else:
            st.error(f"❌ {mensagem}")
