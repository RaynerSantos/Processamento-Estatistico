import pandas as pd
import numpy as np
from regex import F
import streamlit as st
from io import BytesIO
from collections import Counter
from utils import ordenar_labels, ordenar_labels_multipla, ordenar_valores, classificar_nps, funcao_agrupamento, classificar_satis
from metodos import processar_tabela, mensagem_sucesso, processamento
from metodos import verificar_incosistencias_iniciais, verif_TipoTabela, verif_bandeiras_cabecalho, verif_bandeiras

dict_tipo_tabela = {
        "SIMPLES": (
            "Use quando a variável da **linha** for **categórica** (não numérica), como gênero, região, cargo, canal de compra, etc. A tabela mostrará a **distribuição por categorias** (quantidade e/ou %)."
        ),
        "IPA_5": (
            "Use quando a variável da **linha** for uma **escala de Likert com 5 níveis** de concordância (ex.: Discordo totalmente → Concordo totalmente). Ideal para perguntas de **opinião/atitude**."
        ),
        "IPA_10": (
            "Use quando a variável da **linha** for **numérica** e você quer agrupar as notas em faixas **BTB** e **TTB** (ex.: notas baixas vs. notas altas) para facilitar a leitura. São características mensuráveis cujos valores são números que permitem operações matemáticas."
        ),
        "NPS": (
            "Use quando a variável da **linha** for a nota **NPS (0 a 10)**. A tabela separa automaticamente em: **Detratores (0–6)**, **Neutros (7–8)** e **Promotores (9–10)**."
        ),
        "MULTIPLA": (
            "Use quando a variável da **linha** permitir **múltiplas respostas** (marcar mais de uma opção), como 'Por qual motivo você deu essa nota?'. Normalmente essas respostas ficam registradas em **várias colunas** no banco de dados e a tabela consolida tudo em uma única visualização."
        )
    }

st.set_page_config(layout='wide', page_title='Processamento de dados', 
                   page_icon='images/Logo_Expertise.png')

st.logo(image="images/ExpertiseAI.svg", size="large")

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.")
    st.stop()

st.title('Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode gerar o relatório estatístico dos seus dados')
st.write('')

