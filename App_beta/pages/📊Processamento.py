import pandas as pd
import numpy as np
import streamlit as st
from io import BytesIO
from collections import Counter
from utils import ordenar_labels, ordenar_labels_multipla, ordenar_valores, classificar_nps, funcao_agrupamento, classificar_satis
from metodos import processar_tabela, mensagem_sucesso, processamento
from metodos import verificar_incosistencias_iniciais, verif_TipoTabela, verif_bandeiras_cabecalho, verif_bandeiras

# Função para salvar as tabelas em um único Excel com única aba
def salvar_excel_unica_tabela(tabelas, TipoTabela, Var_linha):
    # Aceita DataFrame único ou lista de DataFrames
    if isinstance(tabelas, pd.DataFrame):
        tabelas = [tabelas]

    # Validação básica (pra não cair em tuple de novo)
    for t in tabelas:
        if not isinstance(t, pd.DataFrame):
            raise TypeError(f"Esperado DataFrame, recebi: {type(t)}. Valor: {str(t)[:200]}")
        
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet(f"{Var_linha}")
        writer.sheets[f"{Var_linha}"] = worksheet

        linha_atual = 0  # Controle da linha onde cada tabela será escrita
        percent_format = workbook.add_format({'num_format': '0.0%'})
        int_format = workbook.add_format({'num_format': '0'})
        float_format = workbook.add_format({'num_format': '0.0'})

        for i, tabela in enumerate(tabelas):
            # Escreve o nome da tabela antes dela
            worksheet.write(linha_atual, 0, f'{Var_linha}')
            linha_atual += 1

            # Salva a tabela na linha atual
            tabela.to_excel(writer, sheet_name=f"{Var_linha}", startrow=linha_atual, startcol=0)

            # Formatação personalizada (igual à função original, mas ajustando para a aba única)
            tamanho = len(tabela)

            if TipoTabela in ['NPS', 'IPA_10']:
                for row in range(linha_atual + 4, linha_atual + tamanho + 3): 
                    worksheet.set_row(row, None, percent_format)
                for row in range(linha_atual + len(tabela[:-2]) + 3, linha_atual + tamanho + 2):  
                    worksheet.set_row(row, None, float_format) 
                for row in range(linha_atual + len(tabela[:-2]) + 4, linha_atual + tamanho + 4): 
                    worksheet.set_row(row, None, int_format)

            elif TipoTabela == 'MULTIPLA':
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

tab1, tab2 = st.tabs(["Processar uma tabela", "Processar por Sintaxe"])

