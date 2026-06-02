import streamlit as st
import re
import pandas as pd
import streamlit.components.v1 as components
import pydeck as pdk
from models.db import obter_linha_por_id
from views.mod_cadastro import _carregar_todas_referencias
from models.gtfs_loader import load_gtfs_data, processar_quadro_horario
from utils.ui_components import render_logo, obter_label

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

    # --- Mapeamento de Dados ---
    v_linha = dados.get('numeroLinha', '-')

    # --- Carregar Dados GTFS (dinâmico, sem salvar no BD) ---
    gtfs = load_gtfs_data(v_linha)
    is_ativa = gtfs is not None
    v_gtfs_status = "Ativa" if is_ativa else "Inativa"
    v_gtfs_class = "status-ativa" if is_ativa else "status-inativa"
    v_servico = obter_label(refs.get('servicos', {}), dados.get('servico'))
    v_vista = dados.get('vista', '-')
    v_via = dados.get('via') or '-'
    v_operador = obter_label(refs.get('operadores', {}), dados.get('operador'))
    
    v_criacao = dados.get('dataCriacaoLinha') or '-'
    if "-" in v_criacao and len(v_criacao) == 10:
        v_criacao = v_criacao[8:10] + "/" + v_criacao[5:7] + "/" + v_criacao[0:4]

    v_tipo = obter_label(refs.get('tipos_sistema', {}), dados.get('tipoSistema'))
    v_area_op = obter_label(refs.get('areas_op', {}), dados.get('areaOperacional'))
    CORES_AREA = {
        "Roxo": "#8330A5", "Laranja": "#FF8C00", "Marrom": "#8B4513",
        "Ciano": "#00BFFF", "Rosa": "#FF69B4", "Verde": "#2E8B57",
        "Azul": "#1a3a5c", "Vermelho": "#DC143C", "Cinza": "#808080",
    }
    v_cor_area = next((hex for nome, hex in CORES_AREA.items() if nome in v_area_op), "#1a3a5c")
    v_grupamento = obter_label(refs.get('grupamentos', {}), dados.get('grupamentoBRS'))
    
    v_km_ida = str(dados.get('kmIDA')).replace('.',',') if dados.get('kmIDA') else '-'
    v_km_volta = str(dados.get('kmVOLTA')).replace('.',',') if dados.get('kmVOLTA') else '-'
    v_obs = dados.get('observacao') or '-'

    v_tipologia = obter_label(refs.get('tipologia', {}), dados.get('tipologiaRede'))
    v_abrangencia = obter_label(refs.get('abrangencia', {}), dados.get('abrangenciaTerritorial'))
    v_geometria = obter_label(refs.get('geometria', {}), dados.get('geometriaTracado'))
    v_hierarquia = obter_label(refs.get('hierarquia', {}), dados.get('hierarquiaAtendimento'))

    def _of_html(of_id):
        if not of_id: return "-"
        lbl = obter_label(refs.get('oficios', {}), of_id)
        return lbl

    v_oficio_prin = _of_html(dados.get('oficio'))
    oficio_ult_id = dados.get('oficioUltimaAlteracao')
    v_oficio_ult  = _of_html(oficio_ult_id)
    v_oficio_ult_assunto = refs.get("assuntos_oficios", {}).get(oficio_ult_id, "-") if oficio_ult_id else "-"
    
    v_frota_of_html = _of_html(dados.get('frotaUltimoOficio'))
    v_frota_tipo = obter_label(refs.get('tipos_veiculo', {}), dados.get('frotaTipoVeiculo'))
    v_frota_propulsao = obter_label(refs.get('tipos_propulsao', {}), dados.get('frotaTipoPropulsao'))
    
    v_frota_data = dados.get('frotaDataOficio') or '-'
    if "-" in v_frota_data and len(v_frota_data) == 10:
        v_frota_data = v_frota_data[8:10] + "/" + v_frota_data[5:7] + "/" + v_frota_data[0:4]

    # --- Processamento de Itinerários ---
    it_lista = dados.get("itinerarios", [])
    
    def _gerar_linhas_itinerario(tipo, sentido):
        pts = [it for it in it_lista if it.get("tipo") == tipo and str(it.get("sentido")) == str(sentido)]
        pts = sorted(pts, key=lambda x: x.get("ordem", 0))
        if not pts:
            return "<tr><td colspan='3' style='color:#888; font-style:italic;'>Sem registros</td></tr>"
        rows = ""
        for p in pts:
            rows += f"<tr><td>{p.get('logradouro', '')}</td><td>{p.get('observacao', '')}</td><td>{p.get('bairro', '')}</td></tr>"
        return rows

    tipos_it = sorted(list(set(it.get("tipo", "R") for it in it_lista)))
    if "R" in tipos_it:
        tipos_it.remove("R")
        tipos_it = ["R"] + tipos_it

    itinerarios_html = ""
    for t in tipos_it:
        nome_it = "ITINERÁRIO REGULAR" if t == "R" else f"ITINERÁRIO ALTERNATIVO ({t})"
        of_id_it = next((it.get("oficio") for it in it_lista if it.get("tipo") == t), None)
        of_raw_it = _of_html(of_id_it)
        
        itinerarios_html += f"""
        <div class="section-header">{nome_it}</div>
        <div class="data-grid">
            <div class="field" style="grid-column: span 6;"><span class="label">Tipo de Operação:</span><span class="value">{v_tipo}</span></div>
            <div class="field" style="grid-column: span 6;"><span class="label">Ofício de Autorização:</span><span class="value">{of_raw_it}</span></div>
        </div>
        
        <div class="it-sub-header">Itinerário de Ida</div>
        <table class="it-table">
            <thead><tr><th>Logradouro</th><th>Complemento</th><th>Bairro</th></tr></thead>
            <tbody>{_gerar_linhas_itinerario(t, "0")}</tbody>
        </table>
        
        <div class="it-sub-header">Itinerário de Volta</div>
        <table class="it-table">
            <thead><tr><th>Logradouro</th><th>Complemento</th><th>Bairro</th></tr></thead>
            <tbody>{_gerar_linhas_itinerario(t, "1")}</tbody>
        </table>
        """

    # --- Imagem do Logo ---
    logo_img = render_logo("140px")

    # --- HTML DOC ---
    html_doc = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap');
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Roboto', sans-serif; font-size: 11px; color: #000; background: #f0f2f5; }}
    .ficha-container {{
        max-width: 1000px;
        margin: 20px auto;
        background: white;
        padding-bottom: 60px;
        box-shadow: 0 0 30px rgba(0,0,0,0.15);
        border-radius: 8px;
    }}
    .header-rio {{ background: #ffdc00; height: 100px; display: flex; align-items: center; padding: 0 50px; }}
    .header-rio .ficha-label {{
        font-weight: 900;
        font-size: 24px;
        letter-spacing: 1px;
        margin-left: 30px;
    }}
    .section {{ margin: 30px 50px; }}
    .section-header {{ border-bottom: 3px solid #000; font-weight: 900; font-size: 14px; padding-bottom: 5px; margin-bottom: 15px; text-transform: uppercase; }}
    .data-grid {{ display: grid; grid-template-columns: repeat(12, 1fr); gap: 5px; margin-bottom: 12px; }}
    .field {{ display: flex; flex-direction: row; gap: 4px; align-items: baseline; }}
    .label {{ font-weight: 700; white-space: nowrap; font-size: 11px; }}
    .value {{ font-weight: 400; font-size: 11px; }}
    .area-badge {{ color: white; padding: 2px 30px; font-weight: bold; font-size: 11px; margin-left: 10px; border-radius: 0px; text-transform: lowercase; }}
    .status-badge {{ color: white; padding: 2px 8px; font-weight: bold; font-size: 9px; border-radius: 4px; text-transform: uppercase; margin-left: 5px; display: inline-block; }}
    .status-ativa {{ background-color: #2e7d32; }}
    .status-inativa {{ background-color: #c62828; }}
    .it-sub-header {{ font-weight: 700; margin: 10px 0 5px 0; font-size: 11px; text-decoration: none; }}
    .it-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
    .it-table th {{ text-align: left; font-weight: 700; padding: 4px 0; border-bottom: 1px solid #eee; }}
    .it-table td {{ padding: 4px 0; border-bottom: 1px dotted #ccc; vertical-align: top; width: 33.33%; }}
    .btn-print-box {{ position: fixed; bottom: 30px; right: 30px; z-index: 999; }}
    .btn-print {{
        background: #000; color: #ffdc00; border: none; padding: 12px 20px; border-radius: 50px;
        cursor: pointer; font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    @media print {{
        .no-print {{ display: none !important; }}
        body {{ background: white; padding: 0; }}
        .ficha-container {{ box-shadow: none; width: 100%; }}
        .header-rio {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
    }}
    </style>
    </head>
    <body>
    <div class="btn-print-box no-print">
        <button class="btn-print" onclick="window.print()"><span>🖨️</span> Imprimir Ficha</button>
    </div>
    <div class="ficha-container">
        <div class="header-rio">
            <div class="logo-rio">{logo_img}</div>
            <div class="ficha-label">FICHA CADASTRAL</div>
        </div>
        
        <!-- INFORMAÇÕES GERAIS -->
        <div class="section">
            <div class="section-header">INFORMAÇÕES GERAIS</div>
            <div class="data-grid">
                <div class="field" style="grid-column: span 6;"><span class="label">Linha:</span><span class="value">{v_linha}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Serviço:</span><span class="value">{v_servico}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Vista:</span><span class="value">{v_vista}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Grupamento BRS:</span><span class="value">{v_grupamento}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Via:</span><span class="value">{v_via}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Data de Criação:</span><span class="value">{v_criacao}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Extensão de ida:</span><span class="value">{v_km_ida} km</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Extensão de volta:</span><span class="value">{v_km_volta} km</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Plano Operacional (GTFS):</span><span class="status-badge {v_gtfs_class}">{v_gtfs_status}</span></div>
                <div class="field" style="grid-column: span 12;"><span class="label">Observação:</span><span class="value">{v_obs}</span></div>
            </div>
        </div>

        <!-- OPERADOR RESPONSÁVEL -->
        <div class="section">
            <div class="section-header">OPERADOR RESPONSÁVEL</div>
            <div class="data-grid">
                <div class="field" style="grid-column: span 6;"><span class="label">Lote:</span><span class="value">-</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Termo:</span><span class="value">-</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Razão Social:</span><span class="value">{v_operador}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Nome Fantasia:</span><span class="value">{v_operador}</span></div>
                <div class="field" style="grid-column: span 12;">
                    <span class="label">Área Operacional:</span>
                    <span class="area-badge" style="background:{v_cor_area}">{v_area_op}</span>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-header">CLASSIFICAÇÃO</div>
            <div class="data-grid">
                <div class="field" style="grid-column: span 6;"><span class="label">Hierarquia do Atendimento:</span><span class="value">{v_hierarquia}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Abrangência Territorial:</span><span class="value">{v_abrangencia}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Tipologia de Rede:</span><span class="value">{v_tipologia}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Geometria:</span><span class="value">{v_geometria}</span></div>
            </div>
        </div>

        <!-- DADOS PROCESSUAIS -->
        <div class="section">
            <div class="section-header">DADOS PROCESSUAIS</div>
            <div class="data-grid">
                <div class="field" style="grid-column: span 6;"><span class="label">Ofício de Criação:</span><span class="value">{v_oficio_prin}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Início de Vigência:</span><span class="value">{v_criacao}</span></div>
                <div class="field" style="grid-column: span 12; flex-direction: column; align-items: flex-start; gap: 2px;">
                    <div>
                        <span class="label">Ofício de Última Alteração:</span>
                        <span class="value">{v_oficio_ult}</span>
                    </div>
                    <div style="margin-top: 2px;">
                        <span class="label" style="font-weight: 500; color: #555;">Assunto:</span>
                        <span class="value" style="font-style: italic;">{v_oficio_ult_assunto}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- FROTA AUTORIZADA -->
        <div class="section">
            <div class="section-header">FROTA AUTORIZADA</div>
            <div class="data-grid">
                <div class="field" style="grid-column: span 6;"><span class="label">Tecnologia Autorizada:</span><span class="value">{v_frota_tipo}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Ofício de Autorização:</span><span class="value">{v_frota_of_html}</span></div>
                <div class="field" style="grid-column: span 6;"><span class="label">Propulsão:</span><span class="value">{v_frota_propulsao}</span></div>
            </div>
        </div>

        <!-- ITINERÁRIOS -->
        <div class="section">
            {itinerarios_html}
        </div>
    </div>
    </body>
    </html>
    """

    col_back, _ = st.columns([1.5, 8.5])
    with col_back:
        if st.button("⬅️ Voltar", width='stretch', key="btn_voltar_ficha"):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()

    import urllib.parse
    encoded_html = urllib.parse.quote(html_doc)
    iframe_html = f'<iframe id="ficha-frame" src="data:text/html;charset=utf-8,{encoded_html}" style="width:100%;height:1000px;border:none;"></iframe>'
    st.markdown(iframe_html, unsafe_allow_html=True)

    # ── SEÇÃO GTFS ───────────────────────────────────────────
    st.write("")
    st.markdown("---")
    st.markdown("### 📊 Planejamento Operacional (GTFS)")
    
    if gtfs:
        st.success(f"✅ Dados encontrados no arquivo: `{gtfs['filename']}`")
        tab_mapa, tab_horario, tab_stops = st.tabs(["🗺️ Mapa do Itinerário", "🕒 Quadro Horário (Partidas)", "🛑 Pontos de Parada"])
        
        with tab_mapa:
            shapes = gtfs["shapes"]
            shape_dirs = gtfs.get("shape_directions", pd.DataFrame())
            if not shapes.empty:
                sentido_opcoes = {0: "➡️ Ida", 1: "⬅️ Volta"}
                sel_sentidos = st.multiselect("Sentidos a exibir", [0, 1], default=[0, 1], format_func=lambda x: sentido_opcoes[x], key="mapa_sentidos")
                ids_filtrados = shape_dirs[shape_dirs['direction_id'].isin(sel_sentidos)]['shape_id'].unique()
                path_data = []; stop_points = []
                first_shape = shapes[shapes['shape_id'].isin(ids_filtrados)]['shape_id'].iloc[0] if len(ids_filtrados) > 0 else shapes['shape_id'].iloc[0]
                center_lat = shapes[shapes['shape_id'] == first_shape]['shape_pt_lat'].mean()
                center_lon = shapes[shapes['shape_id'] == first_shape]['shape_pt_lon'].mean()
                for sid in ids_filtrados:
                    subset = shapes[shapes['shape_id'] == sid].sort_values('shape_pt_sequence')
                    coords = subset[['shape_pt_lon', 'shape_pt_lat']].values.tolist()
                    direcao = shape_dirs[shape_dirs['shape_id'] == sid]['direction_id'].iloc[0]
                    cor = [30, 144, 255] if direcao == 0 else [255, 140, 0]
                    path_data.append({"path": coords, "name": f"{sentido_opcoes[direcao]}", "color": cor})
                df_st = gtfs["timetable"]
                if not df_st.empty:
                    df_st_sel = df_st[df_st['direction_id'].isin(sel_sentidos)]
                    unique_stops = df_st_sel[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']].drop_duplicates('stop_id')
                    for _, row in unique_stops.iterrows():
                        stop_points.append({"pos": [row['stop_lon'], row['stop_lat']], "name": row['stop_name'], "color": [255, 255, 255]})
                view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=12)
                layer_path = pdk.Layer("PathLayer", path_data, get_path="path", get_color="color", width_min_pixels=3, pickable=True)
                layer_stops = pdk.Layer("ScatterplotLayer", stop_points, get_position="pos", get_color="color", radius_units="pixels", get_radius=6, get_line_color=[0, 0, 0], get_line_width=1, stroked=True, filled=True, pickable=True)
                st.pydeck_chart(pdk.Deck(layers=[layer_path, layer_stops], initial_view_state=view_state, tooltip={"text": "{name}"}))
            else: st.warning("Nenhuma geometria encontrada.")

        with tab_horario:
            partidas = processar_quadro_horario(gtfs)
            if not partidas.empty:
                sentidos = {0: "Ida", 1: "Volta"}
                dias_disponiveis = sorted(partidas['tipo_dia'].unique())
                dia_sel = st.segmented_control("Tipo de Dia", dias_disponiveis, selection_mode="single", default=dias_disponiveis[0], key="gtfs_dia_sel")
                if dia_sel:
                    df_dia = partidas[partidas['tipo_dia'] == dia_sel]
                    col_ida, col_volta = st.columns(2)
                    with col_ida:
                        st.markdown(f"**➡️ {sentidos.get(0, 'Ida')}**")
                        ida_df = df_dia[df_dia['direction_id'] == 0].copy()
                        if not ida_df.empty:
                            ida_df['Horário'] = ida_df['departure_time'].str[:5]
                            st.dataframe(ida_df[['Horário']].reset_index(drop=True), width='stretch', height=300)
                    with col_volta:
                        st.markdown(f"**⬅️ {sentidos.get(1, 'Volta')}**")
                        volta_df = df_dia[df_dia['direction_id'] == 1].copy()
                        if not volta_df.empty:
                            volta_df['Horário'] = volta_df['departure_time'].str[:5]
                            st.dataframe(volta_df[['Horário']].reset_index(drop=True), width='stretch', height=300)
            else: st.warning("Nenhum quadro horário encontrado.")

        with tab_stops:
            df_stops = gtfs["timetable"]
            if not df_stops.empty:
                sentidos = {0: "Ida", 1: "Volta"}
                col_s_ida, col_s_volta = st.columns(2)
                for s_id, col in zip([0, 1], [col_s_ida, col_s_volta]):
                    with col:
                        st.markdown(f"**📍 {sentidos.get(s_id)}**")
                        df_s = df_stops[df_stops['direction_id'] == s_id]
                        if not df_s.empty:
                            trip_exemplo = df_s.groupby('trip_id')['stop_sequence'].count().idxmax()
                            pontos = df_s[df_s['trip_id'] == trip_exemplo].sort_values('stop_sequence')
                            st.dataframe(pontos[['stop_sequence', 'stop_name']].rename(columns={'stop_sequence': 'Seq', 'stop_name': 'Ponto de Parada'}), width='stretch', hide_index=True, height=450)
    else: st.info("ℹ️ Nenhum dado de GTFS encontrado.")
