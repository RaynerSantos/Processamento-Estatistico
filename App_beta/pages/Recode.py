import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import criar_bandeira, to_excel, recode_variavel

st.set_page_config(layout='wide', page_title='Processamento de dados', page_icon='📊')

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.")
    st.stop()

st.title('Pré-Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode realizar recodes simples em suas variáveis existentes.')
st.write('')

colunas = st.session_state.data.columns.tolist()
selected_column = st.selectbox('Selecione a coluna que será recodificada:', colunas, key="recode_selected_column")

if selected_column:

    nome_bandeira_recode = st.text_input(label="📝 Insira o nome da nova bandeira recodificada", placeholder="nome da nova bandeira recodificada", key="recode_nome_bandeira")

    if nome_bandeira_recode in st.session_state.data.columns:
        st.error(f"❌ A coluna '{nome_bandeira_recode}' já existe no DataFrame. Por favor, escolha outro nome.")
    else:
        dataframe_recode = st.session_state.lista_labels[st.session_state.lista_labels['Coluna'] == selected_column][['Codigo', 'Label']].copy()
        dataframe_recode = dataframe_recode.rename(columns={'Codigo': 'Codigo', 'Label': 'Label'})
        dataframe_recode['Codigo_novo'] = None
        dataframe_recode['Label_novo'] = None

        dataframe_recode_edited = st.data_editor(dataframe_recode, num_rows="dynamic", 
                                                 use_container_width=True, 
                                                 key="dataframe_recode_editor", 
                                                 hide_index=True)
        

        if st.button('Realizar recode', key="btn_recode") and nome_bandeira_recode:
            # st.dataframe(dataframe_recode_edited, hide_index=True)

            data, lista_labels = recode_variavel(
                data=st.session_state.data,
                lista_labels=st.session_state.lista_labels,
                COLUNA_ORIGINAL=selected_column,
                NOVA_BANDEIRA=nome_bandeira_recode,
                dataframe_recode=dataframe_recode_edited
            )
            st.session_state.data = data
            st.session_state.lista_labels = lista_labels
            st.session_state.ultima_bandeira = nome_bandeira_recode
            st.success('✅ Recode realizado com sucesso!')

            # Exibir a frequência da nova bandeira criada
            ultima = st.session_state.ultima_bandeira
            st.write(f'Frequência da nova bandeira: {ultima}')

            freq = st.session_state.data[ultima].value_counts(dropna=False).rename("Frequência").to_frame()
            freq["%"] = (freq["Frequência"] / freq["Frequência"].sum() * 100).round(2)
            total_line = round(pd.DataFrame(freq.sum()).T)
            total_line.index = ['Total']
            freq = pd.concat([freq, total_line], ignore_index=False)
            freq["Código"] = freq.index
            st.dataframe(freq[["Código", "Frequência", "%"]], hide_index=True)




# if selected_column:
#     st.success("✅ Coluna selecionada com sucesso!")

#     nome_bandeira_recode = st.text_input(label="📝 Insira o nome da nova bandeira recodificada", placeholder="nome da nova bandeira recodificada", key="recode_nome_bandeira")

#     if nome_bandeira_recode in st.session_state.data.columns:
#         st.error(f"❌ A coluna '{nome_bandeira_recode}' já existe no DataFrame. Por favor, escolha outro nome.")
#     else:
#         uploaded_file = st.file_uploader("📂 Faça o upload do arquivo Excel contendo o mapeamento de recode", type=["xlsx"], key="recode_file_uploader")

#         if uploaded_file is not None:
#             dataframe_recode = pd.read_excel(uploaded_file)
#             st.write("Preview do mapeamento de recode:")
#             st.dataframe(dataframe_recode, hide_index=True)

#             if st.button('Realizar recode', key="btn_recode") and nome_bandeira_recode:
#                 data, lista_labels = recode_variavel(
#                     st.session_state.data,
#                     st.session_state.lista_labels,
#                     selected_column,
#                     nome_bandeira_recode,
#                     dataframe_recode
#                 )
#                 st.session_state.data = data
#                 st.session_state.lista_labels = lista_labels
#                 st.session_state.ultima_bandeira = nome_bandeira_recode
#                 st.success('✅ Recode realizado com sucesso!')

#                 # Exibir a frequência da nova bandeira criada
#                 ultima = st.session_state.ultima_bandeira
#                 st.write(f'Frequência da nova bandeira: {ultima}')