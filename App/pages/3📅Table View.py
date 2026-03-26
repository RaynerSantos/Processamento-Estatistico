import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date

st.set_page_config(layout='wide', page_title='Processamento de dados', 
                   page_icon='images/Logo_Expertise.png')

st.logo(image="images/ExpertiseAI.svg", size="large")

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.")
    st.stop()

st.title('Pré-Processamento de Dados Estatísticos')
st.divider()

tab1, tab2 = st.tabs(["Visualizar Frequência", "Deletar Coluna"])

with tab1:
    st.subheader('Aqui você pode visualizar a frequência da coluna desejada')
    st.write('')

    with st.spinner("Please wait..."):
        with st.expander("📅 Dicionário de variáveis:"):
            st.dataframe(st.session_state.lista_variaveis, hide_index=True, selection_mode=["multi-row", "multi-cell"], width='stretch')

    st.write('')
    st.write('')

    with st.container(border=True):
        tipo_freq = st.selectbox(
            '👇 Escolha o tipo de visualização da tabela de frequência', 
            ["Simples", "Ponderada"], 
            key="table_view_tipo_freq"
        )
    st.write("")

    colunas = st.session_state.data.columns.tolist()
    coluna1, coluna2= st.columns(2)
    with coluna1:
        with st.container(border=True):
            selected_column = st.selectbox('👇 Selecione a coluna desejada:', 
                                            colunas, 
                                            key="table_view_selected_column")
    with coluna2:
        with st.container(border=True):
            casas_decimais = st.number_input(label="📟 Insira a quantidade de casas decimais que deseja visualizar o percentual",
                                            min_value=0, max_value=5,
                                            value=2, 
                                            key="casas_decimais_table_view")

    if selected_column:
        rotulo = st.session_state.lista_variaveis.loc[st.session_state.lista_variaveis["Coluna"] == selected_column, "Rotulo"].iloc[0]
        st.write(f'**{selected_column}**: {rotulo}')
        st.write("")

    # if selected_column:
    #     rotulo = st.session_state.lista_variaveis.loc[st.session_state.lista_variaveis["Coluna"] == selected_column, "Rotulo"].iloc[0]
    #     st.write(f'**{selected_column}**: {rotulo}')
    #     st.write("")

    def fmt_int_ptbr(x):
        if pd.isna(x):
            return ""
        # 8634 -> "8.634"
        return f"{int(x):,}".replace(",", ".")

    def fmt_pct_ptbr(x, casas=2):
        if pd.isna(x):
            return ""
        # 56.12 -> "56,12%"
        s = f"{x:,.{casas}f}"          # "56.12" (ou "1,234.56" se tiver milhar)
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return s + "%"


    if st.button('Visualizar frequência', key="btn_table_view") and selected_column and tipo_freq:
        if tipo_freq == "Simples":
            freq = (
                st.session_state.data[selected_column]
                .value_counts(dropna=False)
                .rename("Frequência")
                .to_frame()
            )
        else:
            if "POND" in st.session_state.data.columns:
                # >>> soma da ponderação por código (inclui NaN do código se houver)
                freq = (
                    st.session_state.data.groupby(selected_column, dropna=False)["POND"]
                    .sum()
                    .rename("Frequência")
                    .to_frame()
                )
            else:
                st.warning("Necessário criar a coluna de **Ponderação (POND)** para trazer a frequência ponderada", icon="⚠️")
        freq["%"] = ( freq["Frequência"] / freq["Frequência"].sum() * 100)
        total_line = round(pd.DataFrame(freq.sum()).T)
        total_line.index = ['Total']
        freq = pd.concat([freq, total_line], ignore_index=False)
        freq["Código"] = freq.index

        dict_codigo_label = st.session_state.lista_labels.loc[st.session_state.lista_labels["Coluna"]==selected_column].set_index("Codigo")["Label"]
        freq["Código"] = freq.index
        freq["Label"] = freq["Código"].map(dict_codigo_label)
        freq.loc["Total", "Label"] = "Total"

        # st.dataframe(
        #     freq[["Código", "Label", "Frequência", "%"]], 
        #     hide_index=True, 
        #     column_config={"%": st.column_config.NumberColumn("%", format=f"%.{casas_decimais}f%%")},
        #     width='stretch'
        #     )
        
        # >>> Colunas formatadas para exibição (pt-BR)
        freq["Frequência_fmt"] = freq["Frequência"].apply(fmt_int_ptbr)
        freq["%_fmt"] = freq["%"].apply(lambda v: fmt_pct_ptbr(v, casas=casas_decimais))

        st.dataframe(
            freq[["Código", "Label", "Frequência_fmt", "%_fmt"]].rename(
                columns={"Frequência_fmt": "Frequência", "%_fmt": "%"}
            ),
            hide_index=True,
            width='stretch'
        )

with tab2:
    st.subheader('Aqui você pode excluir a(s) coluna(s) desejada(s) do seu banco de dados')
    st.write('')

    with st.spinner("Please wait..."):
        with st.expander("📅 Dicionário de variáveis **(com Rótulos Editáveis)**:"):
            lista_variaveis_edited = st.data_editor(
                st.session_state.lista_variaveis, 
                disabled=["Coluna"],  # essa coluna não poderá ser editada
                hide_index=True
            )
        st.session_state.lista_variaveis = lista_variaveis_edited

    st.write('')
    st.write('')

    colunas = st.session_state.data.columns.tolist()
    selected_columns_trash = st.multiselect('Selecione a(s) coluna(s) que deseja excluir do banco de dados:', 
                                    colunas, 
                                    key="deletar_coluna_selected_columns_trash")
    
    if selected_columns_trash:
        if st.button("Deletar", key="deletar_colunas", icon="🗑️"):
            colunas_desejadas = [col for col in colunas if col not in selected_columns_trash]
            st.session_state.data = st.session_state.data[colunas_desejadas]

            for col in selected_columns_trash:
                print(f"\n{col}")
                st.session_state.lista_labels = st.session_state.lista_labels.loc[st.session_state.lista_labels["Coluna"] != col]
                st.session_state.lista_variaveis = st.session_state.lista_variaveis.loc[st.session_state.lista_variaveis["Coluna"] != col]

            st.success("Colunas removidas com sucesso!", icon="✅")
    
st.write("")
st.write("")
st.write("")
st.divider()
if st.button("Recarregar página", icon="🔄"):
    st.rerun()
st.write('')
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg") # Expertise_Marca_VerdeEscuro_mini.jpg