import streamlit as st
import re
import os
import base64
from db import obter_linha_por_id
from mod_cadastro import _carregar_todas_referencias
import streamlit.components.v1 as components


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
    v_class = dados.get('classificacaoEspacial') or '-'
    v_area_op = _obter_label(refs.get('areas_op', {}), dados.get('areaOperacional'))
    v_area_geo = _obter_label(refs.get('areas_geo', {}), dados.get('areaGeografica'))
    v_grupamento = _obter_label(refs.get('grupamentos', {}), dados.get('grupamentoBRS'))
    v_parametro = _obter_label(refs.get('parametros', {}), dados.get('parametro'))
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
    
    def _gerar_linhas_itinerario(tipo):
        ida = [it for it in it_lista if it.get("tipo") == tipo and str(it.get("sentido")) == "0"]
        volta = [it for it in it_lista if it.get("tipo") == tipo and str(it.get("sentido")) == "1"]
        
        ida = sorted(ida, key=lambda x: x.get("ordem", 0))
        volta = sorted(volta, key=lambda x: x.get("ordem", 0))
        
        max_rows = max(len(ida), len(volta))
        rows_html = ""
        
        if max_rows == 0:
            return "<tr><td colspan='6' style='text-align:center; color:#888;'>Nenhum ponto registrado</td></tr>"
            
        for i in range(max_rows):
            p_ida = ida[i] if i < len(ida) else {}
            p_volta = volta[i] if i < len(volta) else {}
            
            rows_html += f"<tr><td>{p_ida.get('logradouro', '')}</td><td>{p_ida.get('observacao', '')}</td><td>{p_ida.get('bairro', '')}</td><td style='border-left: 2px solid #000;'>{p_volta.get('logradouro', '')}</td><td>{p_volta.get('observacao', '')}</td><td>{p_volta.get('bairro', '')}</td></tr>"
        return rows_html

    v_html_reg = _gerar_linhas_itinerario("R")
    v_html_alt = _gerar_linhas_itinerario("A")

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

    col_back, col_print, _ = st.columns([1.5, 2.5, 6])
    with col_back:
        if st.button("⬅️ Voltar", width='stretch'):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()
    with col_print:
        components.html("""
        <button onclick="document.getElementById('ficha-frame').contentWindow.print()" style="background-color: #1a3a5c; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-family: sans-serif; font-weight: 600; font-size: 14px; width: 100%; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            🖨️ Imprimir
        </button>
        """, height=45)
            
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
    .itinerario-table {{ width: calc(100% - 40px); margin: 0 20px 15px 20px; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 11px; }}
    .itinerario-table th, .itinerario-table td {{ border: 1px solid #000; padding: 4px 6px; vertical-align: top; }}
    .itinerario-table th {{ background: #f5f5f5; font-weight: bold; text-align: center; }}
    @media print {{
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
            <div class="title">
                <h1>Rede Integrada de Ônibus</h1>
                <p>Cadastro e Consulta</p>
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
                <th>Tipo de linha:</th><td>{v_tipo}</td>
                <th>Classificação espacial:</th><td>{v_class}</td>
            </tr>
            <tr>
                <th>Área Operacional:</th><td>{v_area_op}</td>
                <th>Área Geográfica:</th><td>{v_area_geo}</td>
            </tr>
            <tr>
                <th>Grupamento BRS:</th><td>{v_grupamento}</td>
                <th>Parâmetro Funcional:</th><td>{v_parametro}</td>
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
            <tr>
                <th>Ofício Principal:</th><td colspan="3">{v_oficio_prin}</td>
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
        
        <div class="section-title">Itinerário Regular</div>
        <table class="itinerario-table">
            <tr>
                <th colspan="3">Itinerário de Ida</th>
                <th colspan="3" style="border-left: 2px solid #000;">Itinerário de Volta</th>
            </tr>
            <tr>
                <th style="width: 20%;">Logradouro</th>
                <th style="width: 15%;">Complemento</th>
                <th style="width: 15%;">Bairro</th>
                <th style="width: 20%; border-left: 2px solid #000;">Logradouro</th>
                <th style="width: 15%;">Complemento</th>
                <th style="width: 15%;">Bairro</th>
            </tr>
            {v_html_reg}
        </table>
        
        <div class="section-title">Itinerário Alternativo</div>
        <table class="itinerario-table">
            <tr>
                <th colspan="3">Itinerário de Ida</th>
                <th colspan="3" style="border-left: 2px solid #000;">Itinerário de Volta</th>
            </tr>
            <tr>
                <th style="width: 20%;">Logradouro</th>
                <th style="width: 15%;">Complemento</th>
                <th style="width: 15%;">Bairro</th>
                <th style="width: 20%; border-left: 2px solid #000;">Logradouro</th>
                <th style="width: 15%;">Complemento</th>
                <th style="width: 15%;">Bairro</th>
            </tr>
            {v_html_alt}
        </table>
    </div>
    </body>
    </html>
    """

    import urllib.parse
    encoded_html = urllib.parse.quote(html_doc)
    iframe_html = f'<iframe id="ficha-frame" src="data:text/html;charset=utf-8,{encoded_html}" style="width:100%;height:900px;border:none;"></iframe>'
    st.markdown(iframe_html, unsafe_allow_html=True)
