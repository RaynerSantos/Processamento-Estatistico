import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import criar_pond_3dim, criar_pond_2dim, criar_pond_4dim

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

tab1, tab2, tab3 = st.tabs(["2 dimensões", "3 dimensões", "4 dimensões"])

with tab1:
    coluna1, coluna2 = st.columns(2, border=True)

    with st.form('sheet_name_DFuniverso_DFcoletado_2dim'):
        with coluna1:
            nome_sheet_df_universo_2dim = st.text_input(label="📝 Informe o nome da aba (sheet) que contém a tabela com a **quantidade real do universo do projeto**.", 
                                            value="FONTE",
                                            help="A tabela deverá conter duas categorias (Coluna, Linha).",
                                            key="nome_sheet_df_universo_2dim_input")
        with coluna2:
            nome_sheet_df_coletado_2dim = st.text_input(label="📝 Informe o nome da aba (sheet) que contém a tabela com a **quantidade coletada do projeto**.", 
                                                    value="COLETADO",
                                                    help="A tabela deverá conter duas categorias (Coluna, Linha).",
                                                    key="nome_sheet_df_coletado_2dim_input")

        with st.status("🔍 A seguir, veja uma imagem de exemplo da tabela:"):
            st.image(image="images/Tabela fonte universo_2dim.png", width="content")
        input_buttom_submit_DATA_2dim = st.form_submit_button("Enviar")

    if input_buttom_submit_DATA_2dim:
        st.session_state.nome_sheet_df_universo_2dim = nome_sheet_df_universo_2dim
        st.session_state.nome_sheet_df_coletado_2dim = nome_sheet_df_coletado_2dim

        if not st.session_state.nome_sheet_df_universo_2dim or not st.session_state.nome_sheet_df_coletado_2dim:
            st.error("Preencha os dois nomes de abas antes de continuar.", icon="❌")
        else:
            st.success("Nome das abas (sheets) enviado com sucesso", icon="✅")

    st.write('')
    data_file_pond = st.file_uploader("📂 Selecione o banco de dados (em xlsx)", 
                                type=["xlsx"], 
                                help="Selecione o arquivo Excel contendo as tabelas **quantidade real do universo do projeto** e **quantidade coletada do projeto**.", 
                                key="ponderacao_uploader_2dim")

    if data_file_pond is not None:
        # Lista as abas disponíveis (ajuda muito a evitar erro)
        xls = pd.ExcelFile(data_file_pond)
        st.caption(f"Abas encontradas no arquivo: {', '.join(xls.sheet_names)}")

        sheet_univ = st.session_state.get("nome_sheet_df_universo_2dim", "")
        sheet_col = st.session_state.get("nome_sheet_df_coletado_2dim", "")

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

        df_universo = pd.read_excel(data_file_pond, sheet_name=nome_sheet_df_universo_2dim)
        df_universo.index = df_universo.iloc[:, 0]
        df_universo = df_universo.iloc[:, 1:].copy()

        df_coletado = pd.read_excel(data_file_pond, sheet_name=nome_sheet_df_coletado_2dim)
        df_coletado.index = df_coletado.iloc[:, 0]
        df_coletado = df_coletado.iloc[:, 1:].copy()

        st.session_state.df_universo = df_universo
        st.session_state.df_coletado = df_coletado
        
        st.success("Planilha carregada com sucesso!", icon="✅")

    st.write('')
    st.write('')
    st.write('')
    colunas = st.session_state.data.columns.tolist()
    coluna1, coluna2= st.columns(2)
    with st.form('cabecalho_2dim'):
        with coluna1:
            selected_column_coluna = st.selectbox('👇 Selecione a coluna que representa o **nível das colunas** da tabela:', 
                                            colunas, 
                                            key="ponderacao_selected_column_coluna_2dim",
                                            help="A imagem com o exemplo acima seria a coluna do banco de dados que representa o **segmento empresarial**.")
        with coluna2:
            selected_column_linha = st.selectbox('👇 Selecione a coluna que representa o **nível das linhas** da tabela:', 
                                            colunas, 
                                            key="ponderacao_selected_column_linha_2dim",
                                            help="A imagem com o exemplo acima seria a coluna do banco de dados que representa as **regiões**.")
            
        input_buttom_submit_cabecalho_2dim = st.form_submit_button("Enviar e gerar coluna de ponderação")
    if input_buttom_submit_cabecalho_2dim:
        st.success("Nome das colunas enviado com sucesso", icon="✅")

        st.session_state.data = criar_pond_2dim(df_universo=df_universo, df_coletado=df_coletado, bd_codigo=st.session_state.data,
                                                lista_labels=st.session_state.lista_labels,
                                                coluna=selected_column_coluna, linha=selected_column_linha)
        
        st.write("")
        st.dataframe(st.session_state.data[[selected_column_coluna, selected_column_linha, "POND", "POND_nova"]], 
                                            hide_index=True, 
                                            selection_mode=["multi-row", "multi-cell"])





