import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import recode_variavel

if "bandeiras_criadas" not in st.session_state:
    st.session_state.bandeiras_criadas = []

def verifica_label_ordem(df):
    erro = 0

    # 1) Uma mesma Label renomeada com mais de uma Ordem
    ordens_por_label = df.groupby('Label renomeada')['Novo Codigo'].nunique()
    labels_inconsistentes = ordens_por_label[ordens_por_label > 1]

    if not labels_inconsistentes.empty:
        erro += len(labels_inconsistentes)
        print("Labels com mais de uma ordem:")
        print(labels_inconsistentes)

    # 2) Uma mesma Ordem atribuída a mais de uma Label renomeada
    labels_por_ordem = df.groupby('Novo Codigo')['Label renomeada'].nunique()
    ordens_inconsistentes = labels_por_ordem[labels_por_ordem > 1]

    if not ordens_inconsistentes.empty:
        erro += len(ordens_inconsistentes)
        print("\nOrdens atribuídas a mais de uma label:")
        print(ordens_inconsistentes)

        # opcional: mostrar as linhas problemáticas
        print("\nLinhas com ordens duplicadas entre labels diferentes:")
        print(df[df['Novo Codigo'].isin(ordens_inconsistentes.index)].sort_values('Novo Codigo'))

    return erro

def verif_cols_selected(selected_column, lista_labels):
    dict_labels_sub = []
    for c in selected_column:
        labels_sub = lista_labels.loc[lista_labels["Coluna"] == c]
        dict_labels_sub.append(dict(zip(labels_sub["Codigo"], labels_sub["Label"])))
    
    for i in range(len(dict_labels_sub)-1):
        if dict_labels_sub[i] != dict_labels_sub[i+1]:
            return f"Colunas **{selected_column[i]}** e **{selected_column[i+1]}** tem labels divergentes, não é possível recodificá-las ao mesmo tempo!"
    return 0

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

def limpar_estado_pagina_recode():
    chaves_para_limpar = [
        "recode_selected_column",
        "dataframe_recode_editor",
        "recode_nome_bandeira",
        "ultima_selecao_recode",
        "ultima_bandeira",
    ]

    for chave in chaves_para_limpar:
        st.session_state.pop(chave, None)

    # se quiser também zerar a lista de bandeiras criadas nesta sessão:
    st.session_state.bandeiras_criadas = []


st.set_page_config(layout='wide', page_title='Processamento de dados',
                   page_icon='images/Logo_Expertise.png')

st.logo(image="images/ExpertiseAI.svg", size="large")

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.", icon="⚠️")
    st.stop()

st.title('Pré-Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode realizar recodes simples em suas variáveis existentes.')
st.write('')

with st.spinner("Please wait..."):
    with st.expander("📅 Dicionário de variáveis:"):
        st.dataframe(st.session_state.lista_variaveis, hide_index=True, selection_mode=["multi-row", "multi-cell"], width='stretch')

st.write('')

if "recode_nome_bandeira" not in st.session_state:
    st.session_state.recode_nome_bandeira = ""

if "ultima_selecao_recode" not in st.session_state:
    st.session_state.ultima_selecao_recode = []

sufixo = "_xx"

col1, col2 = st.columns([1.5, 1], border=True, gap='small', vertical_alignment='top', width='stretch')
colunas = st.session_state.data.columns.tolist()
with col1:
    selected_column = st.multiselect('Selecione a(s) coluna(s) que será(ão) recodificada(s):', colunas, key="recode_selected_column")

with col2:
    st.caption("Informação da(s) coluna(s) selecionada(s):")

