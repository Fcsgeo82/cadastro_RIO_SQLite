import streamlit as st
import re
import os
import base64
import pandas as pd
from models.db import obter_linha_por_id
from views.mod_cadastro import _carregar_todas_referencias
import streamlit.components.v1 as components
import pydeck as pdk
from models.gtfs_loader import load_gtfs_data, processar_quadro_horario


def _obter_label(dicionario_inverso, chave_busca):
    if not chave_busca:
        return "-"
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

    v_linha = dados.get('numeroLinha', '-')
    v_servico = _obter_label(refs.get('servicos', {}), dados.get('servico'))
    v_vista = dados.get('vista', '-')
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

    def _of_html(of_id):
        if not of_id: return "-"
        lbl = _obter_label(refs.get('oficios', {}), of_id)
        ass = refs.get('assuntos_oficios', {}).get(of_id, '')
        if ass and ass != "Sem assunto":
             return f"{lbl}<br><span style='font-size:10.5px; font-weight:normal; color:#555;'>Assunto: {ass}</span>"
        return lbl

    def _of_raw_lbl(of_id):
        if not of_id: return "-"
        return _obter_label(refs.get('oficios', {}), of_id)

    v_oficio_prin = _of_html(dados.get('oficio'))
    v_oficio_prim = _of_html(dados.get('oficioprimeiroHistorico'))
    v_oficio_ult  = _of_html(dados.get('oficioUltimaAlteracao'))
    
    v_frota_of_html = _of_html(dados.get('frotaUltimoOficio'))
    v_frota_of_raw  = _of_raw_lbl(dados.get('frotaUltimoOficio'))
    v_frota_tipo = _obter_label(refs.get('tipos_veiculo', {}), dados.get('frotaTipoVeiculo'))
    if dados.get('frotaDataOficio'):
        v_frota_data = str(dados.get('frotaDataOficio'))
        if "-" in v_frota_data and len(v_frota_data) == 10: 
            v_frota_data = v_frota_data[8:10] + "/" + v_frota_data[5:7] + "/" + v_frota_data[0:4]
    else: v_frota_data = '-'

    # Processamento de Itinerários para o HTML
    it_lista = dados.get("itinerarios", [])
    
    def _gerar_linhas_itinerario(tipo, sentido):
        pts = [it for it in it_lista if it.get("tipo") == tipo and str(it.get("sentido")) == str(sentido)]
        pts = sorted(pts, key=lambda x: x.get("ordem", 0))
        
        rows_html = ""
        if not pts:
            return "<tr><td style='color:#888;'>Nenhum ponto registrado</td></tr>"
            
        for p in pts:
            obs = f"<span class='obs'>{p.get('observacao', '')}</span>" if p.get('observacao') else ""
            rows_html += f"<tr><td>{p.get('logradouro', '')} {obs}</td></tr>"
        return rows_html

    # Agrupamento dinâmico de Itinerários por Tipo
    tipos_it = sorted(list(set(it.get("tipo", "R") for it in it_lista)))
    if "R" in tipos_it:
        tipos_it.remove("R")
        tipos_it = ["R"] + tipos_it

    itinerarios_redesenhados_html = ""
    for t in tipos_it:
        nome_it = "Regular" if t == "R" else f"Alternativo ({t})"
        if t.startswith("A") and len(t) > 1:
            nome_it = f"Alternativo {t[1:]}"
        elif t == "A":
            nome_it = "Alternativo"
            
        of_id_it = next((it.get("oficio") for it in it_lista if it.get("tipo") == t), None)
        of_raw_it = _of_raw_lbl(of_id_it)
        
        ida_html = _gerar_linhas_itinerario(t, "0")
        volta_html = _gerar_linhas_itinerario(t, "1")
        
        itinerarios_redesenhados_html += f"""
        <div class="it-block">
            <div class="it-side-title">
                <span>{nome_it}</span>
                <span style="font-size:10px; font-weight:normal">Ofício: {of_raw_it}</span>
            </div>
            <div class="it-wrapper">
                <div class="it-side">
                    <div style="font-weight:bold; border-bottom:1px solid #000; margin-bottom:5px;">Itinerário de Ida</div>
                    <table class="it-table">{ida_html}</table>
                </div>
                <div class="it-side">
                    <div style="font-weight:bold; border-bottom:1px solid #000; margin-bottom:5px;">Itinerário de Volta</div>
                    <table class="it-table">{volta_html}</table>
                </div>
            </div>
        </div>
        """

    logo_dir = os.path.dirname(os.path.abspath(__file__))
    logo_svg = os.path.join(logo_dir, "logo_rio.svg")
    logo_png = os.path.join(logo_dir, "logo_rio.png")
    logo_img = ""
    if os.path.exists(logo_svg):
        with open(logo_svg, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        logo_img = f'<img src="data:image/svg+xml;base64,{logo_data}" style="width:140px;height:auto;">'
    elif os.path.exists(logo_png):
        with open(logo_png, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        logo_img = f'<img src="data:image/png;base64,{logo_data}" style="width:130px;height:auto;">'

    col_back, _ = st.columns([1.5, 8.5])
    with col_back:
        if st.button("⬅️ Voltar", width='stretch'):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()
            
    html_doc = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap');
    
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ 
        font-family: 'Roboto', sans-serif; 
        font-size: 11px; 
        color: #000;
        padding: 0;
        background: #f0f2f5;
    }}
    .ficha-container {{
        max-width: 1000px;
        margin: 0 auto;
        background: white;
        min-height: 297mm;
        padding-bottom: 50px;
        box-shadow: 0 0 20px rgba(0,0,0,0.1);
    }}
    
    /* Header Estilo Rio */
    .header-rio {{
        background: #ffdc00;
        height: 80px;
        display: flex;
        align-items: center;
        padding: 0 30px;
        position: relative;
    }}
    .header-rio .logo-rio {{
        display: flex;
        align-items: center;
        gap: 15px;
    }}
    .header-rio .ficha-label {{
        flex-grow: 1;
        text-align: center;
        font-weight: 900;
        font-size: 20px;
        letter-spacing: 1px;
    }}
    
    /* Seções */
    .section {{
        margin: 20px 30px 5px 30px;
    }}
    .section-header {{
        border-bottom: 2px solid #000;
        font-weight: 900;
        font-size: 13px;
        padding-bottom: 3px;
        margin-bottom: 10px;
        text-transform: uppercase;
    }}
    
    /* Grid de Dados */
    .data-grid {{
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: 10px;
        margin-bottom: 15px;
    }}
    .field {{
        display: flex;
        flex-direction: row;
        gap: 5px;
        align-items: baseline;
    }}
    .label {{
        font-weight: 700;
        white-space: nowrap;
    }}
    .value {{
        font-weight: 400;
    }}
    
    /* Badge Área Operacional */
    .area-badge {{
        color: white;
        padding: 2px 10px;
        font-weight: bold;
        font-size: 11px;
        margin-left: 10px;
    }}

    /* Tabelas de Itinerário */
    .it-wrapper {{
        display: flex;
        gap: 20px;
        margin-bottom: 20px;
    }}
    .it-side {{
        flex: 1;
    }}
    .it-side-title {{
        font-weight: 700;
        border-bottom: 2px solid #ccc;
        padding-bottom: 3px;
        margin-bottom: 5px;
        display: flex;
        justify-content: space-between;
        text-transform: uppercase;
        font-size: 12px;
    }}
    .it-table {{
        width: 100%;
        border-collapse: collapse;
    }}
    .it-table td {{
        padding: 3px 0;
        border-bottom: 1px dotted #ccc;
    }}
    .it-table .obs {{
        font-style: italic;
        color: #555;
        font-size: 10px;
        margin-left: 10px;
    }}
    
    .it-block {{
        margin-bottom: 20px;
    }}

    .btn-print-box {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 999;
    }}
    .btn-print {{
        background: #000;
        color: #ffdc00;
        border: none;
        padding: 12px 20px;
        border-radius: 50px;
        cursor: pointer;
        font-weight: bold;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }}
    .btn-print:hover {{ transform: scale(1.05); }}

    @media print {{
        .no-print {{ display: none !important; }}
        body {{ background: white; padding: 0; }}
        .ficha-container {{ box-shadow: none; max-width: 100%; width: 100%; }}
        .header-rio {{ 
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }}
    }}
    </style>
    </head>
    <body>
    <div class="btn-print-box no-print">
        <button class="btn-print" onclick="window.print()">
            <span>🖨️</span> Imprimir Ficha
        </button>
    </div>

    <div class="ficha-container">
        <!-- HEADER -->
        <div class="header-rio">
            <div class="logo-rio">
                {logo_img}
            </div>
            <div class="ficha-label">FICHA CADASTRAL</div>
        </div>
        
        <!-- SEÇÃO 1: INFORMAÇÕES DA LINHA -->
        <div class="section">
            <div class="section-header">Informações da Linha</div>
            <div class="data-grid">
                <div class="field" style="grid-column: span 3;">
                    <span class="label">Linha:</span><span class="value">{v_linha}</span>
                </div>
                <div class="field" style="grid-column: span 5;">
                    <span class="label">Serviço:</span><span class="value">{v_servico}</span>
                </div>
                <div class="field" style="grid-column: span 4;">
                    <span class="label">Verificador:</span><span class="value">A</span>
                </div>
                
                <div class="field" style="grid-column: span 12;">
                    <span class="label">Linha Comercial:</span><span class="value">{v_vista}</span>
                </div>
                
                <div class="field" style="grid-column: span 12;">
                    <span class="label">Via:</span><span class="value">{v_via}</span>
                </div>
            </div>
        </div>

        <!-- SEÇÃO 2: OPERADOR RESPONSÁVEL -->
        <div class="section">
            <div class="section-header">Operador Responsável</div>
            <div class="data-grid">
                <div class="field" style="grid-column: span 4;">
                    <span class="label">Lote:</span><span class="value">-</span>
                </div>
                <div class="field" style="grid-column: span 5;">
                    <span class="label">Área Operacional:</span><span class="value">{v_area_op}</span>
                    <span class="area-badge" style="background:{'#8330A5' if 'Roxo' in v_area_op else '#1a3a5c'}">{v_area_op.split('-')[-1].strip() if '-' in v_area_op else ''}</span>
                </div>
                <div class="field" style="grid-column: span 3;">
                    <span class="label">Grupamento:</span><span class="value">{v_grupamento}</span>
                </div>

                <div class="field" style="grid-column: span 6;">
                    <span class="label">Parâmetro:</span><span class="value">{v_parametro}</span>
                </div>
                <div class="field" style="grid-column: span 6;">
                    <span class="label">Característica:</span><span class="value">{v_caracteristica}</span>
                </div>

                <div class="field" style="grid-column: span 12;">
                    <span class="label">Razão Social:</span><span class="value">{v_operador}</span>
                </div>
                
                <div class="field" style="grid-column: span 12;">
                    <span class="label">Nome Fantasia:</span><span class="value">{v_operador}</span>
                </div>
            </div>
        </div>

        <!-- SEÇÃO 3: DADOS PROCESSUAIS -->
        <div class="section">
            <div class="section-header">Dados Processuais</div>
            <div class="data-grid">
                <div class="field" style="grid-column: span 6;">
                    <span class="label">Ofício de Criação:</span><span class="value">{v_oficio_prin}</span>
                </div>
                <div class="field" style="grid-column: span 6;">
                    <span class="label">Início de Vigência:</span><span class="value">{v_criacao}</span>
                </div>
            </div>
        </div>

        <!-- SEÇÃO 4: FROTA AUTORIZADA -->
        <div class="section">
            <div class="section-header">Frota Autorizada</div>
            <div class="data-grid">
                <div class="field" style="grid-column: span 6;">
                    <span class="label">Tecnologia Autorizada:</span><span class="value">{v_frota_tipo}</span>
                </div>
                <div class="field" style="grid-column: span 6;">
                    <span class="label">Ofício de Autorização:</span><span class="value">{v_frota_of_html}</span>
                </div>
                <div class="field" style="grid-column: span 4;">
                    <span class="label">Extensão Ida:</span><span class="value">{v_km_ida} km</span>
                </div>
                <div class="field" style="grid-column: span 4;">
                    <span class="label">Extensão Volta:</span><span class="value">{v_km_volta} km</span>
                </div>
                <div class="field" style="grid-column: span 4;">
                    <span class="label">Data Ofício:</span><span class="value">{v_frota_data}</span>
                </div>
            </div>
        </div>

        <!-- SEÇÃO 5: ITINERÁRIOS -->
        <div class="section">
            <div class="section-header">Itinerário Autorizado</div>
            {itinerarios_redesenhados_html}
        </div>
        
        <div class="section">
            <div class="section-header">Observações</div>
            <div style="padding: 5px; font-style: italic;">{v_obs}</div>
        </div>
    </div>
    </body>
    </html>
    """

    import urllib.parse
    encoded_html = urllib.parse.quote(html_doc)
    iframe_html = f'<iframe id="ficha-frame" src="data:text/html;charset=utf-8,{encoded_html}" style="width:100%;height:1000px;border:none;"></iframe>'
    st.markdown(iframe_html, unsafe_allow_html=True)

    # ── SEÇÃO GTFS ───────────────────────────────────────────
    st.write("")
    st.markdown("---")
    st.markdown("### 📊 Planejamento Operacional (GTFS)")
    
    gtfs = load_gtfs_data(v_linha)
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
                
                path_data = []
                stop_points = []

                first_shape = shapes[shapes['shape_id'].isin(ids_filtrados)]['shape_id'].iloc[0] if len(ids_filtrados) > 0 else shapes['shape_id'].iloc[0]
                center_lat = shapes[shapes['shape_id'] == first_shape]['shape_pt_lat'].mean()
                center_lon = shapes[shapes['shape_id'] == first_shape]['shape_pt_lon'].mean()

                for sid in ids_filtrados:
                    subset = shapes[shapes['shape_id'] == sid].sort_values('shape_pt_sequence')
                    coords = subset[['shape_pt_lon', 'shape_pt_lat']].values.tolist()
                    direcao = shape_dirs[shape_dirs['shape_id'] == sid]['direction_id'].iloc[0]
                    cor = [30, 144, 255] if direcao == 0 else [255, 140, 0]
                    
                    path_data.append({
                        "path": coords,
                        "name": f"{sentido_opcoes[direcao]} (Shape: {sid})",
                        "color": cor
                    })

                df_st = gtfs["timetable"]
                if not df_st.empty:
                    df_st_sel = df_st[df_st['direction_id'].isin(sel_sentidos)]
                    unique_stops = df_st_sel[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']].drop_duplicates('stop_id')
                    for _, row in unique_stops.iterrows():
                        stop_points.append({
                            "pos": [row['stop_lon'], row['stop_lat']],
                            "name": row['stop_name'],
                            "color": [255, 255, 255]
                        })

                view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=12)
                layer_path = pdk.Layer("PathLayer", path_data, get_path="path", get_color="color", width_min_pixels=3, pickable=True)
                layer_stops = pdk.Layer("ScatterplotLayer", stop_points, get_position="pos", get_color="color", radius_units="pixels", get_radius=6, get_line_color=[0, 0, 0], get_line_width=1, stroked=True, filled=True, pickable=True)

                st.pydeck_chart(pdk.Deck(layers=[layer_path, layer_stops], initial_view_state=view_state, tooltip={"text": "{name}"}))
            else:
                st.warning("Nenhuma geometria encontrada no GTFS.")

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
                            st.dataframe(ida_df[['Horário']].reset_index(drop=True), use_container_width=True, height=300)
                        else: st.caption("Sem partidas.")
                    with col_volta:
                        st.markdown(f"**⬅️ {sentidos.get(1, 'Volta')}**")
                        volta_df = df_dia[df_dia['direction_id'] == 1].copy()
                        if not volta_df.empty:
                            volta_df['Horário'] = volta_df['departure_time'].str[:5]
                            st.dataframe(volta_df[['Horário']].reset_index(drop=True), use_container_width=True, height=300)
                        else: st.caption("Sem partidas.")
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
                            st.dataframe(pontos[['stop_sequence', 'stop_name']].rename(columns={'stop_sequence': 'Seq', 'stop_name': 'Ponto de Parada'}), use_container_width=True, hide_index=True, height=450)
                        else: st.caption("Sem pontos.")
    else:
        st.info("ℹ️ Nenhum dado de GTFS encontrado.")