with st.spinner("Please wait..."):
    with st.expander("📅 Dicionário de variáveis:"):
        st.dataframe(st.session_state.lista_variaveis, hide_index=True, selection_mode=["multi-row", "multi-cell"])

    st.write('')
    st.write('')
    # st.write('Preencha os parâmetros solicitados abaixo para gerar a sua tabela de dados processada')
    # st.write('')

    Colunas = st.session_state.data.columns
    with st.form('parametros_processamento_formulario_teste'):

        st.subheader("Preencha os parâmetros solicitados abaixo para gerar o Estatístico")
        st.write("")

        selected_columns_bandeiras = st.multiselect("Selecione as **BANDEIRAS** que representam as colunas da tabela, separados por ', ' (virgula e um espaço).", 
                                                    options=Colunas,
                                                    key="Processamento_Bandeiras")
        st.write("")
        st.write("")
        
        selected_columns_Cabecalho = st.text_input(
            label="📝 Informe o **cabeçalho** desejado que substituará os nomes das colunas na tabela. **Coloque o cabeçalho separado por vírgula e um espaço (, )**", 
            placeholder="Mercado PME, Mercado 500+, TIM, TIM PME, TIM 500+, TIM Prime, VIVO, VIVO PME, VIVO 500+, CLARO, CLARO PME, CLARO 500+", 
            key="processamento_cabecalho",
            help="ℹ️ O cabeçalho é o nome ideal das colunas que você deseja que apareça na tabela processada. Ex.: nome da coluna: **Q3** → nome do cabeçalho para esta coluna: **Setor de atividade**."
            )
        st.divider()

        selected_columns_SIMPLES = []
        selected_columns_IPA_5 = []
        selected_columns_IPA_10 = []
        selected_columns_NPS = []
        qtd_colunas_banco = len(Colunas)
        for tipo, desc in dict_tipo_tabela.items():
            st.write(f"**{tipo}**: {desc}")
            st.write(f"\nSelecione as colunas para **{tipo}**:")
            if tipo == "SIMPLES":
                # selected_columns_SIMPLES = st.multiselect(f"Selecione as colunas que serão processadas na categoria de tabela **{tipo}**", 
                #                                           options=Colunas,
                #                                           key="TipoTabela_SIMPLES")
                col1, col2, col3, col4 = st.columns(4)
                for i, col in enumerate(Colunas):
                    if i <= qtd_colunas_banco*0.25:
                        with col1:
                            if st.checkbox(col, key=f"TipoTabela_SIMPLES__{col}"):
                                selected_columns_SIMPLES.append(col)
                    elif (i > qtd_colunas_banco*0.25) and (i <= qtd_colunas_banco*0.5):
                        with col2:
                            if st.checkbox(col, key=f"TipoTabela_SIMPLES__{col}"):
                                selected_columns_SIMPLES.append(col)
                    elif (i > qtd_colunas_banco*0.5) and (i <= qtd_colunas_banco*0.75):
                        with col3:
                            if st.checkbox(col, key=f"TipoTabela_SIMPLES__{col}"):
                                selected_columns_SIMPLES.append(col)
                    else:
                        with col4:
                            if st.checkbox(col, key=f"TipoTabela_SIMPLES__{col}"):
                                selected_columns_SIMPLES.append(col)
                st.divider()
            
            elif tipo == "IPA_5": 
                col1, col2, col3, col4 = st.columns(4)
                for i, col in enumerate(Colunas):
                    if i <= qtd_colunas_banco*0.25:
                        with col1:
                            if st.checkbox(col, key=f"TipoTabela_IPA_5__{col}"):
                                selected_columns_IPA_5.append(col)
                    elif (i > qtd_colunas_banco*0.25) and (i <= qtd_colunas_banco*0.5):
                        with col2:
                            if st.checkbox(col, key=f"TipoTabela_IPA_5__{col}"):
                                selected_columns_IPA_5.append(col)
                    elif (i > qtd_colunas_banco*0.5) and (i <= qtd_colunas_banco*0.75):
                        with col3:
                            if st.checkbox(col, key=f"TipoTabela_IPA_5__{col}"):
                                selected_columns_IPA_5.append(col)
                    else:
                        with col4:
                            if st.checkbox(col, key=f"TipoTabela_IPA_5__{col}"):
                                selected_columns_IPA_5.append(col)
                st.divider()
            
            elif tipo == "IPA_10": 
                col1, col2, col3, col4 = st.columns(4)
                for i, col in enumerate(Colunas):
                    if i <= qtd_colunas_banco*0.25:
                        with col1:
                            if st.checkbox(col, key=f"TipoTabela_IPA_10__{col}"):
                                selected_columns_IPA_10.append(col)
                    elif (i > qtd_colunas_banco*0.25) and (i <= qtd_colunas_banco*0.5):
                        with col2:
                            if st.checkbox(col, key=f"TipoTabela_IPA_10__{col}"):
                                selected_columns_IPA_10.append(col)
                    elif (i > qtd_colunas_banco*0.5) and (i <= qtd_colunas_banco*0.75):
                        with col3:
                            if st.checkbox(col, key=f"TipoTabela_IPA_10__{col}"):
                                selected_columns_IPA_10.append(col)
                    else:
                        with col4:
                            if st.checkbox(col, key=f"TipoTabela_IPA_10__{col}"):
                                selected_columns_IPA_10.append(col)
                st.divider()

            elif tipo == "NPS": 
                col1, col2, col3, col4 = st.columns(4)
                for i, col in enumerate(Colunas):
                    if i <= qtd_colunas_banco*0.25:
                        with col1:
                            if st.checkbox(col, key=f"TipoTabela_NPS__{col}"):
                                selected_columns_NPS.append(col)
                    elif (i > qtd_colunas_banco*0.25) and (i <= qtd_colunas_banco*0.5):
                        with col2:
                            if st.checkbox(col, key=f"TipoTabela_NPS__{col}"):
                                selected_columns_NPS.append(col)
                    elif (i > qtd_colunas_banco*0.5) and (i <= qtd_colunas_banco*0.75):
                        with col3:
                            if st.checkbox(col, key=f"TipoTabela_NPS__{col}"):
                                selected_columns_NPS.append(col)
                    else:
                        with col4:
                            if st.checkbox(col, key=f"TipoTabela_NPS__{col}"):
                                selected_columns_NPS.append(col)
                st.divider()
            
            elif tipo == "MULTIPLA":
                selected_columns_MULTIPLA = st.text_input(f"""Informe as colunas que serão processadas na categoria de tabela **{tipo}**.
                                                              Os nomes deverão ser informados com **separação por vírgula e um espaço (, )**, ex.: **REC, NEC, NCR**.  
                                                                  ℹ️ **Importante!** Quando o Tipo de Tabela processada for MULTIPLA, o nome da variável deverá ser diferente das colunas de múltipla resposta. Ex.: Se as colunas múltiplas são 'Q8_1, Q8_2, Q8_3' então, o nome da coluna da variável que deverá constar na linha será 'Q8'.""",
                                                          key="TipoTabela_MULTIPLA")
                selected_columns_MULTIPLA = selected_columns_MULTIPLA.split(", ")
        
        input_buttom_submit_processamento = st.form_submit_button("Enviar")

        if input_buttom_submit_processamento:
            st.success("OK", icon="✅")
            st.write(selected_columns_SIMPLES)