if selected_column:
    with col2:
        for col in selected_column:
            rotulo = st.session_state.lista_variaveis.loc[st.session_state.lista_variaveis["Coluna"] == col, "Rotulo"].iloc[0]
            st.write(f"**{col}**: {rotulo}")

        nomes_sugeridos = ", ".join(f"{col}{sufixo}" for col in selected_column)

    # atualiza o text_input somente quando a seleção mudar
    if selected_column != st.session_state.ultima_selecao_recode:
        st.session_state.recode_nome_bandeira = nomes_sugeridos
        st.session_state.ultima_selecao_recode = selected_column.copy()
    st.write("")
    st.write("")

    dataframe_recode = st.session_state.lista_labels[st.session_state.lista_labels['Coluna'] == selected_column[0]][['Codigo', 'Label']].copy()
    dataframe_recode = dataframe_recode.rename(columns={'Codigo': 'Codigo', 'Label': 'Label'})
    dataframe_recode['Label renomeada'] = None
    dataframe_recode['Novo Codigo'] = None
    
    dataframe_recode_edited = st.data_editor(dataframe_recode, 
                                             num_rows="fixed", 
                                             key="dataframe_recode_editor", 
                                             hide_index=True,
                                             width='stretch'
                                            )
    st.write("")
    st.write("")

    nome_bandeira_recode = st.text_input(
        label="📝 Digite o(s) nome(s) da(s) nova(s) bandeira(s) recodificada(s) utilizando **vírgula e um espaço (, )**",
        key="recode_nome_bandeira"
        )

    nome_bandeira_recode = [x.strip() for x in nome_bandeira_recode.split(",") if x.strip()]
    for nome in nome_bandeira_recode:
        if nome in st.session_state.data.columns:
            st.error(f"A coluna '{nome}' já existe no DataFrame. Por favor, escolha outro nome.", 
                     icon="❌"
                     )
            

    if st.button('Realizar recode', key="btn_recode", icon=":material/done_outline:") and nome_bandeira_recode:
        # st.dataframe(dataframe_recode_edited, hide_index=True)

        tam_selected_column = len(selected_column)
        tam_nome_bandeira_recode = len(nome_bandeira_recode)
        if tam_selected_column != tam_nome_bandeira_recode:
            st.error("Quantidade de nomes das **bandeiras recodificadas** é diferente da quantidade de **colunas selecionadas**", icon="❌")

        else:
            erro_label_ordem = verifica_label_ordem(dataframe_recode_edited)

            if erro_label_ordem > 0:
                st.error("Verificar correspondência entre a **Label renomeada** e o **novo Código** de cada Label", icon="❌")
                st.write("")

            else:
                res_verificacao = verif_cols_selected(selected_column, st.session_state.lista_labels)
                if isinstance(res_verificacao, str):
                    st.error(res_verificacao, icon="❌")

                else:
                    dict_name_col_bandeira = dict(zip(selected_column, nome_bandeira_recode))
                    for col, name_bandeira in dict_name_col_bandeira.items():
                        data, lista_labels, lista_variaveis = recode_variavel(
                            data=st.session_state.data,
                            lista_labels=st.session_state.lista_labels,
                            lista_variaveis=st.session_state.lista_variaveis,
                            COLUNA_ORIGINAL=col,
                            NOVA_BANDEIRA=name_bandeira,
                            dataframe_recode=dataframe_recode_edited
                        )
                        st.session_state.data = data
                        st.session_state.lista_labels = lista_labels
                        st.session_state.lista_variaveis = lista_variaveis
                        st.session_state.ultima_bandeira = name_bandeira
                        st.session_state.bandeiras_criadas.append(st.session_state.ultima_bandeira)
                    st.write("")
                    st.success('✅ Recode realizado com sucesso!')
                    st.write("")

                    # Exibir a frequência da nova bandeira criada
                    ultima = st.session_state.ultima_bandeira
                    st.write(f'Frequência da nova bandeira: {ultima}')

                    freq = st.session_state.data[ultima].value_counts(dropna=False).rename("Frequência").to_frame()
                    freq["%"] = ( freq["Frequência"] / freq["Frequência"].sum() * 100)
                    total_line = round(pd.DataFrame(freq.sum()).T)
                    total_line.index = ['Total']
                    freq = pd.concat([freq, total_line], ignore_index=False)
                    freq["Código"] = freq.index

                    dict_codigo_label = st.session_state.lista_labels.loc[st.session_state.lista_labels["Coluna"]==st.session_state.ultima_bandeira].set_index("Codigo")["Label"]
                    freq["Código"] = freq.index
                    freq["Label"] = freq["Código"].map(dict_codigo_label)
                    freq.loc["Total", "Label"] = "Total"

                    # st.dataframe(freq[["Código", "Label", "Frequência", "%"]], hide_index=True,
                    #                 column_config={"%": st.column_config.NumberColumn("%", format="percent")})
                    
                    # >>> Colunas formatadas para exibição (pt-BR)
                    freq["Frequência_fmt"] = freq["Frequência"].apply(fmt_int_ptbr)
                    freq["%_fmt"] = freq["%"].apply(lambda v: fmt_pct_ptbr(v, casas=2))

                    st.dataframe(
                        freq[["Código", "Label", "Frequência_fmt", "%_fmt"]].rename(
                            columns={"Frequência_fmt": "Frequência", "%_fmt": "%"}
                        ),
                        hide_index=True,
                        width='stretch'
                    )


st.write('')
st.divider()
if st.button("Recarregar página", icon="🔄"):
    limpar_estado_pagina_recode()
    st.rerun()
st.write('')
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg")  