import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import criar_pond

st.set_page_config(layout='wide', page_title='Processamento de dados', 
                   page_icon='images/Logo_Expertise.png')

st.logo(image="images/ExpertiseAI.svg", size="large")

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.")
    st.stop()

st.title('Pré-Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode criar a coluna de Ponderação')
st.write('')

coluna1, coluna2 = st.columns(2)

with st.form('sheet_name_df_universo_df_coletado'):
    with coluna1:
        nome_sheet_df_universo = st.text_input(label="📝 Informe o nome da aba (sheet) que contém a tabela com a **quantidade real do universo do projeto**.", 
                                        placeholder="FONTE",
                                        help="A tabela deverá conter três categorias (Cabeçalho, coluna, linha).")
    with coluna2:
        nome_sheet_df_coletado = st.text_input(label="📝 Informe o nome da aba (sheet) que contém a tabela com a **quantidade coletada do projeto**.", 
                                                placeholder="COLETADO",
                                                help="A tabela deverá conter três categorias (Cabeçalho, coluna, linha).")

    with st.status("📅 A seguir, veja uma imagem de exemplo da tabela:"):
        st.image(image="images/Tabela fonte universo.png", width="content")
    input_buttom_submit_DATA = st.form_submit_button("Enviar")
        
if input_buttom_submit_DATA:
    st.success("Nome das abas (sheets) da planilha enviado com sucesso", icon="✅")
st.write('')
data_file_pond = st.file_uploader("📂 Selecione o banco de dados (em xlsx)", 
                             type=["xlsx"], 
                             help="Selecione o arquivo Excel contendo as tabelas **quantidade real do universo do projeto** e **quantidade coletada do projeto**.", 
                             key="ponderacao_uploader")

if data_file_pond is not None:
    df_universo = pd.read_excel(data_file_pond, sheet_name=nome_sheet_df_universo, header=[0, 1])
    df_universo.index = df_universo.iloc[:, 0]
    df_universo = df_universo.iloc[:, 1:].copy()

    df_coletado = pd.read_excel(data_file_pond, sheet_name=nome_sheet_df_coletado, header=[0, 1])
    df_coletado.index = df_coletado.iloc[:, 0]
    df_coletado = df_coletado.iloc[:, 1:].copy()

    st.session_state.df_universo = df_universo
    st.session_state.df_coletado = df_coletado
    
    st.success("Planilha carregada com sucesso!", icon="✅")

st.write('')
st.write('')
st.write('')
colunas = st.session_state.data.columns.tolist()
coluna1, coluna2, coluna3 = st.columns(3)
with st.form('cabecalho_multiindex'):
    with coluna1:
        selected_column_cabecalho = st.selectbox('👇 Selecione a coluna que representa o nível do cabeçalho da tabela:', 
                                        colunas, 
                                        key="ponderacao_selected_column_cabecalho",
                                        help="A imagem com o exemplo acima seria a coluna do banco de dados que representa as **empresas**.")
    with coluna2:
        selected_column_coluna = st.selectbox('👇 Selecione a coluna que representa o nível das colunas da tabela:', 
                                        colunas, 
                                        key="ponderacao_selected_column_coluna",
                                        help="A imagem com o exemplo acima seria a coluna do banco de dados que representa as **regiões**.")
    with coluna3:
        selected_column_linha = st.selectbox('👇 Selecione a coluna que representa o nível das linhas da tabela:', 
                                        colunas, 
                                        key="ponderacao_selected_column_linha",
                                        help="A imagem com o exemplo acima seria a coluna do banco de dados que representa o **porte empresarial**.")
        
    input_buttom_submit_cabecalho_multiindex = st.form_submit_button("Enviar e gerar coluna de ponderação")
if input_buttom_submit_cabecalho_multiindex:
    st.success("Nome das colunas enviado com sucesso", icon="✅")

    st.session_state.data = criar_pond(df_universo=df_universo, df_coletado=df_coletado, bd_codigo=st.session_state.data,
                                       lista_labels=st.session_state.lista_labels, cabecalho=selected_column_cabecalho,
                                       coluna=selected_column_coluna, linha=selected_column_linha)
    
    st.write("")
    st.dataframe(st.session_state.data[["codigo_entrevistado", selected_column_cabecalho, 
                                        selected_column_coluna, selected_column_linha, "POND", "POND_nova"]], 
                                        hide_index=True, 
                                        selection_mode=["multi-row", "multi-cell"])
    
st.write("")
st.write("")
st.write("")
st.divider()
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg")






