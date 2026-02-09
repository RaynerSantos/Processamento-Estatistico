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
    with st.form('parametros_processamento_formulario'):

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
        st.write("")
        st.divider()
        st.write("")

        # selected_columns_SIMPLES = []
        for tipo, desc in dict_tipo_tabela.items():
            if tipo == "SIMPLES":
                st.write(f"**{tipo}**: {desc}")
                selected_columns_SIMPLES = st.multiselect(f"Selecione as colunas que serão processadas na categoria de tabela **{tipo}**", 
                                                          options=Colunas,
                                                          key="TipoTabela_SIMPLES")
                # selected_columns_SIMPLES.append(st.checkbox(Colunas, key="TipoTabela_SIMPLES"))
                st.write("")
                st.divider()
                st.write("")

            
            elif tipo == "IPA_5":
                st.write(f"**{tipo}**: {desc}")
                selected_columns_IPA_5 = st.multiselect(f"Selecione as colunas que serão processadas na categoria de tabela **{tipo}**", 
                                                          options=Colunas,
                                                          key="TipoTabela_IPA_5")
                st.write("")
                coluna1, coluna2 = st.columns(2, border=True)
                with coluna1: 
                    valores_BTB = st.text_input(
                        label="📝 Informe a **faixa de notas BTB** - notas baixas desejada. **Coloque os valores separados por vírgula e um espaço (, )**", 
                        placeholder="1, 2", 
                        key="processamento_valores_btb_IPA_5",
                        help="ℹ️ Agrupamento de notas baixas."
                        )
                
                with coluna2:
                    valores_TTB = st.text_input(
                        label="📝 Informe a **faixa de notas TTB** - notas altas desejada. **Coloque os valores separados por vírgula e um espaço (, )**", 
                        placeholder="4, 5", 
                        key="processamento_valores_ttb_IPA_5",
                        help="ℹ️ Agrupamento de notas altas."
                    )
                st.write("")
                st.divider()
                st.write("")

            elif tipo == "IPA_10":
                st.write(f"**{tipo}**: {desc}")
                selected_columns_IPA_10 = st.multiselect(f"Selecione as colunas que serão processadas na categoria de tabela **{tipo}**", 
                                                          options=Colunas,
                                                          key="TipoTabela_IPA_10")
                st.write("")
                coluna3, coluna4 = st.columns(2, border=True)
                with coluna3: 
                    valores_BTB = st.text_input(
                        label="📝 Informe a **faixa de notas BTB** - notas baixas desejada. **Coloque os valores separados por vírgula e um espaço (, )**", 
                        placeholder="1, 2, 3", 
                        key="processamento_valores_btb_IPA_10",
                        help="ℹ️ Agrupamento de notas baixas."
                        )
                
                with coluna4:
                    valores_TTB = st.text_input(
                        label="📝 Informe a **faixa de notas TTB** - notas altas desejada. **Coloque os valores separados por vírgula e um espaço (, )**", 
                        placeholder="8, 9, 10", 
                        key="processamento_valores_ttb_IPA_10",
                        help="ℹ️ Agrupamento de notas altas."
                    )
                st.write("")
                st.divider()
                st.write("")

            elif tipo == "NPS":
                st.write(f"**{tipo}**: {desc}")
                selected_columns_NPS = st.multiselect(f"Selecione as colunas que serão processadas na categoria de tabela **{tipo}**", 
                                                          options=Colunas,
                                                          key="TipoTabela_NPS")
                st.write("")            


                    # selected_columns_MULTIPLA = st.multiselect(
                    #     "Selecione as **colunas múltipla** que representam uma pergunta do questionário. Ex.: 'Por qual motivo você deu essa nota?'.",
                    #     options=Colunas,
                    #     key="TipoTabela_MULTIPLA"
                    #     )
                    # st.write("")
                    # selected_columns_MULTIPLA_name = st.text_input(
                    #     """Informe o **nome da variável** que irá representar as colunas múltiplas informadas acima.   
                    #     ℹ️ **Importante!** Quando o Tipo de Tabela processada for **MULTIPLA**, o nome da variável deverá ser diferente das colunas de múltipla resposta.   
                    #     **Ex.:** Se as colunas múltiplas são 'Q8_1, Q8_2, Q8_3' então, o nome da variável que irá representar as colunas múltiplas poderá ser 'Q8'.""",
                    #     key="name_MULTIPLA")
                    


                    # selected_columns_MULTIPLA = st.text_input(f"""Informe as colunas que serão processadas na categoria de tabela **{tipo}**.
                    #                                               Os nomes deverão ser informados com **separação por vírgula e um espaço (, )**, ex.: **REC, NEC, NCR**.  
                    #                                                   ℹ️ **Importante!** Quando o Tipo de Tabela processada for MULTIPLA, o nome da variável deverá ser diferente das colunas de múltipla resposta. Ex.: Se as colunas múltiplas são 'Q8_1, Q8_2, Q8_3' então, o nome da coluna da variável que deverá constar na linha será 'Q8'.""",
                    #                                           key="TipoTabela_MULTIPLA")
                    # selected_columns_MULTIPLA = selected_columns_MULTIPLA.split(", ")
    
        input_buttom_submit_processamento = st.form_submit_button("Enviar")

    if input_buttom_submit_processamento:
        selected_columns = selected_columns_SIMPLES + selected_columns_IPA_5 + selected_columns_IPA_10 + selected_columns_NPS
        st.session_state.selected_columns = selected_columns
        st.write("")
        st.write("Resultado:")
        st.write(st.session_state.selected_columns)

    st.write("")
    st.divider()
    st.write("")
    container = st.container(border=True)
    with container:
        for tipo, desc in dict_tipo_tabela.items():
            if tipo == "MULTIPLA":
                st.write(f"**{tipo}**: {desc}")
                st.write("### Configurações MULTIPLA")

                if "multipla_grupos" not in st.session_state:
                    st.session_state.multipla_grupos = []  # lista de dicts: [{"cols": [...], "name": "Q8"}, ...]
                
                # Botão para adicionar um novo grupo
                if st.button("➕ Adicionar pergunta múltipla"):
                    st.session_state.multipla_grupos.append({"cols": [], "name": ""})

                # Renderiza cada grupo já adicionado
                for i, grp in enumerate(st.session_state.multipla_grupos):
                    st.markdown(f"**Pergunta múltipla #{i+1}**")

                    cols = st.multiselect(
                        "Selecione as colunas de **múltipla resposta** que representam uma pergunta do questionário. Ex.: 'Por qual motivo você deu essa nota?' (colunas de exemplo: 'Q8_1, Q8_2, Q8_3').",
                        options=Colunas,
                        key=f"TipoTabela_MULTIPLA_cols_{i}"
                    )
                    name = st.text_input(
                        "Informe o nome da variável - o nome da variável deverá ser diferente das colunas de múltipla resposta (ex.: 'Q8').",
                        key=f"TipoTabela_MULTIPLA_name_{i}",
                        help="ℹ️ **Importante!** Quando o Tipo de Tabela processada for MULTIPLA, o nome da variável deverá ser diferente das colunas de múltipla resposta. Ex.: Se as colunas múltiplas são 'Q8_1, Q8_2, Q8_3' então, o nome da coluna da variável que deverá constar na linha será 'Q8'."
                    )

                    # Persistir no estado (para você usar depois no submit)
                    st.session_state.multipla_grupos[i]["cols"] = cols
                    st.session_state.multipla_grupos[i]["name"] = name

                    c1, c2 = st.columns([1, 5])
                    with c1:
                        if st.button("🗑️ Remover", key=f"remove_multipla_{i}"):
                            st.session_state.multipla_grupos.pop(i)
                            st.rerun()

                    st.divider()

                # Se quiser “flatten” (todas as colunas MULTIPLA em uma lista única)
                selected_columns_MULTIPLA = [
                    col
                    for grp in st.session_state.multipla_grupos
                    for col in grp["cols"]
                ]
            else:
                # se desativar, opcionalmente limpar
                # st.session_state.multipla_grupos = []
                selected_columns_MULTIPLA = []

        st.write("")
        Fecha_100 = st.selectbox(
                label="📝 Deseja que as tabelas múltiplas fechem os percentuais em 100% (**contabiliza o nº de respostas**) ou, acima de 100% (**contabiliza o nº de respondentes**)?", 
                options=["NAO", "SIM"], 
                key="processamento_fecha_100",
                help="ℹ️ Escolha a opção desejada se a tabela retornará os percentuais fechando 100% ou não."
            )
        
        st.write("")
        st.write("")
        if st.button("Salvar informações", icon="✔️", key="Processamento_salvar_info_multipla"):
            st.write("")
            st.write(selected_columns_MULTIPLA)
            st.session_state.selected_columns = st.session_state.selected_columns + selected_columns_MULTIPLA

    st.write("")
    st.divider()
    st.write("")
    
    with st.form('parametros_processamento_formulario_third_fase'):
        coluna5, coluna6 = st.columns(2, border=True)
        with coluna5:
            Var_ID = st.selectbox(
                label="📝 Informe qual a **variável/coluna identificadora**, utilizada para identificar a entrevista como única", 
                options=Colunas, 
                key="processamento_unico_var_id",
                help="ℹ️ Essa é a variável/coluna que identifica o respondente e não pode ter código repetido. Ex.: 'codigo_entrevistado'."
            )
        
        with coluna6:
            Var_Pond = st.selectbox(
                label="📝 Informe qual a **variável/coluna de ponderação**", 
                options=Colunas, 
                key="processamento_unico_var_pond",
                help="ℹ️ Observação: se o projeto não tiver ponderação, é necessário criar uma coluna no banco de dados do projeto para representar a variável POND e preencher os campos com o nº 1."
            )
        st.write("")

        # Titulo = st.text_input(
        #     label="📝 Informe qual deverá ser o **título** da tabela processada.",
        #     placeholder="Título da tabela",
        #     key="processamento_unico_titulo",
        #     help="ℹ️"
        # )
        input_buttom_submit_processamento_third_fase = st.form_submit_button("Enviar")


    if input_buttom_submit_processamento and input_buttom_submit_processamento_third_fase:
        selected_columns = selected_columns_SIMPLES + selected_columns_IPA_5 + selected_columns_IPA_10 + selected_columns_NPS + selected_columns_MULTIPLA
        st.write(f"{selected_columns}")



