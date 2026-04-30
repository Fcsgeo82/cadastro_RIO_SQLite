import streamlit as st
import os
import shutil
from models.gtfs_loader import GTFS_DIR, get_latest_gtfs_path

def render():
    st.markdown("### 📁 Gerenciar Arquivos GTFS")
    st.markdown("Faça o upload do arquivo GTFS (formato `.zip`) para atualizar os itinerários e quadros horários do sistema.")

    if not os.path.exists(GTFS_DIR):
        os.makedirs(GTFS_DIR)

    # 1. Upload de Arquivo
    with st.expander("⬆️ Upload de Novo GTFS", expanded=True):
        uploaded_file = st.file_uploader("Selecione o arquivo .zip do GTFS", type=["zip"])
        
        if uploaded_file is not None:
            file_path = os.path.join(GTFS_DIR, uploaded_file.name)
            
            # Verificar se já existe
            if os.path.exists(file_path):
                st.warning(f"O arquivo `{uploaded_file.name}` já existe na pasta. Ele será sobrescrito.")
            
            if st.button("💾 Salvar Arquivo GTFS", type="primary"):
                try:
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.success(f"✅ Arquivo `{uploaded_file.name}` salvo com sucesso!")
                    st.cache_data.clear() # Limpar cache para forçar recarregamento do GTFS
                except Exception as e:
                    st.error(f"Erro ao salvar arquivo: {e}")

    st.divider()

    # 2. Listagem de Arquivos Existentes
    st.markdown("#### 📂 Arquivos na Pasta `data/gtfs`:")
    
    files = [f for f in os.listdir(GTFS_DIR) if f.endswith(".zip")]
    if not files:
        st.info("Nenhum arquivo GTFS encontrado na pasta.")
    else:
        latest = get_latest_gtfs_path()
        latest_name = os.path.basename(latest) if latest else ""

        for f in sorted(files, reverse=True):
            col_icon, col_name, col_status, col_action = st.columns([0.5, 4, 2, 2])
            
            with col_icon:
                st.write("📦")
            
            with col_name:
                st.write(f"**{f}**")
            
            with col_status:
                if f == latest_name:
                    st.markdown(":green[**[Ativo]**]")
                else:
                    st.caption("Inativo (Antigo)")
            
            with col_action:
                if st.button("🗑️", key=f"del_{f}"):
                    try:
                        os.remove(os.path.join(GTFS_DIR, f))
                        st.success(f"Removido: {f}")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    st.info("💡 O sistema utiliza automaticamente o arquivo com a data de modificação mais recente como fonte oficial.")