with tab1:
    st.write("")
    st.write("")
    with st.spinner("Please wait..."):
        with st.expander("📅 Dicionário de variáveis:"):
            st.dataframe(
                st.session_state.lista_variaveis, hide_index=True, 
                selection_mode=["multi-row", "multi-cell"], 
                use_container_width=True
                )

    st.write('')
    st.write('')
    st.write('Preencha os parâmetros solicitados abaixo para gerar a sua tabela de dados processada')
    st.write('')

    # dict_tipo_tabela = {
    #     "SIMPLES": "Nesta tabela a variável que representa a linha é CATEGÓRICA (representa características não numéricas). Ela descreve atributos e não podem ser medidas quantitativamente.",
    #     "IPA_5": "Nesta tabela a variável que representa a linha deve ter **5 níveis** de concordância (Escala de Likert).",
    #     "IPA_10": "Nesta tabela a variável que representa a linha é NUMÉRICA e deseja-se criar categorias de BTB e TTB. São características mensuráveis cujos valores são números que permitem operações matemáticas.",
    #     "NPS": "Nesta tabela a variável que representa a linha é NUMÉRICA e se trata da classificação NPS. Os Detratores são as notas de 0 a 6, Neutros as notas 7 e 8 e, os Promotores as notas 9 e 10.",
    #     "MULTIPLA": "Nesta tabela a variável que representa a linha é MÚLTIPLA e possui respostas múltiplas, com mais de uma resposta e, portanto, é gravado suas respostas em duas ou mais colunas no banco de dados."
    #     }

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

    colunas = st.session_state.data.columns.tolist()

    # Upload das planilhas
    coluna1, coluna2 = st.columns(2)
    with st.form('parametros_gerar_tabela_processada'):
        with coluna1:
            TipoTabela = st.selectbox(
                label="📝 Informe o **tipo da tabela** a ser processada", 
                options=dict_tipo_tabela.keys(), 
                key="processamento_unico_TipoTabela",
                help="ℹ️ Tipo de tabela = como a variável que ficará na **linha** deve ser interpretada e exibida. Ela pode ser: **categórica** (SIMPLES), **Likert 5 pontos** (IPA_5), **numérica para BTB/TTB** (IPA_10), **NPS** (NPS) ou **múltipla escolha** (MULTIPLA)."
                )
            with st.status("ℹ️ Informação do Tipo da Tabela Selecionada:"):
            # st.write("ℹ️ Informação do Tipo da Tabela Selecionada:")
                st.write(f"**{TipoTabela}**: {dict_tipo_tabela[TipoTabela]}")
            st.write("")
            st.write("")
        
        with coluna2:
            if TipoTabela == "MULTIPLA":
                Var_linha = st.text_input(
                    label="📝 Informe o nome da variável que deverá constar no **nível das linhas** da tabela processada. Se as colunas de múltipla resposta são: 'Q8_1, Q8_2, Q8_3' então, informe um nome diferente para a variável linha, ex.: 'Q8'.",
                    placeholder="Nome_variavel_linha",
                    key="processamento_unico_var_linha",
                    help="ℹ️ Importante! Quando o Tipo de Tabela processada for MULTIPLA, o nome da variável deverá ser diferente das colunas de múltipla resposta. Ex.: Se as colunas múltiplas são 'Q8_1, Q8_2, Q8_3' então, o nome da coluna da variável que deverá constar na linha será 'Q8'."
                )

            else:
                Var_linha = st.selectbox(
                    label="📝 Informe qual a variável que deverá constar no **nível das linhas** da tabela processada", 
                    options=colunas, 
                    key="processamento_unico_var_linha",
                    help="ℹ️ A variável linha é aquela que cruzará com toda informação das bandeiras."
                    )
            

        # coluna3, coluna4 = st.columns(2)    
        Colunas = st.multiselect(
            label="📝 Informe as **bandeiras** que deverão representar as colunas da tabela processada", 
            options=colunas, 
            key="processamento_unico_Colunas",
            help="ℹ️ As bandeiras são simplesmente as variáveis que constará nas colunas da tabela processada."
            )
        st.write("")
        st.write("")
        
        Cabecalho = st.text_input(
            label="📝 Informe o **cabeçalho** desejado que substituará os nomes das colunas na tabela. **Coloque o cabeçalho separado por vírgula e um espaço (, )**", 
            placeholder="Mercado PME, Mercado 500+, TIM, TIM PME, TIM 500+, TIM Prime, VIVO, VIVO PME, VIVO 500+, CLARO, CLARO PME, CLARO 500+", 
            key="processamento_unico_cabecalho",
            help="ℹ️ O cabeçalho é o nome ideal das colunas que você deseja que apareça na tabela processada. Ex.: nome da coluna: **Q3** → nome do cabeçalho para esta coluna: **Setor de atividade**."
            )
        st.write("")  
        st.write("")  
        
        NS_NR = st.selectbox(
            label="📝 Deseja que a tabela contabilize os casos de **NS/NR (Não sabe / Não respondeu)**?", 
            options=["NAO", "SIM"], 
            key="processamento_unico_ns_nr",
            help="ℹ️ Escolha a opção desejada se a tabela retornará os percentuais de NS/NR ou não."
            )
        st.write("")
        st.write("")
        
        if TipoTabela == "IPA_10" or TipoTabela == "IPA_5":
            coluna3, coluna4 = st.columns(2)
            with coluna3:
                valores_BTB = st.text_input(
                label="📝 Informe a **faixa de notas BTB** - notas baixas desejada. **Coloque os valores separados por vírgula e um espaço (, )**", 
                placeholder="1, 2, 3", 
                key="processamento_unico_valores_btb",
                help="ℹ️ Agrupamento de notas baixas."
                )

            with coluna4:
                valores_TTB = st.text_input(
                    label="📝 Informe a **faixa de notas TTB** - notas altas desejada. **Coloque os valores separados por vírgula e um espaço (, )**", 
                    placeholder="8, 9, 10", 
                    key="processamento_unico_valores_ttb",
                    help="ℹ️ Agrupamento de notas altas."
                )
            st.write("")
            st.write("")
            
        if TipoTabela == "MULTIPLA":
            Valores_Agrup = st.text_input(
                label="📝 Informe quais as **variáveis/colunas representam a variável MÚLTIPLA** escolhida (respostas ficam registradas em **várias colunas** no banco de dados). Ex.: Q8_1, Q8_2, Q8_3",
                placeholder="Q8_1, Q8_2, Q8_3",
                key="processamento_unico_valores_agrup",
                help="ℹ️ Importante! Quando o Tipo de Tabela processada for MULTIPLA, o nome da variável deverá ser diferente das colunas de múltipla resposta. Ex.: Se as colunas múltiplas são 'Q8_1, Q8_2, Q8_3' então, o nome da coluna da variável que deverá constar na linha será 'Q8'."
            )
            st.write("")
            st.write("")

            Fecha_100 = st.selectbox(
                label="📝 Deseja que a tabela feche os percentuais em 100% (**contabiliza o nº de respostas**) ou, acima de 100% (**contabiliza o nº de respondentes**)?", 
                options=["NAO", "SIM"], 
                key="processamento_unico_fecha_100",
                help="ℹ️ Escolha a opção desejada se a tabela retornará os percentuais fechando 100% ou não."
            )
            st.write("")
            st.write("")

        coluna5, coluna6 = st.columns(2)
        with coluna5:
            Var_ID = st.selectbox(
                label="📝 Informe qual a **variável/coluna identificadora**, utilizada para identificar a entrevista como única", 
                options=colunas, 
                key="processamento_unico_var_id",
                help="ℹ️ Essa é a variável/coluna que identifica o respondente e não pode ter código repetido. Ex.: 'codigo_entrevistado'."
            )
        
        with coluna6:
            Var_Pond = st.selectbox(
                label="📝 Informe qual a **variável/coluna de ponderação**", 
                options=colunas, 
                key="processamento_unico_var_pond",
                help="ℹ️ Observação: se o projeto não tiver ponderação, é necessário criar uma coluna no banco de dados do projeto para representar a variável POND e preencher os campos com o nº 1."
            )
        st.write("")
        st.write("")

        Titulo = st.text_input(
            label="📝 Informe qual deverá ser o **título** da tabela processada.",
            placeholder="Título da tabela",
            key="processamento_unico_titulo",
            help="ℹ️"
        )
            
        input_buttom_submit_processamento_unico = st.form_submit_button("Enviar")

    if input_buttom_submit_processamento_unico:
        kwargs = dict(
                bd_dados=st.session_state.data,
                lista_labels=st.session_state.lista_labels,
                TipoTabela=TipoTabela,
                Var_linha=Var_linha,
                Colunas=Colunas,
                Cabecalho=Cabecalho,
                NS_NR=NS_NR,
                Var_ID=Var_ID,
                Var_Pond=Var_Pond,
                Titulo=Titulo,
            )
        qtd_bandeiras = len(Colunas)
        qtd_cabecalho = len(Cabecalho.split(", "))
        if qtd_bandeiras != qtd_cabecalho:
            st.warning("A quantidade de valores para o **Cabeçalho** deve ser a mesma quantidade para as **Bandeiras**", icon="⚠️")

        elif TipoTabela == "MULTIPLA" and Var_linha in Valores_Agrup:
            verificar_Valores_Agrup = Valores_Agrup.split(", ")
            if Var_linha in Valores_Agrup:
                st.warning("O nome da variável referente ao **nível linha** da tabela não pode ser o mesmo nome das colunas que representam a **variável MULTIPLA**", icon="⚠️")

        else:
            if TipoTabela in ("IPA_10", "IPA_5"):
                kwargs["valores_BTB"] = st.session_state.get("processamento_unico_valores_btb", "1, 2, 3")
                kwargs["valores_TTB"] = st.session_state.get("processamento_unico_valores_ttb", "8, 9, 10")

            if TipoTabela == "MULTIPLA":
                kwargs["Valores_Agrup"] = st.session_state.get("processamento_unico_valores_agrup", "Q8_1, Q8_2, Q8_3")
                kwargs["Fecha_100"] = st.session_state.get("processamento_unico_fecha_100", "SIM")

            tabela_processada, tabela_processada_front = processar_tabela(**kwargs)
            st.dataframe(tabela_processada_front, hide_index=False, use_container_width=True)

            st.write("")
            # Salvar em Excel com formatação
            excel_data = salvar_excel_unica_tabela(tabela_processada, TipoTabela=TipoTabela, Var_linha=Var_linha)
            st.download_button(
                    label="📥 Baixar tabela processada em Excel",
                    data=excel_data,
                    file_name=f'Tabela_processada.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    on_click=mensagem_sucesso
                )
            

