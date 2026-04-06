import streamlit as st
import datetime
from db import obter_linha_por_id
from mod_cadastro import _carregar_todas_referencias

def _obter_label(dicionario_inverso, chave_busca):
    """Encontra a label de um ID pesquisando num dicionário {Label: ID}."""
    if not chave_busca:
        return "-"
    for label, id_ in dicionario_inverso.items():
        if str(id_) == str(chave_busca):
            return label
    return chave_busca

def parse_date(date_str):
    if not date_str:
        return None
    # Trata timezone do ISO
    if isinstance(date_str, str):
        if 'T' in date_str:
            try:
                # Caso de ISO format ISO 8601 ex: 2026-03-31T12:00:00+00:00
                d = date_str.replace('Z', '+00:00')
                dt = datetime.datetime.fromisoformat(d)
                return dt.replace(tzinfo=None) # Ignora o fuso para poder comparar
            except:
                pass
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return dt.replace(tzinfo=None)
        except:
            return None
    
    # Se já for objeto datetime explícito com fuso, vamos garantir
    if hasattr(date_str, "replace"):
        try:
             return date_str.replace(tzinfo=None)
        except:
             return date_str
    return date_str

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

    # --- Header ---
    col_back, _ = st.columns([1, 8])
    with col_back:
        if st.button("⬅️ Voltar", width='stretch'):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()
            
    st.markdown("---")
    st.markdown(f"## 🕰️ Histórico de Atualizações: **{dados.get('numeroLinha', 'N/A')}**")
    st.markdown(f"*{dados.get('vista', 'Sem Vista')}*")

    st.info("Abaixo você encontra a linha do tempo das principais alterações de **Ofícios** realizadas nesta linha.")

    events = []
    
    # 1. Criação
    events.append({
        "tipo": "🆕 Criação da Linha",
        "data_raw": dados.get("dataCriacaoLinha"),
        "date_obj": parse_date(dados.get("dataCriacaoLinha")),
        "oficio": dados.get("oficioprimeiroHistorico"),
    })
    
    # 2. Itinerário Ida
    if dados.get("itinerarioIdaOficio"):
        events.append({
            "tipo": "🗺️ Alteração Itinerário Ida",
            "data_raw": dados.get("itinerarioIdaData"),
            "date_obj": parse_date(dados.get("itinerarioIdaData")),
            "oficio": dados.get("itinerarioIdaOficio"),
        })

    # 3. Itinerário Volta
    if dados.get("itinerarioVoltaOficio"):
        events.append({
            "tipo": "🗺️ Alteração Itinerário Volta",
            "data_raw": dados.get("itinerarioVoltaData"),
            "date_obj": parse_date(dados.get("itinerarioVoltaData")),
            "oficio": dados.get("itinerarioVoltaOficio"),
        })

    # 4. Frota
    if dados.get("frotaUltimoOficio"):
        events.append({
            "tipo": "🚍 Alteração de Frota",
            "data_raw": dados.get("frotaDataOficio"),
            "date_obj": parse_date(dados.get("frotaDataOficio")),
            "oficio": dados.get("frotaUltimoOficio"),
        })

    # 5. Última Modificação
    events.append({
        "tipo": "💾 Última Modificação Geral",
        "data_raw": dados.get("ultimaAtualizacao"),
        "date_obj": parse_date(dados.get("ultimaAtualizacao")),
        "oficio": dados.get("oficioUltimaAlteracao"),
    })

    # Filtrar eventos que não conseguiram achar data
    valid_events = [e for e in events if e["date_obj"] is not None]
    
    # Ordenar por data cronológica descrecente (mais novo primeiro)
    valid_events.sort(key=lambda x: x["date_obj"], reverse=True)

    if not valid_events:
        st.warning("Não há ofícios de histórico com datas válidas para esta linha.")
        return

    st.markdown("### Linha do Tempo")
    for i, ev in enumerate(valid_events):
        label_ofn = "<Não informado>"
        assunto_label = "N/A"
        if ev['oficio']:
             label_ofn = _obter_label(refs['oficios'], ev['oficio'])
             assunto_label = refs.get('assuntos_oficios', {}).get(ev['oficio'], "Sem assunto registrado")
             
        data_formatada = ev['date_obj'].strftime('%d/%m/%Y')
        if "Geral" in ev["tipo"]:
             data_formatada = ev['date_obj'].strftime('%d/%m/%Y %H:%M')
             
        st.markdown(f'''
        <div style="padding: 16px; border-left: 4px solid #2d6a9f; background-color: #f7f9fc; margin-bottom: 16px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <p style="margin: 0 0 6px 0; color: #6b7a99; font-size: 0.85em; font-weight: 700; text-transform: uppercase;">
                🗓️ {data_formatada}
            </p>
            <h4 style="margin: 0 0 8px 0; color: #1a3a5c; font-size: 1.15em;">{ev["tipo"]}</h4>
            <p style="margin: 0; color: #334155;"><strong>Ofício:</strong> {label_ofn}</p>
            <p style="margin: 4px 0 0 0; color: #475569; font-size: 0.9em;"><em>Assunto: {assunto_label}</em></p>
        </div>
        ''', unsafe_allow_html=True)