with tab2:
    coluna1, coluna2 = st.columns(2, border=True)

    with st.form('sheet_name_DFuniverso_DFcoletado_3dim'):
        with coluna1:
            nome_sheet_df_universo_3dim = st.text_input(label="📝 Informe o nome da aba (sheet) que contém a tabela com a **quantidade real do universo do projeto**.", 
                                            value="FONTE",
                                            help="A tabela deverá conter três categorias (Cabeçalho, coluna, linha).",
                                            key="nome_sheet_df_universo_3dim_input")
        with coluna2:
            nome_sheet_df_coletado_3dim = st.text_input(label="📝 Informe o nome da aba (sheet) que contém a tabela com a **quantidade coletada do projeto**.", 
                                                    value="COLETADO",
                                                    help="A tabela deverá conter três categorias (Cabeçalho, coluna, linha).",
                                                    key="nome_sheet_df_coletado_3dim_input")

        with st.status("🔍 A seguir, veja uma imagem de exemplo da tabela:"):
            st.image(image="images/Tabela fonte universo.png", width="content")
        input_buttom_submit_DATA_3dim = st.form_submit_button("Enviar")
            
    if input_buttom_submit_DATA_3dim:
        st.session_state.nome_sheet_df_universo_3dim = (nome_sheet_df_universo_3dim or "").strip()
        st.session_state.nome_sheet_df_coletado_3dim = (nome_sheet_df_coletado_3dim or "").strip()

        if not st.session_state.nome_sheet_df_universo_3dim or not st.session_state.nome_sheet_df_coletado_3dim:
            st.error("Preencha os dois nomes de abas antes de continuar.", icon="❌")
        else:
            st.success("Nome das abas (sheets) enviado com sucesso", icon="✅")

    st.write('')
    data_file_pond = st.file_uploader("📂 Selecione o banco de dados (em xlsx)", 
                                type=["xlsx"], 
                                help="Selecione o arquivo Excel contendo as tabelas **quantidade real do universo do projeto** e **quantidade coletada do projeto**.", 
                                key="ponderacao_uploader_3dim")

    if data_file_pond is not None:
        # Lista as abas disponíveis (ajuda muito a evitar erro)
        xls = pd.ExcelFile(data_file_pond)
        st.caption(f"Abas encontradas no arquivo: {', '.join(xls.sheet_names)}")

        sheet_univ = (st.session_state.get("nome_sheet_df_universo_3dim", "") or "").strip()
        sheet_col = (st.session_state.get("nome_sheet_df_coletado_3dim", "") or "").strip()

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

        df_universo = pd.read_excel(data_file_pond, sheet_name=sheet_univ, header=[0, 1])
        df_universo.index = df_universo.iloc[:, 0]
        df_universo = df_universo.iloc[:, 1:].copy()

        df_coletado = pd.read_excel(data_file_pond, sheet_name=sheet_col, header=[0, 1])
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
    with st.form('cabecalho_multiindex_3dim'):
        with coluna1:
            selected_column_cabecalho = st.selectbox('👇 Selecione a coluna que representa o **nível do cabeçalho** da tabela:', 
                                            colunas, 
                                            key="ponderacao_selected_column_cabecalho",
                                            help="A imagem com o exemplo acima seria a coluna do banco de dados que representa as **empresas**.")
        with coluna2:
            selected_column_coluna = st.selectbox('👇 Selecione a coluna que representa o **nível das colunas** da tabela:', 
                                            colunas, 
                                            key="ponderacao_selected_column_coluna",
                                            help="A imagem com o exemplo acima seria a coluna do banco de dados que representa as **regiões**.")
        with coluna3:
            selected_column_linha = st.selectbox('👇 Selecione a coluna que representa o **nível das linhas** da tabela:', 
                                            colunas, 
                                            key="ponderacao_selected_column_linha",
                                            help="A imagem com o exemplo acima seria a coluna do banco de dados que representa o **porte empresarial**.")
            
        input_buttom_submit_cabecalho_multiindex_3dim = st.form_submit_button("Enviar e gerar coluna de ponderação")
    if input_buttom_submit_cabecalho_multiindex_3dim:
        st.success("Nome das colunas enviado com sucesso", icon="✅")

        st.session_state.data = criar_pond_3dim(df_universo=df_universo, df_coletado=df_coletado, bd_codigo=st.session_state.data,
                                                lista_labels=st.session_state.lista_labels, cabecalho=selected_column_cabecalho,
                                                coluna=selected_column_coluna, linha=selected_column_linha)
        
        st.write("")
        st.dataframe(st.session_state.data[[
                                            selected_column_cabecalho, 
                                            selected_column_coluna, selected_column_linha, "POND", "POND_nova"]], 
                                            hide_index=True, 
                                            selection_mode=["multi-row", "multi-cell"])
        