# Função para salvar as tabelas em um único Excel com várias abas e formatação
def salvar_excel_com_formatacao(todas_tabelas_gerais, bd_processamento):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for i, tabela in enumerate(bd_processamento['Var_Linha']):
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
            worksheet.write(linha_atual, 0, f'Tabela{i} - {bd_processamento["Var_Linha"][i]}')
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

            
with tab2:
    st.write("")
    st.write("")

    st.markdown(
        """
        📄 [Documentação do Sistema em PDF](https://github.com/RaynerSantos/Processamento-Estatistico/blob/main/Documenta%C3%A7%C3%A3o%20-%20Processamento%20do%20Estat%C3%ADstico.pdf)
        
        📥 [Exemplo da Sintaxe](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fraw.githubusercontent.com%2FRaynerSantos%2FProcessamento-Estatistico%2Frefs%2Fheads%2Fupdate-solicitado-sintaxe%2FSintaxe_Exemplo.xlsx&wdOrigin=BROWSELINK)
        """,
        unsafe_allow_html=True
    )

    st.write("")
    st.write("")

    with st.spinner("Please wait..."):
        with st.expander("📅 Dicionário de variáveis:"):
            st.dataframe(st.session_state.lista_variaveis, hide_index=True, selection_mode=["multi-row", "multi-cell"])
    
        st.write("")
        st.write("")

        with st.form('sheet_name_sintaxe'):
            nome_sheet_sintaxe = st.text_input(
                label="📝 Informe o nome da aba (sheet) que contém a **Sintaxe** com os parâmetros da criação das tabelas.", 
                placeholder="Sintaxe"
                )
            with st.status("🔍 A seguir, veja uma imagem de exemplo da **Sintaxe**:"):
                st.image(image="images/Sintaxe.png")
            input_buttom_submit_sintaxe = st.form_submit_button("Enviar")

        if input_buttom_submit_sintaxe:
            st.success("Nome da aba (sheet) da planilha de **Sintaxe** foi enviado com sucesso", icon="✅")

            # Salvar o nome da aba
            st.session_state.nome_sheet_sintaxe = nome_sheet_sintaxe

        st.write('')
        data_sintaxe_file = st.file_uploader("📂 Selecione o banco de dados (em xlsx)", 
                                    type=["xlsx"], 
                                    help="Selecione o arquivo Excel contendo a Sintaxe", 
                                    key="processamento_sintaxe_uploader")

        if data_sintaxe_file is not None:
            sintaxe = pd.read_excel(data_sintaxe_file, sheet_name=st.session_state.nome_sheet_sintaxe)
            st.session_state.sintaxe = sintaxe
            st.success("Planilha carregada com sucesso!", icon="✅")

            st.write("")
            st.write("")

            # Formato do output (uma única aba ou para cada tabela processada gerar uma nova aba)
            with st.form(key='output_excel'):
                tipo_output = st.selectbox(label='Informe a opção do formato para o output desejado', options=['Única aba', 'Várias abas'])
                excel_name = st.text_input(label='Informe o nome desejado para a planilha com o output do Processamento  Estatístico')
                processar_dados = st.form_submit_button("Processar Dados")
                st.session_state.tipo_output = tipo_output
                st.session_state.excel_name = excel_name

            # Botão para processar os dados
            if processar_dados:
                with st.spinner("Please wait..."):
                    processamento_sintaxe = verificar_incosistencias_iniciais(data=st.session_state.data, 
                                                                sintaxe=st.session_state.sintaxe, 
                                                                lista_labels=st.session_state.lista_labels)
                    result_verificar_inconsistencia = processamento_sintaxe.verificar_incosistencia()
                    if result_verificar_inconsistencia != 0:
                        st.warning(result_verificar_inconsistencia)

                    else:
                        # Processar os dados e obter as tabelas
                        todas_tabelas_gerais = processamento(data=st.session_state.data, 
                                                            bd_processamento=st.session_state.sintaxe, 
                                                            lista_labels=st.session_state.lista_labels)
                        
                        if tipo_output == 'Várias abas':
                            # Salvar em Excel com formatação
                            excel_data = salvar_excel_com_formatacao(todas_tabelas_gerais, bd_processamento=st.session_state.sintaxe)
                        elif tipo_output == 'Única aba':
                            # Salvar em Excel com formatação
                            excel_data = salvar_excel_aba_unica(todas_tabelas_gerais, bd_processamento=st.session_state.sintaxe)
                        
                        # Link para download
                        st.download_button(
                            label="Baixar Excel Processado",
                            data=excel_data,
                            file_name=st.session_state.excel_name + ".xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
    
st.write('')
st.write('')
st.divider()
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg") # Expertise_Marca_VerdeEscuro_mini.jpg