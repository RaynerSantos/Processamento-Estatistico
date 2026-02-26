import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import recode_variavel

if "bandeiras_criadas" not in st.session_state:
    st.session_state.bandeiras_criadas = []

def verifica_label_ordem(dataframe_recode_edited):
    # Verificar se as labels e a ordem foi preenchida corretamente
    mapping_de_para_df_recode = dict(zip(dataframe_recode_edited['Label nova'], dataframe_recode_edited['Ordem']))
    lista_verif = []
    erro = 0
    for v in mapping_de_para_df_recode.values():
        if v in lista_verif:
            erro += 1
            print("Verificar correspondência entre códigos e labels")
        lista_verif.append(v)
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


st.set_page_config(layout='wide', page_title='Processamento de dados',
                   page_icon='images/Logo_Expertise.png')

st.logo(image="images/ExpertiseAI.svg", size="large")

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.")
    st.stop()

st.title('Pré-Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode realizar recodes simples em suas variáveis existentes.')
st.write('')

with st.spinner("Please wait..."):
    with st.expander("📅 Dicionário de variáveis:"):
        st.dataframe(st.session_state.lista_variaveis, hide_index=True, selection_mode=["multi-row", "multi-cell"], use_container_width=True)

st.write('')

colunas = st.session_state.data.columns.tolist()
selected_column = st.multiselect('Selecione a(s) coluna(s) que será(ão) recodificada(s):', colunas, key="recode_selected_column")

if selected_column:
    for col in selected_column:
        rotulo = st.session_state.lista_variaveis.loc[st.session_state.lista_variaveis["Coluna"] == col, "Rotulo"].iloc[0]
        st.write(f'**{col}**: {rotulo}')
    st.write("")
    st.write("")

    # dataframe_recode_value_counts = pd.DataFrame(st.session_state.data[selected_column[0]].value_counts(dropna=False))
    # labels_sub = st.session_state.lista_labels.loc[st.session_state.lista_labels["Coluna"] == selected_column[0]]
    # dataframe_recode_value_counts["Codigo"] = dataframe_recode_value_counts.index
    # dataframe_recode_value_counts["Label"] = dataframe_recode_value_counts["Codigo"].map(dict(zip(labels_sub["Codigo"], labels_sub["Label"])))
    # dataframe_recode_value_counts['Label nova'] = None
    # dataframe_recode_value_counts['Ordem'] = None
    # dataframe_recode_value_counts = dataframe_recode_value_counts[["Codigo", "Label", "Label nova", "Ordem"]]

    dataframe_recode = st.session_state.lista_labels[st.session_state.lista_labels['Coluna'] == selected_column[0]][['Codigo', 'Label']].copy()
    dataframe_recode = dataframe_recode.rename(columns={'Codigo': 'Codigo', 'Label': 'Label'})
    dataframe_recode['Label nova'] = None
    dataframe_recode['Ordem'] = None

    # df_merge = dataframe_recode.merge(
    #     dataframe_recode_value_counts,
    #     on="Codigo",
    #     how="outer",
    #     suffixes=("_recode", "_vc")
    # )
    # df_merge["Label"] = df_merge["Label_recode"].combine_first(df_merge["Label_vc"])
    # df_merge["Label nova"] = df_merge["Label nova_recode"].combine_first(df_merge["Label nova_vc"])
    # df_merge["Ordem"] = df_merge["Ordem_recode"].combine_first(df_merge["Ordem_vc"])

    # df_merge_recode = df_merge.drop(columns=[
    #     "Label_recode", "Label_vc",
    #     "Label nova_recode", "Label nova_vc",
    #     "Ordem_recode", "Ordem_vc"
    # ])
    
    dataframe_recode_edited = st.data_editor(dataframe_recode, 
                                             num_rows="fixed", 
                                            #  use_container_width=True, 
                                             key="dataframe_recode_editor", 
                                             hide_index=True,
                                             use_container_width=True
                                             )
    st.write("")
    
    nome_bandeira_recode = st.text_input(
        label="📝 Digite o(s) nome(s) da(s) nova(s) bandeira(s) recodificada(s) utilizando **vírgula e um espaço (, )**", 
        placeholder="nome da nova bandeira recodificada", 
        key="recode_nome_bandeira"
    )

    nome_bandeira_recode = nome_bandeira_recode.split(", ")
    for nome in nome_bandeira_recode:
        if nome in st.session_state.data.columns:
            st.error(f"A coluna '{nome}' já existe no DataFrame. Por favor, escolha outro nome.", 
                    icon="⚠️")
            

    if st.button('Realizar recode', key="btn_recode") and nome_bandeira_recode:
        # st.dataframe(dataframe_recode_edited, hide_index=True)

        erro_label_ordem = verifica_label_ordem(dataframe_recode_edited)

        if erro_label_ordem > 0:
            st.warning("Verificar correspondência entre a Label nova e a ordenação de cada Label", icon="⚠️")
            st.write("")

        else:
            res_verificacao = verif_cols_selected(selected_column, st.session_state.lista_labels)
            if isinstance(res_verificacao, str):
                st.warning(res_verificacao, icon="⚠️")

            else:
                dict_name_col_bandeira = dict(zip(selected_column, nome_bandeira_recode))
                for col, name_bandeira in dict_name_col_bandeira.items():
                    data, lista_labels = recode_variavel(
                        data=st.session_state.data,
                        lista_labels=st.session_state.lista_labels,
                        COLUNA_ORIGINAL=col,
                        NOVA_BANDEIRA=name_bandeira,
                        dataframe_recode=dataframe_recode_edited
                    )
                    st.session_state.data = data
                    st.session_state.lista_labels = lista_labels
                    st.session_state.ultima_bandeira = name_bandeira
                    st.session_state.bandeiras_criadas.append(st.session_state.ultima_bandeira)
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
                    use_container_width=True
                )


st.write('')
st.divider()
if st.button("Recarregar página", icon="🔄"):
    st.rerun()
st.write('')
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg")  