with tab3:
    coluna1, coluna2 = st.columns(2, border=True)

    with st.form('sheet_name_DFuniverso_DFcoletado_4dim'):
        with coluna1:
            nome_sheet_df_universo_4dim = st.text_input(label="📝 Informe o nome da aba (sheet) que contém a tabela com a **quantidade real do universo do projeto**.", 
                                            value="FONTE",
                                            help="A tabela deverá conter três categorias (Cabeçalho, coluna, linha).",
                                            key="nome_sheet_df_universo_4dim_input")
        with coluna2:
            nome_sheet_df_coletado_4dim = st.text_input(label="📝 Informe o nome da aba (sheet) que contém a tabela com a **quantidade coletada do projeto**.", 
                                                    value="COLETADO",
                                                    help="A tabela deverá conter três categorias (Cabeçalho, coluna, linha).",
                                                    key="nome_sheet_df_coletado_4dim_input")

        with st.status("🔍 A seguir, veja uma imagem de exemplo da tabela:"):
            st.image(image="images/Tabela fonte universo_4dim.png", width="content")
        input_buttom_submit_DATA_4dim = st.form_submit_button("Enviar")
            
    if input_buttom_submit_DATA_4dim:
        st.session_state.nome_sheet_df_universo_4dim = (nome_sheet_df_universo_4dim or "").strip()
        st.session_state.nome_sheet_df_coletado_4dim = (nome_sheet_df_coletado_4dim or "").strip()

        if not st.session_state.nome_sheet_df_universo_4dim or not st.session_state.nome_sheet_df_coletado_4dim:
            st.error("Preencha os dois nomes de abas antes de continuar.", icon="❌")
        else:
            st.success("Nome das abas (sheets) enviado com sucesso", icon="✅")

    st.write('')
    data_file_pond = st.file_uploader("📂 Selecione o banco de dados (em xlsx)", 
                                type=["xlsx"], 
                                help="Selecione o arquivo Excel contendo as tabelas **quantidade real do universo do projeto** e **quantidade coletada do projeto**.", 
                                key="ponderacao_uploader_4dim")

    if data_file_pond is not None:
        # Lista as abas disponíveis (ajuda muito a evitar erro)
        xls = pd.ExcelFile(data_file_pond)
        st.caption(f"Abas encontradas no arquivo: {', '.join(xls.sheet_names)}")

        sheet_univ = (st.session_state.get("nome_sheet_df_universo_4dim", "") or "").strip()
        sheet_col = (st.session_state.get("nome_sheet_df_coletado_4dim", "") or "").strip()

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

        df_universo = pd.read_excel(data_file_pond, sheet_name=sheet_univ, 
                                    header=[0, 1, 2], # <- pega CABEÇALHO SUPERIOR, CABEÇALHO e COLUNA
                                    index_col=0 # <- LINHA vira índice (Dimensão 4)
                                    )

        df_coletado = pd.read_excel(data_file_pond, sheet_name=sheet_col,
                                    header=[0, 1, 2], # <- pega CABEÇALHO SUPERIOR, CABEÇALHO e COLUNA
                                    index_col=0 # <- LINHA vira índice (Dimensão 4)
                                    )

        st.session_state.df_universo = df_universo
        st.session_state.df_coletado = df_coletado
        
        st.success("Planilha carregada com sucesso!", icon="✅")

    st.write('')
    st.write('')
    st.write('')
    colunas = st.session_state.data.columns.tolist()
    coluna1, coluna2, coluna3, coluna4 = st.columns(4)
    with st.form('cabecalho_multiindex_4dim'):
        with coluna1:
            selected_column_cabecalho_greater = st.selectbox('👇 Selecione a coluna que representa o **nível do cabeçalho superior** da tabela:', 
                                            colunas, 
                                            key="ponderacao_selected_column_cabecalho_4d",
                                            help="A imagem com o exemplo acima seria a coluna do banco de dados que representa o **Gênero**.")
        with coluna2:
            selected_column_cabecalho = st.selectbox('👇 Selecione a coluna que representa o **nível do cabeçalho** da tabela:', 
                                            colunas, 
                                            key="ponderacao_selected_column_cabecalho_greater_4d",
                                            help="A imagem com o exemplo acima seria a coluna do banco de dados que representa o **Público - PF ou PJ**.")
        with coluna3:
            selected_column_coluna = st.selectbox('👇 Selecione a coluna que representa o **nível das colunas** da tabela:', 
                                            colunas, 
                                            key="ponderacao_selected_column_coluna_4d",
                                            help="A imagem com o exemplo acima seria a coluna do banco de dados que representa o **Segmento empresarial**.")
        with coluna4:
            selected_column_linha = st.selectbox('👇 Selecione a coluna que representa o **nível das linhas** da tabela:', 
                                            colunas, 
                                            key="ponderacao_selected_column_linha_4d",
                                            help="A imagem com o exemplo acima seria a coluna do banco de dados que representa as **Regiões**.")
            
        input_buttom_submit_cabecalho_multiindex_4dim = st.form_submit_button("Enviar e gerar coluna de ponderação")
    if input_buttom_submit_cabecalho_multiindex_4dim:
        st.success("Nome das colunas enviado com sucesso", icon="✅")

        st.session_state.data = criar_pond_4dim(df_universo=df_universo, df_coletado=df_coletado, bd_codigo=st.session_state.data,
                                                lista_labels=st.session_state.lista_labels, 
                                                cabecalho_greater=selected_column_cabecalho_greater, 
                                                cabecalho=selected_column_cabecalho,
                                                coluna=selected_column_coluna, linha=selected_column_linha)
        
        st.write("")
        st.dataframe(st.session_state.data[[
                                            "ID_EMP", selected_column_cabecalho_greater, selected_column_cabecalho, 
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






