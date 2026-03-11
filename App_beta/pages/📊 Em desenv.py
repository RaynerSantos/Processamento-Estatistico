import pandas as pd
import numpy as np
import streamlit as st
from io import BytesIO
from collections import Counter
from utils import ordenar_labels, ordenar_labels_multipla, ordenar_valores, classificar_nps, funcao_agrupamento, classificar_satis
from metodos import processar_tabela, mensagem_sucesso, processamento
from metodos import verificar_incosistencias_iniciais, verif_TipoTabela, verif_bandeiras_cabecalho, verif_bandeiras

# Função para salvar as tabelas em um único Excel com várias abas e formatação
def salvar_excel_com_formatacao(todas_tabelas_gerais, bd_processamento):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for i, tabela in enumerate(bd_processamento['Var_linha']):
            nome_aba = f'Tabela{i} {tabela}'
            todas_tabelas_gerais[i].to_excel(writer, sheet_name=nome_aba, index=True)
            workbook = writer.book
            worksheet = writer.sheets[nome_aba]

            # Formatar as linhas que deverão estar com formatação de percentual
            percent_format = workbook.add_format({'num_format': '0.0%'})
            if (bd_processamento['TipoTabela'][i] == 'NPS') | (bd_processamento['TipoTabela'][i] == 'IPA_10'):
                tamanho = len(todas_tabelas_gerais[i])
                for row in range(4, tamanho+1):
                    worksheet.set_row(row, None, percent_format)
                # Formatar as linhas que não terão casas decimais
                num_format = workbook.add_format({'num_format': '0'})
                for row in range((len(todas_tabelas_gerais[i][:-2])+4), (len(todas_tabelas_gerais[i])+4)):
                    worksheet.set_row(row, None, num_format)

            elif (bd_processamento['TipoTabela'][i] == 'MULTIPLA'):
                tamanho = len(todas_tabelas_gerais[i])
                # Formatar as linhas que deverão estar com formatação de percentual
                for row in range(4, tamanho+1):
                    worksheet.set_row(row, None, percent_format)
                # Formatar as linhas que não terão casas decimais
                num_format = workbook.add_format({'num_format': '0'})
                for row in range((len(todas_tabelas_gerais[i])+1), (len(todas_tabelas_gerais[i])+2)):
                    worksheet.set_row(row, None, num_format)
                # Formatar o Índice de Multiplicidade que terá somente 1 casa decimal
                num_format = workbook.add_format({'num_format': '0.0'})
                for row in range((len(todas_tabelas_gerais[i])+3), (len(todas_tabelas_gerais[i])+4)):
                    worksheet.set_row(row, None, num_format)

            else:
                tamanho = len(todas_tabelas_gerais[i]) + 4
                # Formatar as linhas que deverão estar com formatação de percentual
                for row in range(3, tamanho+1):
                    worksheet.set_row(row, None, percent_format)
                # Formatar as linhas que não terão casas decimais
                num_format = workbook.add_format({'num_format': '0'})
                for row in range((len(todas_tabelas_gerais[i][:-2])+4), (len(todas_tabelas_gerais[i])+4)):
                    worksheet.set_row(row, None, num_format)
    return output.getvalue()

# Função para salvar as tabelas em um único Excel com única aba
def salvar_excel_aba_unica(todas_tabelas_gerais, bd_processamento):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Processamento_Estatistico")
        writer.sheets["Processamento_Estatistico"] = worksheet

        linha_atual = 0  # Controle da linha onde cada tabela será escrita
        percent_format = workbook.add_format({'num_format': '0.0%'})
        int_format = workbook.add_format({'num_format': '0'})
        float_format = workbook.add_format({'num_format': '0.0'})

        for i, tabela in enumerate(todas_tabelas_gerais):
            # Escreve o nome da tabela antes dela
            worksheet.write(linha_atual, 0, f'Tabela{i} - {bd_processamento["Var_linha"][i]}')
            linha_atual += 1

            # Salva a tabela na linha atual
            tabela.to_excel(writer, sheet_name="Processamento_Estatistico", startrow=linha_atual, startcol=0)

            # Formatação personalizada (igual à função original, mas ajustando para a aba única)
            tipo = bd_processamento['TipoTabela'][i]
            tamanho = len(tabela)

            if tipo in ['NPS', 'IPA_10']:
                for row in range(linha_atual + 4, linha_atual + tamanho + 3): 
                    worksheet.set_row(row, None, percent_format)
                for row in range(linha_atual + len(tabela[:-2]) + 3, linha_atual + tamanho + 2):  
                    worksheet.set_row(row, None, float_format) 
                for row in range(linha_atual + len(tabela[:-2]) + 4, linha_atual + tamanho + 4): 
                    worksheet.set_row(row, None, int_format)

            elif tipo == 'MULTIPLA':
                for row in range(linha_atual + 4, linha_atual + tamanho + 4):
                    worksheet.set_row(row, None, percent_format)
                for row in range(linha_atual + len(tabela[:-2]) + 3, linha_atual + tamanho + 6): ###
                    worksheet.set_row(row, None, int_format) ###
                worksheet.set_row(linha_atual + tamanho + 3, None, float_format)

            else:
                for row in range(linha_atual + 3, linha_atual + tamanho + 4):
                    worksheet.set_row(row, None, percent_format)
                for row in range(linha_atual + len(tabela[:-2]) + 4, linha_atual + tamanho + 4):
                    worksheet.set_row(row, None, int_format)

            linha_atual += tamanho + 3 + 4  # Adiciona +4 para considerar o cabeçalho e +3 de espaçamento
    return output.getvalue()


