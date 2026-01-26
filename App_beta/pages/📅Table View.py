import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import criar_bandeira, to_excel, mensagem_sucesso

st.set_page_config(layout='wide', page_title='Processamento de dados', 
                   page_icon='images/LOGO_Expertise_Marca_VerdeEscuro.jpg')

st.logo(image="images/Expertise_Marca_OffWhite_mini.jpg", size="large")

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.")
    st.stop()

st.title('Pré-Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode visualizar a frequência da coluna desejada')
st.write('')

colunas = st.session_state.data.columns.tolist()
selected_column = st.selectbox('Selecione a coluna que deseja visualizar a tabela de frequência:', 
                                  colunas, 
                                  key="table_view_selected_column")

if st.button('Visualizar frequência', key="btn_table_view") and selected_column:
    freq = st.session_state.data[selected_column].value_counts(dropna=False).rename("Frequência").to_frame()
    freq["%"] = ( freq["Frequência"] / freq["Frequência"].sum() ).round(4)
    total_line = round(pd.DataFrame(freq.sum()).T)
    total_line.index = ['Total']
    freq = pd.concat([freq, total_line], ignore_index=False)
    freq["Código"] = freq.index

    dict_codigo_label = st.session_state.lista_labels.loc[st.session_state.lista_labels["Coluna"]==selected_column].set_index("Codigo")["Label"]
    freq["Código"] = freq.index
    freq["Label"] = freq["Código"].map(dict_codigo_label)
    freq.loc["Total", "Label"] = "Total"

    st.dataframe(freq[["Código", "Label", "Frequência", "%"]], hide_index=True, 
                column_config={"%": st.column_config.NumberColumn("%", format="percent")})
    
st.write("")
st.write("")
st.write("")
st.divider()
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg")