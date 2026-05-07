import streamlit as st
import os
import base64

@st.cache_data(show_spinner=False)
def get_logo_b64():
    """Lê e encoda o logo em base64 com cache."""
    # Procura no diretório raiz do projeto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_svg = os.path.join(base_dir, "logo_rio.svg")
    logo_png = os.path.join(base_dir, "logo_rio.png")
    
    if os.path.exists(logo_svg):
        with open(logo_svg, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f'data:image/svg+xml;base64,{data}'
    elif os.path.exists(logo_png):
        with open(logo_png, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f'data:image/png;base64,{data}'
    return ""

def render_logo(width="230px"):
    """Retorna o HTML do logo."""
    logo_b64 = get_logo_b64()
    if logo_b64:
        return f'<img src="{logo_b64}" style="width:{width};height:auto;display:block;margin:0 auto;">'
    return ""

def obter_label(dicionario_inverso, chave_busca):
    """Retorna o label correspondente ao ID em um dicionário de referências."""
    if not chave_busca:
        return "-"
    
    # Se for uma lista separada por vírgula (múltiplas seleções)
    if isinstance(chave_busca, str) and "," in chave_busca:
        ids = [i.strip() for i in chave_busca.split(",")]
        labels = []
        for i in ids:
            label_encontrado = None
            for label, id_ in dicionario_inverso.items():
                if str(id_) == str(i):
                    label_encontrado = label
                    break
            labels.append(label_encontrado if label_encontrado else i)
        return ", ".join(labels)

    for label, id_ in dicionario_inverso.items():
        if str(id_) == str(chave_busca):
            return label
    return str(chave_busca)
