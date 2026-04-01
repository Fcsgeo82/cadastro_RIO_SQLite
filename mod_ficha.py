import streamlit as st
import textwrap
import re   # Add regex import here
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

    # --- Container Controle ---
    col_back, col_print, _ = st.columns([1.5, 2.5, 6])
    with col_back:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.session_state["aba_ativa"] = "Principal"
            st.rerun()
    with col_print:
        import streamlit.components.v1 as components
        components.html("""
        <button onclick="window.parent.print()" style="background-color: #1a3a5c; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-family: sans-serif; font-weight: 600; font-size: 14px; width: 100%; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            🖨️ Imprimir (A4)
        </button>
        """, height=40)
            
    st.markdown("<br>", unsafe_allow_html=True)

    # Parametrização dos Campos (Formatação e Checagem contra Nulos)
    v_linha = dados.get('numeroLinha', '-')
    v_servico = _obter_label(refs.get('servicos', {}), dados.get('servico'))
    v_vista = dados.get('vista', '-')
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

    # Tratamento customizado de Ofícios para incluir o Assunto em Nova Linha dentro da Célula HTML
    def _of_html(of_id):
        if not of_id: return "-"
        lbl = _obter_label(refs.get('oficios', {}), of_id)
        ass = refs.get('assuntos_oficios', {}).get(of_id, '')
        if ass and ass != "Sem assunto":
             # Adiciona assunto num tamanho diminuto e sem negrito
             return f"{lbl}<br><span style='font-size:10.5px; font-weight:normal; color:#555;'>Assunto: {ass}</span>"
        return lbl

    # Tratamento inline sem "Assunto" para as headers ao lado do bloco
    def _of_raw_lbl(of_id):
        if not of_id: return "-"
        return _obter_label(refs.get('oficios', {}), of_id)


    v_oficio_prin = _of_html(dados.get('oficio'))
    v_oficio_prim = _of_html(dados.get('oficioprimeiroHistorico'))
    v_oficio_ult  = _of_html(dados.get('oficioUltimaAlteracao'))
    
    # Frota
    v_frota_of_html = _of_html(dados.get('frotaUltimoOficio'))
    v_frota_of_raw  = _of_raw_lbl(dados.get('frotaUltimoOficio'))
    v_frota_tipo = _obter_label(refs.get('tipos_veiculo', {}), dados.get('frotaTipoVeiculo'))
    if dados.get('frotaDataOficio'):
        v_frota_data = str(dados.get('frotaDataOficio'))
        if "-" in v_frota_data and len(v_frota_data) == 10: 
            v_frota_data = v_frota_data[8:10] + "/" + v_frota_data[5:7] + "/" + v_frota_data[0:4]
    else: v_frota_data = '-'

    # Itinerários
    v_itida_of_raw = _of_raw_lbl(dados.get('itinerarioIdaOficio'))
    v_itida_it = dados.get('itinerarioIDA') or '-'
    
    v_itvolta_of_raw = _of_raw_lbl(dados.get('itinerarioVoltaOficio'))
    v_itvolta_it = dados.get('itinerarioVOLTA') or '-'

    # ================== HTML GENERATOR ==============================
    html_content = textwrap.dedent(f"""
    <style>
    .ficha-container {{
        background-color: white;
        padding: 40px;
        border: 1px solid #ccc;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        max-width: 900px;
        margin: 0 auto;
        color: black;
    }}
    .ficha-header-logo {{
        font-family: Arial, sans-serif;
        font-size: 26px;
        font-weight: 900;
        color: #0b3c68;
        border-right: 2px solid #0b3c68;
        padding-right: 15px;
        margin-right: 15px;
        display: inline-block;
        letter-spacing: -0.5px;
    }}
    .ficha-header-text {{
        font-family: Arial, sans-serif;
        font-size: 16px;
        color: #0b3c68;
        display: inline-block;
        font-weight: 500;
    }}
    .ficha-main-title {{
        font-family: Arial, sans-serif;
        font-weight: bold;
        font-size: 15px;
        margin: 35px 0 20px 0;
        color: #000;
        text-transform: uppercase;
    }}
    .ficha-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 25px;
        font-family: Arial, sans-serif;
        font-size: 13px;
        color: #000;
    }}
    .ficha-table th, .ficha-table td {{
        border: 1px solid #000;
        padding: 6px 8px;
        vertical-align: top;
        line-height: 1.3;
    }}
    .ficha-table th {{
        text-align: right;
        font-weight: bold;
        width: 20%;
    }}
    .ficha-table td {{
        text-align: left;
        width: 30%;
    }}
    .ficha-title {{
        font-size: 14px;
        font-weight: bold;
        margin: 0 0 5px 0;
        font-family: Arial, sans-serif;
        color: #000;
    }}
    .ficha-flex-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        font-family: Arial, sans-serif;
        font-size: 14px;
        font-weight: bold;
        margin: 0 0 5px 0;
        color: #000;
    }}
    @media print {{
        @page {{
            size: A4;
            margin: 15mm;
        }}
        body {{
            background: white !important;
        }}
        header[data-testid="stHeader"], div[data-testid="stSidebar"], div[data-testid="stToolbar"], div[data-testid="stDecoration"], .stButton, iframe {{
            display: none !important;
        }}
        .stApp {{
            overflow: visible !important;
        }}
        div[data-testid="stVerticalBlock"] {{
            gap: 0 !important;
        }}
        .ficha-container {{
            box-shadow: none !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
        }}
    }}
    </style>

    <div class="ficha-container">
        <!-- HEADER -->
        <div style="margin-bottom: 10px;">
            <span class="ficha-header-logo">PREFEITURA RIO</span>
            <span class="ficha-header-text">Transportes</span>
        </div>
        
        <div class="ficha-main-title">FICHA CADASTRAL</div>
        
        <!-- SEC 1 -->
        <div class="ficha-title">Dados Cadastrais</div>
        <table class="ficha-table">
            <tr>
                <th>Linha:</th><td>{v_linha}</td>
                <th>Serviço:</th><td>{v_servico}</td>
            </tr>
            <tr>
                <th>Vista:</th><td colspan="3">{v_vista}</td>
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
        
        <!-- SEC 2 -->
        <div class="ficha-title">Dados processuais</div>
        <table class="ficha-table">
            <tr>
                <th>Ofício de criação:</th><td>{v_oficio_prim}</td>
                <th>Ofício de última alteração:</th><td>{v_oficio_ult}</td>
            </tr>
            <tr>
                <th>Ofício Principal:</th><td colspan="3">{v_oficio_prin}</td>
            </tr>
        </table>
        
        <!-- SEC 3 -->
        <div class="ficha-flex-header">
           <span>Frota autorizada</span>
           <span style="font-size:13px; font-weight:normal">Ofício de autorização: <b>{v_frota_of_raw}</b></span>
        </div>
        <table class="ficha-table">
            <tr>
                <th style="width: 15%">Tipo:</th>
                <td>{v_frota_tipo}</td>
                <th style="width: 20%">Data do Ofício:</th>
                <td>{v_frota_data}</td>
            </tr>
        </table>
        
        <!-- SEC 4 -->
        <div class="ficha-flex-header">
           <span>Itinerário de ida</span>
           <span style="font-size:13px; font-weight:normal">Ofício de última alteração: <b>{v_itida_of_raw}</b></span>
        </div>
        <table class="ficha-table">
            <tr>
                <th style="width: 15%">Tipo:</th><td colspan="3">{v_tipo}</td>
            </tr>
            <tr>
                <th style="width: 15%">Itinerário:</th><td colspan="3" style="text-align:justify">{v_itida_it}</td>
            </tr>
        </table>
        
        <!-- SEC 5 -->
        <div class="ficha-flex-header">
           <span>Itinerário de volta</span>
           <span style="font-size:13px; font-weight:normal">Ofício de última alteração: <b>{v_itvolta_of_raw}</b></span>
        </div>
        <table class="ficha-table">
            <tr>
                <th style="width: 15%">Tipo:</th><td colspan="3">{v_tipo}</td>
            </tr>
            <tr>
                <th style="width: 15%">Itinerário:</th><td colspan="3" style="text-align:justify">{v_itvolta_it}</td>
            </tr>
        </table>
    </div>
    """)

    # Remove qualquer indentação para impedir que o Streamlit Markdown o renderize como bloco de código (<pre><code>)
    html_content = re.sub(r'\n\s+', '\n', html_content)

    st.markdown(html_content, unsafe_allow_html=True)
