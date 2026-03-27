import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from metodos import to_excel, mensagem_sucesso


st.set_page_config(layout='wide', page_title='Processamento de Dados', 
                   page_icon='images/Logo_Expertise.png')

st.logo(image="images/ExpertiseAI.svg", size="large") # Expertise_Marca_OffWhite_mini.jpg

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.", icon="⚠️")
    st.stop()


st.title('Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode fazer o download de seu Banco de Dados atualizado')
st.write('')

with st.spinner("Please wait..."):
    if "data" in st.session_state and "lista_labels" in st.session_state and "lista_variaveis" in st.session_state:
        st.write('')
        # with st.expander("📅 Dicionário de variáveis:"):
        #     st.dataframe(
        #         st.session_state.lista_variaveis, 
        #         hide_index=True, 
        #         selection_mode=["multi-row", "multi-cell"], 
        #         width='stretch'
        #         )
        # with st.expander("📋 Colunas"):
        #     # default_cols = [c for c in st.session_state.data.columns if c != 'POND']
        #     colunas = st.multiselect('Selecione as colunas que deseja visualizar:', 
        #                             st.session_state.data.columns.tolist(), 
        #                             default=st.session_state.data.columns.tolist(),
        #                             key="home_colunas")
        # dados_filtrados = st.session_state.data[colunas]
        # st.dataframe(dados_filtrados, hide_index=True, selection_mode=["multi-row", "multi-cell"], width='stretch')

        excel_data = to_excel(st.session_state.data, st.session_state.lista_labels, st.session_state.lista_variaveis)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.download_button(
            label="📥 Baixar arquivo Excel",
            data=excel_data,
            file_name=f'Base de dados atualizada - {now}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            on_click=mensagem_sucesso
        )


st.write('')
st.divider()
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg") # Expertise_Marca_VerdeEscuro_mini.jpg