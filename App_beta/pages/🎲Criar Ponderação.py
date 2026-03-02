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
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.", icon="⚠️")
    st.stop()

st.title('Pré-Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode criar a coluna de Ponderação')
st.write('')

tab1, tab2 = st.tabs(["Ponderação", "RAKE"])

with tab1:
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
            if qtd_dimensao == 2:
                st.write("2 dimensões:")
                st.image(image="images/Tabela fonte universo_2dim.png")
            elif qtd_dimensao == 3:
                st.write("3 dimensões:")
                st.image(image="images/Tabela fonte universo.png")
            elif qtd_dimensao == 4:
                st.write("4 dimensões:")
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
            st.error(result, icon="❌")
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


def rake_weights(df, weight_col, margins, control=None):
    """
    Raking (IPF) por margens 1D.
    
    df: DataFrame com colunas das variáveis de margem
    weight_col: nome da coluna de peso a ajustar
    margins: dict {var: {categoria: total_pop}}
             ex.: {"sexo": {"M": 5200, "F": 4800}, "idade": {"18-34": 3000, ...}}
    control: dict com "maxit" e "epsilon"
    """
    if control is None:
        control = {"maxit": 100, "epsilon": 1e-10}

    w = df[weight_col].to_numpy(dtype=float)

    # Checagens básicas (missing em variáveis de margem quebra o algoritmo)
    for var in margins.keys():
        if df[var].isna().any():
            raise ValueError(f"Há missing na variável de margem '{var}'. Trate antes de rakear.")

    for it in range(control["maxit"]):
        w_old = w.copy()
        max_rel_change = 0.0

        # Ajusta uma margem por vez
        for var, pop_totals in margins.items():
            # Totais atuais por categoria (ponderados)
            current = (
                pd.DataFrame({var: df[var].values, "_w": w})
                .groupby(var)["_w"].sum()
                .to_dict()
            )

            # Aplica fator categoria-a-categoria
            for cat, pop_total in pop_totals.items():
                cur_total = current.get(cat, 0.0)

                # Se a categoria não aparece na amostra, não dá para ajustar (divisão por zero)
                if cur_total <= 0:
                    raise ValueError(
                        f"Categoria '{cat}' (var='{var}') tem total atual 0 na amostra. "
                        f"Rake não consegue ajustar: revise categorias/margens/amostra."
                    )

                ratio = pop_total / cur_total
                mask = (df[var].values == cat)
                w[mask] *= ratio

        # Critério de convergência: maior mudança relativa de peso
        rel_change = np.max(np.abs(w - w_old) / (np.abs(w_old) + 1e-12))
        max_rel_change = max(max_rel_change, rel_change)

        if max_rel_change < control["epsilon"]:
            break

    return w


with tab2:
    with st.form('sheet_name_fonte_rake'):
        with st.container(border=True):
            nome_sheet_df_rake = st.text_input(
                label="📝 Digite o nome da aba (sheet) que contém a tabela com os **Totais marginais** das características demográficas importantes para o estudo.", 
                value="RAKE",
                # help="A tabela deverá conter duas categorias (Coluna, Linha).",
                key="pond_nome_sheet_rake"
                )
            
        with st.status("🔍 A seguir, veja uma imagem de exemplo da tabela:"):
            st.image(image="images/Tabela fonte pond rake.png")
        input_buttom_submit_DATA_rake = st.form_submit_button("Enviar")

    if input_buttom_submit_DATA_rake:
        st.session_state.nome_sheet_df_rake = nome_sheet_df_rake

        if not st.session_state.nome_sheet_df_rake:
            st.error("Preencha o nome da aba antes de continuar.", icon="❌")
        else:
            st.success("Nome da aba (sheet) enviado com sucesso", icon="✅")


    st.write('')
    data_file_pond_rake = st.file_uploader(
        "📂 Selecione o banco de dados (em xlsx)", 
        type=["xlsx"], 
        help="Selecione o arquivo Excel contendo a tabela com os **Totais marginais** das características demográficas.", 
        key="ponderacao_rake_uploader"
    )

    if data_file_pond_rake is not None:
        # Lista as abas disponíveis (ajuda muito a evitar erro)
        xls = pd.ExcelFile(data_file_pond_rake)
        st.caption(f"Abas encontradas no arquivo: {',  '.join(xls.sheet_names)}")

        sheet_rake = st.session_state.get("nome_sheet_df_rake", "")

        # Validações antes de ler
        if st.session_state.nome_sheet_df_rake not in xls.sheet_names:
            st.error(f"A aba dos **Totais marginais** '{sheet_rake}' não existe no arquivo.", icon="❌")
            st.stop()

        df_rake = pd.read_excel(
            data_file_pond_rake, 
            sheet_name=nome_sheet_df_rake
            )
        st.session_state.df_rake = df_rake
        st.success("Planilha carregada com sucesso!", icon="✅")

        # ========================================================== #
        ### Forçar um filtro para apresentar o resultado da Cielo ###
        df = st.session_state.data.copy()
        df = df.loc[(df["TRAB_C"] == 1) & (df["ONDA"] == 59)]

        # df_margins -> margins (dict de dict)
        margins = (
            df_rake.dropna(subset=["Total marginais"])
                .groupby("Colunas")
                .apply(lambda g: dict(zip(g["Codigo"], g["Total marginais"])), include_groups=False)
                .to_dict()
        )
        print("\n", margins)

        df["w_base"] = 1.0
        w_raked = rake_weights(df, "w_base", margins, control={"maxit": 5000, "epsilon": 1e-10})
        df["POND_RAKE"] = w_raked
        st.write("")
        COLUNAS = [col for col in df.columns.tolist() if col != "w_base"]
        with st.expander("📋 Colunas"):
            # default_cols = st.session_state.data.columns.tolist()
            colunas = st.multiselect('Selecione as colunas que deseja visualizar:', 
                                        COLUNAS, 
                                        default=["ID_EMP", "PF_PJ", "SEG_NOVO_BU", "VREG", "POND", "POND_RAKE"],
                                        key="pond_rake_colunas")
        dados_filtrados = df[colunas]
        st.dataframe(dados_filtrados, hide_index=True, selection_mode=["multi-row", "multi-cell"], use_container_width=True)


    
st.write("")
st.write("")
st.write("")
st.divider()
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg")






