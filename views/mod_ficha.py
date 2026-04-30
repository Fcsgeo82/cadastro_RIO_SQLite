import streamlit as st
import re
import os
import base64
from models.db import obter_linha_por_id
from views.mod_cadastro import _carregar_todas_referencias
import streamlit.components.v1 as components
import pydeck as pdk
import pandas as pd
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
    
    def _gerar_linhas_direcao(tipo, sentido):
        pts = [it for it in it_lista if it.get("tipo") == tipo and str(it.get("sentido")) == str(sentido)]
        pts = sorted(pts, key=lambda x: x.get("ordem", 0))
        
        rows_html = ""
        if not pts:
            return "<tr><td colspan='3' style='text-align:center; color:#888;'>Nenhum ponto registrado</td></tr>"
            
        for p in pts:
            rows_html += f"<tr><td>{p.get('logradouro', '')}</td><td>{p.get('observacao', '')}</td><td>{p.get('bairro', '')}</td></tr>"
        return rows_html

    # Agrupamento dinâmico de Itinerários por Tipo
    tipos_it = sorted(list(set(it.get("tipo", "R") for it in it_lista)))
    # Garantir que "R" venha primeiro se existir
    if "R" in tipos_it:
        tipos_it.remove("R")
        tipos_it = ["R"] + tipos_it

    itinerarios_html = ""
    for t in tipos_it:
        nome_it = "Regular" if t == "R" else f"Alternativo ({t})"
        if t.startswith("A") and len(t) > 1:
            nome_it = f"Alternativo {t[1:]}"
        elif t == "A":
            nome_it = "Alternativo"
            
        of_id_it = next((it.get("oficio") for it in it_lista if it.get("tipo") == t), None)
        of_raw_it = _of_raw_lbl(of_id_it)
        
        ida_html = _gerar_linhas_direcao(t, "0")
        volta_html = _gerar_linhas_direcao(t, "1")
        
        itinerarios_html += f"""
        <div class="flex-header">
           <span>Itinerário {nome_it}</span>
           <span style="font-size:13px; font-weight:normal">Ofício de autorização: <b>{of_raw_it}</b></span>
        </div>
        <table class="itinerario-table">
            <tr><th colspan="3" class="it-sub-header">Itinerário de Ida</th></tr>
            <tr>
                <th style="width: 40%;">Logradouro</th>
                <th style="width: 30%;">Complemento</th>
                <th style="width: 30%;">Bairro</th>
            </tr>
            {ida_html}
            <tr><th colspan="3" class="it-sub-header">Itinerário de Volta</th></tr>
            <tr>
                <th>Logradouro</th>
                <th>Complemento</th>
                <th>Bairro</th>
            </tr>
            {volta_html}
        </table>
        """

    logo_dir = os.path.dirname(os.path.abspath(__file__))
    logo_svg = os.path.join(logo_dir, "logo_rio.svg")
    logo_png = os.path.join(logo_dir, "logo_rio.png")
    logo_img = ""
    if os.path.exists(logo_svg):
        with open(logo_svg, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        logo_img = f'<img src="data:image/svg+xml;base64,{logo_data}" style="width:180px;height:auto;">'
    elif os.path.exists(logo_png):
        with open(logo_png, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        logo_img = f'<img src="data:image/png;base64,{logo_data}" style="width:160px;height:auto;">'

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
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ 
        font-family: Arial, sans-serif; 
        font-size: 13px; 
        color: #000;
        padding: 0;
        background: white;
    }}
    .ficha-container {{
        max-width: 900px;
        margin: 0 auto;
        background: white;
    }}
    .header-bar {{
        background: linear-gradient(135deg, #ffdc00 0%, #ffdc00 100%);
        padding: 12px 20px;
        display: flex;
        align-items: center;
        gap: 20px;
    }}
    .header-bar .logo {{ }}
    .header-bar .title {{ color: #000; }}
    .header-bar .title h1 {{
        font-size: 1.4rem;
        margin: 0;
        font-family: Arial, sans-serif;
        font-weight: 800;
    }}
    .header-bar .title p {{
        margin: 2px 0 0;
        font-size: 0.85rem;
    }}
    .main-title {{
        font-size: 18px;
        font-weight: bold;
        color: #0b3c68;
        margin: 15px 20px 15px 20px;
        text-transform: uppercase;
    }}
    .section-title {{
        font-size: 14px;
        font-weight: bold;
        margin: 15px 20px 5px 20px;
        font-family: Arial, sans-serif;
        color: #000;
    }}
    .flex-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        font-family: Arial, sans-serif;
        font-size: 14px;
        font-weight: bold;
        margin: 15px 20px 5px 20px;
        color: #000;
    }}
    .data-table {{
        width: calc(100% - 40px);
        margin: 0 20px 15px 20px;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
        font-size: 13px;
    }}
    .data-table th, .data-table td {{
        border: 1px solid #000;
        padding: 5px 8px;
        vertical-align: top;
    }}
    .data-table th {{
        text-align: right;
        font-weight: bold;
        width: 20%;
        background: #f5f5f5;
    }}
    .itinerario-table {{ width: calc(100% - 40px); margin: 0 20px 10px 20px; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 11px; }}
    .itinerario-table th, .itinerario-table td {{ border: 1px solid #000; padding: 4px 6px; vertical-align: top; }}
    .itinerario-table th {{ background: #f5f5f5; font-weight: bold; text-align: left; }}
    .it-sub-header {{ background: #e9ecef !important; font-weight: bold; text-align: center; text-transform: uppercase; font-size: 11px; }}
    .btn-print {{
        background: #1a3a5c;
        color: white;
        border: none;
        padding: 8px 15px;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }}
    .btn-print:hover {{ background: #254d77; }}
    @media print {{
        .no-print {{ display: none !important; }}
        body {{ padding: 0; }}
        .header-bar {{
            background: #ffdc00 !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }}
    }}
    </style>
    </head>
    <body>
    <div class="ficha-container">
        <div class="header-bar">
            <div class="logo">{logo_img}</div>
            <div class="title" style="flex-grow: 1;">
                <h1>Rede Integrada de Ônibus</h1>
                <p>Cadastro e Consulta</p>
            </div>
            <div class="no-print">
                <button class="btn-print" onclick="window.print()">
                    <span>🖨️</span> Imprimir Ficha
                </button>
            </div>
        </div>
        
        <div class="main-title">FICHA CADASTRAL</div>
        
        <div class="section-title">Dados Cadastrais</div>
        <table class="data-table">
            <tr>
                <th>Linha:</th><td>{v_linha}</td>
                <th>Serviço:</th><td>{v_servico}</td>
            </tr>
            <tr>
                <th>Vista:</th><td colspan="3">{v_vista}</td>
            </tr>
            <tr>
                <th>Via:</th><td colspan="3">{v_via}</td>
            </tr>
            <tr>
                <th>Operador:</th><td>{v_operador}</td>
                <th>Data de Criação:</th><td>{v_criacao}</td>
            </tr>
            <tr>
                <th>Tipo de Sistema:</th><td>{v_tipo}</td>
                <th>Característica:</th><td>{v_caracteristica}</td>
            </tr>
            <tr>
                <th>Área Operacional:</th><td>{v_area_op}</td>
                <th>Parâmetro:</th><td>{v_parametro}</td>
            </tr>
            <tr>
                <th>Grupamento BRS:</th><td colspan="3">{v_grupamento}</td>
            </tr>
            <tr>
                <th>Extensão de ida:</th><td>{v_km_ida} km</td>
                <th>Extensão de volta:</th><td>{v_km_volta} km</td>
            </tr>
            <tr>
                <th>Observação:</th><td colspan="3">{v_obs}</td>
            </tr>
        </table>
        
        <div class="section-title">Dados processuais</div>
        <table class="data-table">
            <tr>
                <th>Ofício de criação:</th><td>{v_oficio_prim}</td>
                <th>Ofício de última alteração:</th><td>{v_oficio_ult}</td>
            </tr>
        </table>
        
        <div class="flex-header">
           <span>Frota autorizada</span>
           <span style="font-size:13px; font-weight:normal">Ofício de autorização: <b>{v_frota_of_raw}</b></span>
        </div>
        <table class="data-table">
            <tr>
                <th style="width: 15%">Tipo:</th>
                <td>{v_frota_tipo}</td>
                <th style="width: 20%">Data do Ofício:</th>
                <td>{v_frota_data}</td>
            </tr>
        </table>
        
        {itinerarios_html}
    </div>
    </body>
    </html>
    """

    import urllib.parse
    encoded_html = urllib.parse.quote(html_doc)
    iframe_html = f'<iframe id="ficha-frame" src="data:text/html;charset=utf-8,{encoded_html}" style="width:100%;height:900px;border:none;"></iframe>'
    st.markdown(iframe_html, unsafe_allow_html=True)

    # ── SEÇÃO GTFS ───────────────────────────────────────────
    st.write("")
    st.markdown("---")
    st.markdown("### 📊 Planejamento Operacional (GTFS)")
    
    gtfs = load_gtfs_data(v_linha)
    if gtfs:
        st.success(f"✅ Dados encontrados no arquivo: `{gtfs['filename']}`")
        
        tab_mapa, tab_horario = st.tabs(["🗺️ Mapa do Itinerário", "🕒 Quadro Horário (Partidas)"])
        
        with tab_mapa:
            shapes = gtfs["shapes"]
            shape_dirs = gtfs.get("shape_directions", pd.DataFrame())
            
            if not shapes.empty:
                # Seletor de Sentido
                sentido_opcoes = {0: "➡️ Ida", 1: "⬅️ Volta"}
                sel_sentidos = st.multiselect("Sentidos a exibir", [0, 1], default=[0, 1], format_func=lambda x: sentido_opcoes[x])
                
                # Filtrar shape_ids
                ids_filtrados = shape_dirs[shape_dirs['direction_id'].isin(sel_sentidos)]['shape_id'].unique()
                
                path_data = []
                point_data = [] # Para os markers de início/fim

                # Centralização do mapa
                first_shape = shapes[shapes['shape_id'].isin(ids_filtrados)]['shape_id'].iloc[0] if len(ids_filtrados) > 0 else shapes['shape_id'].iloc[0]
                center_lat = shapes[shapes['shape_id'] == first_shape]['shape_pt_lat'].mean()
                center_lon = shapes[shapes['shape_id'] == first_shape]['shape_pt_lon'].mean()

                for sid in ids_filtrados:
                    subset = shapes[shapes['shape_id'] == sid].sort_values('shape_pt_sequence')
                    coords = subset[['shape_pt_lon', 'shape_pt_lat']].values.tolist()
                    
                    # Determinar cor pelo sentido
                    direcao = shape_dirs[shape_dirs['shape_id'] == sid]['direction_id'].iloc[0]
                    cor = [30, 144, 255] if direcao == 0 else [255, 140, 0] # Azul p/ Ida, Laranja p/ Volta
                    
                    path_data.append({
                        "path": coords,
                        "name": f"{sentido_opcoes[direcao]} (Shape: {sid})",
                        "color": cor
                    })
                    
                    # Ponto de Início
                    point_data.append({
                        "pos": coords[0],
                        "name": f"Início - {sentido_opcoes[direcao]}",
                        "color": [0, 200, 0] # Verde
                    })
                    # Ponto de Fim
                    point_data.append({
                        "pos": coords[-1],
                        "name": f"Fim - {sentido_opcoes[direcao]}",
                        "color": [255, 0, 0] # Vermelho
                    })

                view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=12)
                
                # Camada do Trajeto
                layer_path = pdk.Layer(
                    "PathLayer",
                    path_data,
                    get_path="path",
                    get_color="color",
                    width_min_pixels=3,
                    pickable=True
                )
                
                # Camada de Início/Fim
                layer_points = pdk.Layer(
                    "ScatterplotLayer",
                    point_data,
                    get_position="pos",
                    get_color="color",
                    get_radius=150,
                    pickable=True
                )

                st.pydeck_chart(pdk.Deck(
                    layers=[layer_path, layer_points], 
                    initial_view_state=view_state, 
                    tooltip={"text": "{name}"}
                ))
            else:
                st.warning("Nenhuma geometria (shape) encontrada no GTFS para esta linha.")

        with tab_horario:
            partidas = processar_quadro_horario(gtfs)
            if not partidas.empty:
                sentidos = {0: "Ida", 1: "Volta"}
                
                # Filtro de Dia
                dias_disponiveis = sorted(partidas['tipo_dia'].unique())
                dia_sel = st.segmented_control("Tipo de Dia", dias_disponiveis, selection_mode="single", default=dias_disponiveis[0])
                
                if dia_sel:
                    df_dia = partidas[partidas['tipo_dia'] == dia_sel]
                    col_ida, col_volta = st.columns(2)
                    
                    with col_ida:
                        st.markdown(f"**➡️ {sentidos.get(0, 'Ida')}**")
                        ida_df = df_dia[df_dia['direction_id'] == 0].copy()
                        if not ida_df.empty:
                            ida_df['Horário'] = ida_df['departure_time'].str[:5]
                            st.dataframe(ida_df[['Horário']].reset_index(drop=True), use_container_width=True, height=300)
                        else:
                            st.caption("Sem partidas registradas.")

                    with col_volta:
                        st.markdown(f"**⬅️ {sentidos.get(1, 'Volta')}**")
                        volta_df = df_dia[df_dia['direction_id'] == 1].copy()
                        if not volta_df.empty:
                            volta_df['Horário'] = volta_df['departure_time'].str[:5]
                            st.dataframe(volta_df[['Horário']].reset_index(drop=True), use_container_width=True, height=300)
                        else:
                            st.caption("Sem partidas registradas.")
                
                st.caption("💡 Os horários exibidos são as partidas da primeira parada de cada viagem conforme planejado no GTFS.")
            else:
                st.warning("Nenhum quadro horário encontrado no GTFS para esta linha.")
    else:
        st.info("ℹ️ Nenhum dado de GTFS (shapes/horários) vinculado a esta linha foi encontrado na pasta `data/gtfs`.")