if "params_fase1_ok" not in st.session_state:
    st.session_state.params_fase1_ok = False
if "button_salvar_multiplas" not in st.session_state:
    st.session_state.button_salvar_multiplas = False
if "input_buttom_submit_gerar_sintaxe" not in st.session_state:
    st.session_state.input_buttom_submit_gerar_sintaxe = False


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

        with st.container(border=True):
            selected_columns_bandeiras = st.multiselect(
                "Selecione as **BANDEIRAS** que representam as colunas da tabela, separados por ', ' (virgula e um espaço).", 
                options=Colunas,
                key="Processamento_Bandeiras"
            )
        st.write("")
        
        with st.container(border=True):
            selected_columns_Cabecalho = st.text_input(
                label="📝 Informe o **cabeçalho** desejado que substituará os nomes das colunas na tabela. **Coloque o cabeçalho separado por vírgula e um espaço (, )**", 
                placeholder="Mercado PME, Mercado 500+, TIM, TIM PME, TIM 500+, TIM Prime, VIVO, VIVO PME, VIVO 500+, CLARO, CLARO PME, CLARO 500+", 
                key="processamento_cabecalho",
                help="ℹ️ O cabeçalho é o nome ideal das colunas que você deseja que apareça na tabela processada. Ex.: nome da coluna: **Q3** → nome do cabeçalho para esta coluna: **Setor de atividade**."
                )
        st.divider()
        st.write("")

        # selected_columns_SIMPLES = []

        for tipo, desc in dict_tipo_tabela.items():
            if tipo == "SIMPLES":
                with st.container(border=True):
                    st.write(f"**{tipo}**: {desc}")
                    selected_columns_SIMPLES = st.multiselect(f"Selecione as colunas que serão processadas na categoria de tabela **{tipo}**", 
                                                            options=Colunas,
                                                            key="TipoTabela_SIMPLES")
                    if selected_columns_SIMPLES:
                        qtd_simples = len(selected_columns_SIMPLES)
                        TipoTabela_SIMPLES = [tipo] * qtd_simples
                st.divider()
                st.write("")

            
            elif tipo == "IPA_5":
                with st.container(border=True):
                    st.write(f"**{tipo}**: {desc}")
                    selected_columns_IPA_5 = st.multiselect(f"Selecione as colunas que serão processadas na categoria de tabela **{tipo}**", 
                                                            options=Colunas,
                                                            key="TipoTabela_IPA_5")
                    if selected_columns_IPA_5:
                        qtd_ipa_5 = len(selected_columns_IPA_5)
                        TipoTabela_IPA_5 = [tipo] * qtd_ipa_5
                st.write("")
                coluna1, coluna2 = st.columns(2)
                with coluna1: 
                    with st.container(border=True):
                        valores_BTB_IPA_5 = st.text_input(
                            label="📝 Informe a **faixa de notas BTB** - notas baixas desejada. **Coloque os valores separados por vírgula e um espaço (, )**", 
                            placeholder="1, 2", 
                            key="processamento_valores_btb_IPA_5",
                            help="ℹ️ Agrupamento de notas baixas."
                            )
                        st.session_state.valores_BTB_IPA_5 = valores_BTB_IPA_5
                
                with coluna2:
                    with st.container(border=True):
                        valores_TTB_IPA_5 = st.text_input(
                            label="📝 Informe a **faixa de notas TTB** - notas altas desejada. **Coloque os valores separados por vírgula e um espaço (, )**", 
                            placeholder="4, 5", 
                            key="processamento_valores_ttb_IPA_5",
                            help="ℹ️ Agrupamento de notas altas."
                        )
                        st.session_state.valores_TTB_IPA_5 = valores_TTB_IPA_5
                st.divider()
                st.write("")

            elif tipo == "IPA_10":
                with st.container(border=True):
                    st.write(f"**{tipo}**: {desc}")
                    selected_columns_IPA_10 = st.multiselect(f"Selecione as colunas que serão processadas na categoria de tabela **{tipo}**", 
                                                            options=Colunas,
                                                            key="TipoTabela_IPA_10")
                    if selected_columns_IPA_10:
                        qtd_ipa_10 = len(selected_columns_IPA_10)
                        TipoTabela_IPA_10 = [tipo] * qtd_ipa_10
                st.write("")
                coluna3, coluna4 = st.columns(2)
                with coluna3:
                    with st.container(border=True):
                        valores_BTB_IPA_10 = st.text_input(
                            label="📝 Informe a **faixa de notas BTB** - notas baixas desejada. **Coloque os valores separados por vírgula e um espaço (, )**", 
                            placeholder="1, 2, 3", 
                            key="processamento_valores_btb_IPA_10",
                            help="ℹ️ Agrupamento de notas baixas."
                            )
                        st.session_state.valores_BTB_IPA_10 = valores_BTB_IPA_10
                
                with coluna4:
                    with st.container(border=True):
                        valores_TTB_IPA_10 = st.text_input(
                            label="📝 Informe a **faixa de notas TTB** - notas altas desejada. **Coloque os valores separados por vírgula e um espaço (, )**", 
                            placeholder="8, 9, 10", 
                            key="processamento_valores_ttb_IPA_10",
                            help="ℹ️ Agrupamento de notas altas."
                        )
                        st.session_state.valores_TTB_IPA_10 = valores_TTB_IPA_10
                st.divider()
                st.write("")

            elif tipo == "NPS":
                with st.container(border=True):
                    st.write(f"**{tipo}**: {desc}")
                    selected_columns_NPS = st.multiselect(f"Selecione as colunas que serão processadas na categoria de tabela **{tipo}**", 
                                                            options=Colunas,
                                                            key="TipoTabela_NPS")
                    if selected_columns_NPS:
                        qtd_nps = len(selected_columns_NPS)
                        TipoTabela_NPS = [tipo] * qtd_nps

        # st.write("")
        # st.divider()
        # st.write("")
        
        # coluna5, coluna6, coluna7 = st.columns(3)
        # with coluna5:
        #     with st.container(border=True):
        #         NS_NR = st.selectbox(
        #             label="📝 Deseja que a tabela contabilize os casos de **NS/NR (Não sabe / Não respondeu)**?", 
        #             options=["NAO", "SIM"], 
        #             key="processamento_ns_nr",
        #             help="ℹ️ Escolha a opção desejada se a tabela retornará os percentuais de NS/NR ou não."
        #         )

        # with coluna6:
        #     with st.container(border=True):
        #         Var_ID = st.selectbox(
        #             label="📝 Informe qual a **variável/coluna identificadora**, utilizada para identificar a entrevista como única", 
        #             options=Colunas, 
        #             key="processamento_unico_var_id",
        #             help="ℹ️ Essa é a variável/coluna que identifica o respondente e não pode ter código repetido. Ex.: 'codigo_entrevistado'."
        #         )
        
        # with coluna7:
        #     with st.container(border=True):
        #         Var_Pond = st.selectbox(
        #             label="📝 Informe qual a **variável/coluna de ponderação**", 
        #             options=Colunas, 
        #             key="processamento_unico_var_pond",
        #             help="ℹ️ Observação: se o projeto não tiver ponderação, é necessário criar uma coluna no banco de dados do projeto para representar a variável POND e preencher os campos com o nº 1."
        #         )
        st.write("")          
    
        input_buttom_submit_processamento = st.form_submit_button("Enviar parâmetros", icon=":material/done_outline:")

    if input_buttom_submit_processamento:
        st.session_state.params_fase1_ok = True
        st.session_state.renderizar_sintaxe = False
        # st.session_state.input_buttom_submit_processamento = input_buttom_submit_processamento
        st.session_state.selected_columns_bandeiras = selected_columns_bandeiras
        st.session_state.selected_columns_Cabecalho = selected_columns_Cabecalho
        selected_columns = selected_columns_SIMPLES + selected_columns_IPA_5 + selected_columns_IPA_10 + selected_columns_NPS
        st.session_state.selected_columns = selected_columns
        st.session_state.Bandeiras = len(st.session_state.selected_columns) * [st.session_state.selected_columns_bandeiras]
        st.session_state.Bandeiras = [", ".join(valor) for valor in st.session_state.Bandeiras]
        st.session_state.Cabecalho = len(st.session_state.selected_columns) * [st.session_state.selected_columns_Cabecalho]
        st.session_state.TipoTabela = []
        if selected_columns_SIMPLES:
            st.session_state.TipoTabela += TipoTabela_SIMPLES
        if selected_columns_IPA_5:
            st.session_state.TipoTabela += TipoTabela_IPA_5
        if selected_columns_IPA_10:
            st.session_state.TipoTabela += TipoTabela_IPA_10
        if selected_columns_NPS:
            st.session_state.TipoTabela += TipoTabela_NPS
        # st.session_state.TipoTabela = TipoTabela_SIMPLES + TipoTabela_IPA_5 + TipoTabela_IPA_10 + TipoTabela_NPS
        # st.write("Resultado:")
        # st.write(st.session_state.selected_columns)
        st.success("Bandeiras e Variáveis referente as linhas de cada tabela foram salvas com sucesso!", icon="✅")

    st.divider()
    st.write("")
    container = st.container(border=True)
    with container:
        dict_tabela_multipla = {}
        for tipo, desc in dict_tipo_tabela.items():
            if tipo == "MULTIPLA":
                st.write(f"**{tipo}**: {desc}")
                st.write("### Configurações MULTIPLA")

                if "multipla_grupos" not in st.session_state:
                    st.session_state.multipla_grupos = []  # lista de dicts: [{"cols": [...], "name": "Q8"}, ...]
                
                # Botão para adicionar um novo grupo
                if st.button(" Adicionar pergunta múltipla", icon=":material/add:"):
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

                    # Persistir no estado (para usar depois no submit)
                    st.session_state.multipla_grupos[i]["cols"] = cols
                    st.session_state.multipla_grupos[i]["name"] = name

                    # st.write("Colunas: ", st.session_state.multipla_grupos[i]["cols"])
                    # st.write("Name: ", st.session_state.multipla_grupos[i]["name"])

                    nome = st.session_state.multipla_grupos[i]["name"]
                    if nome:  # só cria entrada se tiver nome
                        dict_tabela_multipla[nome] = st.session_state.multipla_grupos[i]["cols"]

                    c1, c2 = st.columns([1, 5])
                    with c1:
                        if st.button("🗑️ Remover", key=f"remove_multipla_{i}"):
                            st.session_state.multipla_grupos.pop(i)
                            st.rerun()

                    st.divider()

                # Se quiser “flatten” (todas as colunas MULTIPLA em uma lista única)
                selected_columns_MULTIPLA = [
                    grp["name"]
                    for grp in st.session_state.multipla_grupos
                    if grp["name"]
                ]

                # if nome in dict_tabela_multipla:
                #     st.warning(f"O nome '{nome}' já foi usado. Escolha outro.")
                # else:
                #     dict_tabela_multipla[nome] = cols

                qtd_multipla = len(st.session_state.multipla_grupos)
                TipoTabela_MULTIPLA = [tipo] * qtd_multipla

            else:
                # se desativar, opcionalmente limpar
                # st.session_state.multipla_grupos = []
                selected_columns_MULTIPLA = []

        st.write("")
        with st.container(border=True):
            Fecha_100 = st.selectbox(
                    label="📝 Deseja que as tabelas múltiplas fechem os percentuais em 100% (**SIM: contabiliza o nº de respostas**) ou, acima de 100% (**NAO: contabiliza o nº de respondentes**)?", 
                    options=["NAO", "SIM"], 
                    key="processamento_fecha_100",
                    help="ℹ️ Escolha a opção desejada se a tabela retornará os percentuais fechando 100% ou não."
                )
        
        st.write("")
        button_salvar_multiplas = st.button("Salvar informações", icon=":material/done_outline:", key="Processamento_salvar_info_multipla")
    if button_salvar_multiplas:
        st.session_state.button_salvar_multiplas = button_salvar_multiplas
        st.session_state.renderizar_sintaxe = False
        st.session_state.selected_columns = st.session_state.selected_columns + selected_columns_MULTIPLA
        st.session_state.TipoTabela = st.session_state.TipoTabela + TipoTabela_MULTIPLA
        st.session_state.Bandeiras = len(st.session_state.selected_columns) * [st.session_state.selected_columns_bandeiras]
        st.session_state.Bandeiras = [", ".join(valor) for valor in st.session_state.Bandeiras]
        st.session_state.Cabecalho = len(st.session_state.selected_columns) * [st.session_state.selected_columns_Cabecalho]
        st.session_state.dict_tabela_multipla = dict_tabela_multipla
        st.session_state.Fecha_100 = Fecha_100
        # st.write(st.session_state.dict_tabela_multipla)
        st.success("Variáveis múltiplas cadastradas com sucesso!", icon="✅")

    st.divider()
    st.write("")

    # button_gerar_sintaxe = st.button("Gerar Sintaxe", icon=":material/done_outline:", key="Processamento_gerar_sintaxe")

    with st.form('parametros_processamento_formulario_gerar_sintaxe'):
        coluna5, coluna6, coluna7 = st.columns(3)
        with coluna5:
            with st.container(border=True):
                NS_NR = st.selectbox(
                    label="📝 Deseja que a tabela contabilize os casos de **NS/NR (Não sabe / Não respondeu)**?", 
                    options=["NAO", "SIM"], 
                    key="processamento_ns_nr",
                    help="ℹ️ Escolha a opção desejada se a tabela retornará os percentuais de NS/NR ou não."
                )

        with coluna6:
            with st.container(border=True):
                Var_ID = st.selectbox(
                    label="📝 Informe qual a **variável/coluna identificadora**, utilizada para identificar a entrevista como única", 
                    options=Colunas, 
                    key="processamento_unico_var_id",
                    help="ℹ️ Essa é a variável/coluna que identifica o respondente e não pode ter código repetido. Ex.: 'codigo_entrevistado'."
                )
        
        with coluna7:
            with st.container(border=True):
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
        input_buttom_submit_gerar_sintaxe = st.form_submit_button("Gerar Sintaxe", icon=":material/done_outline:")
    if input_buttom_submit_gerar_sintaxe:
        st.session_state.input_buttom_submit_gerar_sintaxe = True
        st.session_state.renderizar_sintaxe = True

    if st.session_state.input_buttom_submit_gerar_sintaxe and st.session_state.renderizar_sintaxe:
        st.session_state.NS_NR = [NS_NR] * len(st.session_state.selected_columns)
        st.session_state.Var_ID = [Var_ID] * len(st.session_state.selected_columns)
        st.session_state.Var_Pond = [Var_Pond] * len(st.session_state.selected_columns)
        print("\n", "#", "="*100, "#")
        print("\nTipoTabela: ", st.session_state.TipoTabela)
        print("Tamanho: ", len(st.session_state.TipoTabela))
        print("\nBandeiras: ", st.session_state.Bandeiras)
        print("Tamanho: ", len(st.session_state.Bandeiras))
        print("\nCabecalho: ", st.session_state.Cabecalho)
        print("Tamanho: ", len(st.session_state.Cabecalho))
        print("\nVar_linha: ", st.session_state.selected_columns)
        print("Tamanho: ", len(st.session_state.selected_columns))
        print("\nNS_NR: ", st.session_state.NS_NR)
        print("Tamanho: ", len(st.session_state.NS_NR))
        print("\nVar_ID: ", st.session_state.Var_ID)
        print("Tamanho: ", len(st.session_state.Var_ID))
        print("\nVar_Pond: ", st.session_state.Var_Pond)
        print("Tamanho: ", len(st.session_state.Var_Pond))

        # cria sintaxe SOMENTE se ainda não existir
        sintaxe = pd.DataFrame({
            "TipoTabela": st.session_state.TipoTabela,
            "Bandeiras": st.session_state.Bandeiras,
            "Cabecalho": st.session_state.Cabecalho,
            "Var_linha": st.session_state.selected_columns,
            "Contabiliza_NS/NR": st.session_state.NS_NR
        })
        st.session_state.sintaxe = sintaxe
        print("\n", st.session_state.sintaxe)

        st.session_state.BTB = np.where(st.session_state.sintaxe["TipoTabela"] == "IPA_5", st.session_state.valores_BTB_IPA_5, 
                                        np.where(st.session_state.sintaxe["TipoTabela"] == "IPA_10", st.session_state.valores_BTB_IPA_10,
                                        None))
        st.session_state.TTB = np.where(st.session_state.sintaxe["TipoTabela"] == "IPA_5", st.session_state.valores_TTB_IPA_5, 
                                        np.where(st.session_state.sintaxe["TipoTabela"] == "IPA_10", st.session_state.valores_TTB_IPA_10,
                                        None))
        st.session_state.sintaxe["BTB"] = st.session_state.BTB
        st.session_state.sintaxe["TTB"] = st.session_state.TTB

        # cria a coluna com os agrupamentos (lista de colunas) quando Var_linha estiver no dict
        st.session_state.sintaxe["Valores_Agrup"] = st.session_state.sintaxe["Var_linha"].map(st.session_state.dict_tabela_multipla)

        # substituir NaN por lista vazia para os não-múltiplos:
        st.session_state.sintaxe["Valores_Agrup"] = st.session_state.sintaxe["Valores_Agrup"].apply(lambda x: x if isinstance(x, list) else [])
        st.session_state.sintaxe["Valores_Agrup"] = st.session_state.sintaxe["Valores_Agrup"].apply(lambda lst: ", ".join(lst) if lst else "")

        st.session_state.Fecha_100 = np.where(st.session_state.sintaxe["TipoTabela"] == "MULTIPLA", st.session_state.Fecha_100, None)
        st.session_state.sintaxe["Fecha_100"] = st.session_state.Fecha_100
        st.session_state.sintaxe["Var_ID"] = st.session_state.Var_ID
        st.session_state.sintaxe["Var_Pond"] = st.session_state.Var_Pond

        st.write("")
        # st.dataframe(st.session_state.lista_variaveis)
        mapping_de_para_lista_variaveis = dict(zip(st.session_state.lista_variaveis['Coluna'], st.session_state.lista_variaveis['Rotulo']))
        st.session_state.sintaxe["Titulo"] = st.session_state.sintaxe["Var_linha"].map(mapping_de_para_lista_variaveis)

        mask = st.session_state.sintaxe["TipoTabela"].eq("MULTIPLA") & st.session_state.sintaxe["Valores_Agrup"].apply(len).gt(0)
        primeiras = st.session_state.sintaxe.loc[mask, "Valores_Agrup"].str[0]  # pega o primeiro item da lista
        # st.write(f"Primeiras: {primeiras}")

        st.session_state.sintaxe.loc[mask, "Titulo"] = primeiras.map(mapping_de_para_lista_variaveis).fillna(st.session_state.sintaxe.loc[mask, "Var_linha"])

        
        st.write("")
        st.subheader("Parâmetros para a criação das tabelas:")
        st.write("Cada linha é uma tabela que será processada de acordo com os parâmetros fornecidos")
        sintaxe_edited = st.data_editor(
            st.session_state.sintaxe,
            num_rows="dynamic",
            key="dataframe_sintaxe_editor", 
            hide_index=True
        )

        st.session_state.sintaxe_edited = sintaxe_edited

        st.divider()
        st.write("")

        # Formato do output (uma única aba ou para cada tabela processada gerar uma nova aba)
        with st.form(key='output_excel_processamento'):
            tipo_output = st.selectbox(label='Formato do output', options=['Única aba', 'Várias abas'])
            excel_name = st.text_input(label='Nome do arquivo')
            processar_dados = st.form_submit_button("Processar Dados", icon=":material/done_outline:")

        if processar_dados:
            st.session_state.sintaxe_edited = sintaxe_edited
            # Processar os dados e obter as tabelas
            todas_tabelas_gerais = processamento(
                data=st.session_state.data, 
                bd_processamento=st.session_state.sintaxe_edited, 
                lista_labels=st.session_state.lista_labels
            )
            
            if tipo_output == 'Várias abas':
                # Salvar em Excel com formatação
                excel_data = salvar_excel_com_formatacao(todas_tabelas_gerais, bd_processamento=st.session_state.sintaxe_edited)
            elif tipo_output == 'Única aba':
                # Salvar em Excel com formatação
                excel_data = salvar_excel_aba_unica(todas_tabelas_gerais, bd_processamento=st.session_state.sintaxe_edited)
            
            # Link para download
            st.download_button(
                label="Baixar Excel Processado",
                data=excel_data,
                file_name=excel_name + ".xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


st.write('')
st.write('')
st.write('')
st.write('')
st.divider()
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg") # Expertise_Marca_VerdeEscuro_mini.jpg
            

