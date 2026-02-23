import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import Criar_Pond

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


c1, c2, c3 = st.columns(3, vertical_alignment="bottom")

with st.form('sheet_name_DFuniverso_DFcoletado'):
    with c1:
        with st.container(border=True):
            nome_sheet_df_universo = st.text_input(
                label="📝 Digite o nome da aba (sheet) que contém a tabela com a **quantidade real do universo do projeto**.", 
                value="FONTE",
                help="A tabela deverá conter duas categorias (Coluna, Linha).",
                key="pond_nome_sheet_df_universo"
                )
    with c2:
        with st.container(border=True):
            nome_sheet_df_coletado = st.text_input(
                label="📝 Digite o nome da aba (sheet) que contém a tabela com a **quantidade coletada do projeto**.", 
                value="COLETADO",
                help="A tabela deverá conter duas categorias (Coluna, Linha).",
                key="pond_nome_sheet_df_coletado"
                )
    with c3:
        with st.container(border=True):
            qtd_dimensao = st.number_input(
                label="📝 Digite a quantidade de **dimensões** da sua tabela, ou seja, quantas variáveis serão combinadas para criar a ponderação.",
                value=3,
                min_value=2,
                max_value=4,
                key="pond_qtd_dimensao",
                # help="Informe a quantidade de **dimensões** da sua tabela, ou seja, quantas variáveis serão combinadas para criar a ponderação."
            )

    with st.status("🔍 A seguir, veja uma imagem de exemplo da tabela:"):
        st.image(image="images/Tabela fonte universo_4dim.png")
    input_buttom_submit_DATA = st.form_submit_button("Enviar")

if input_buttom_submit_DATA:
    st.session_state.nome_sheet_df_universo = nome_sheet_df_universo
    st.session_state.nome_sheet_df_coletado = nome_sheet_df_coletado
    st.session_state.qtd_dimensao = qtd_dimensao

    if not st.session_state.nome_sheet_df_universo or not st.session_state.nome_sheet_df_coletado:
        st.error("Preencha os dois nomes de abas antes de continuar.", icon="❌")
    else:
        st.success("Nome das abas (sheets) enviado com sucesso", icon="✅")

st.write('')
data_file_pond = st.file_uploader(
    "📂 Selecione o banco de dados (em xlsx)", 
    type=["xlsx"], 
    help="Selecione o arquivo Excel contendo as tabelas **quantidade real do universo do projeto** e **quantidade coletada do projeto**.", 
    key="ponderacao_uploader"
    )

if data_file_pond is not None:
    # Lista as abas disponíveis (ajuda muito a evitar erro)
    xls = pd.ExcelFile(data_file_pond)
    st.caption(f"Abas encontradas no arquivo: {',  '.join(xls.sheet_names)}")

    sheet_univ = st.session_state.get("nome_sheet_df_universo", "")
    sheet_col = st.session_state.get("nome_sheet_df_coletado", "")

    # Validações antes de ler
    if not sheet_univ or not sheet_col:
        st.warning("Envie (submit) os nomes das abas acima antes de carregar as tabelas.", icon="⚠️")
        st.stop()

    if sheet_univ not in xls.sheet_names:
        st.error(f"A aba do universo '{sheet_univ}' não existe no arquivo.", icon="❌")
        st.stop()

    if sheet_col not in xls.sheet_names:
        st.error(f"A aba do coletado '{sheet_col}' não existe no arquivo.", icon="❌")
        st.stop()

    if st.session_state.qtd_dimensao == 2:
        df_universo = pd.read_excel(
            data_file_pond, 
            sheet_name=nome_sheet_df_universo,
            index_col=0
            )
        df_coletado = pd.read_excel(
            data_file_pond, 
            sheet_name=nome_sheet_df_coletado,
            index_col=0
            )
        
    elif st.session_state.qtd_dimensao == 3:
        df_universo = pd.read_excel(
            data_file_pond, 
            sheet_name=nome_sheet_df_universo,
            header=[0, 1],
            index_col=0 
            )
        df_coletado = pd.read_excel(
            data_file_pond, 
            sheet_name=nome_sheet_df_coletado,
            header=[0, 1],
            index_col=0 
            )
    
    elif st.session_state.qtd_dimensao == 4:
        df_universo = pd.read_excel(
            data_file_pond, 
            sheet_name=nome_sheet_df_universo,
            header=[0, 1, 2],
            index_col=0 
            )
        df_coletado = pd.read_excel(
            data_file_pond, 
            sheet_name=nome_sheet_df_coletado,
            header=[0, 1, 2],
            index_col=0 
            )

    st.session_state.df_universo = df_universo
    st.session_state.df_coletado = df_coletado
    
    st.success("Planilha carregada com sucesso!", icon="✅")

    st.write('')
    st.write('')
    st.write('')

    Criar_ponderacao = Criar_Pond(
        df_universo=st.session_state.df_universo, 
        df_coletado=st.session_state.df_coletado, 
        bd_codigo=st.session_state.data, 
        lista_labels=st.session_state.lista_labels
        )
    Criar_ponderacao.n_niveis_colunas()
    result = Criar_ponderacao.verificar_cols_multiindex()
    if isinstance(result, str):
        st.write(result)
    else:
        st.session_state.data, lista_de_colunas_indice = Criar_ponderacao.criar_pond()

        st.write("")
        with st.expander("📋 Colunas"):
            # default_cols = st.session_state.data.columns.tolist()
            colunas = st.multiselect('Selecione as colunas que deseja visualizar:', 
                                        st.session_state.data.columns.tolist(), 
                                        default=lista_de_colunas_indice + ["POND", "POND_nova"],
                                        key="pond_colunas")
        dados_filtrados = st.session_state.data[colunas]
        st.dataframe(dados_filtrados, hide_index=True, selection_mode=["multi-row", "multi-cell"], use_container_width=True)


    
st.write("")
st.write("")
st.write("")
st.divider()
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg")






