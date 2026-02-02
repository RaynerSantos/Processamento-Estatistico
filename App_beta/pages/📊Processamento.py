import pandas as pd
import numpy as np
from regex import F
import streamlit as st
from io import BytesIO
from collections import Counter
from utils import ordenar_labels, ordenar_labels_multipla, ordenar_valores, classificar_nps, funcao_agrupamento, classificar_satis
from metodos import processar_tabela, mensagem_sucesso

# Função para salvar as tabelas em um único Excel com única aba
def salvar_excel_aba_unica(tabelas, TipoTabela, Var_linha):
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

with st.spinner("Please wait..."):
    with st.expander("📅 Dicionário de variáveis:"):
        st.dataframe(st.session_state.lista_variaveis, hide_index=True, selection_mode=["multi-row", "multi-cell"])

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
        "Use quando a variável da **linha** for **numérica** e você quer agrupar as notas em faixas **BTB** e **TTB** (ex.: notas baixas vs. notas altas) para facilitar a leitura."
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
coluna1, coluna2 = st.columns(2, border=True)
with st.form('parametros_gerar_tabela_processada'):
    with coluna1:
        TipoTabela = st.selectbox(
            label="📝 Informe o **tipo da tabela** a ser processada", 
            options=dict_tipo_tabela.keys(), 
            key="processamento_unico_TipoTabela",
            help="ℹ️ Tipo de tabela = como a variável que ficará na **linha** deve ser interpretada e exibida. Ela pode ser: **categórica** (SIMPLES), **Likert 5 pontos** (IPA_5), **numérica para BTB/TTB** (IPA_10), **NPS** (NPS) ou **múltipla escolha** (MULTIPLA)."
            )
        with st.status("ℹ️ Informação do Tipo da Tabela Selecionada"):
            st.write(f"**{TipoTabela}**: {dict_tipo_tabela[TipoTabela]}")
    
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
        

    # coluna3, coluna4 = st.columns(2, border=True)    
    Colunas = st.multiselect(
        label="📝 Informe as **bandeiras** que deverão representar as colunas da tabela processada", 
        options=colunas, 
        key="processamento_unico_Colunas",
        help="ℹ️ As bandeiras são simplesmente as variáveis que constará nas colunas da tabela processada."
        )
    st.write("")
    
    Cabecalho = st.text_input(
        label="📝 Informe o **cabeçalho** desejado que substituará os nomes das colunas na tabela. **Coloque o cabeçalho separado por vírgula e espaço (, )**", 
        placeholder="Mercado PME, Mercado 500+, TIM, TIM PME, TIM 500+, TIM Prime, VIVO, VIVO PME, VIVO 500+, CLARO, CLARO PME, CLARO 500+", 
        key="processamento_unico_cabecalho",
        help="ℹ️ O cabeçalho é o nome ideal das colunas que você deseja que apareça na tabela processada. Ex.: nome da coluna: **Q3** → nome do cabeçalho para esta coluna: **Setor de atividade**."
        )
    st.write("")
    
    NS_NR = st.selectbox(
        label="📝 Deseja que a tabela contabilize os casos de **NS/NR (Não sabe / Não respondeu)**?", 
        options=["NAO", "SIM"], 
        key="processamento_unico_ns_nr",
        help="ℹ️ Escolha a opção desejada se a tabela retornará os percentuais de NS/NR ou não."
        )
    st.write("")
    
    if TipoTabela == "IPA_10" or TipoTabela == "IPA_5":
        coluna3, coluna4 = st.columns(2, border=True)
        with coluna3:
            valores_BTB = st.text_input(
            label="📝 Informe a **faixa de notas BTB** - notas baixas desejada. **Coloque os valores separados por vírgula e espaço (, )**", 
            placeholder="1, 2, 3", 
            key="processamento_unico_valores_btb",
            help="ℹ️ Agrupamento de notas baixas."
            )

        with coluna4:
            valores_TTB = st.text_input(
                label="📝 Informe a **faixa de notas TTB** - notas altas desejada. **Coloque os valores separados por vírgula e espaço (, )**", 
                placeholder="8, 9, 10", 
                key="processamento_unico_valores_ttb",
                help="ℹ️ Agrupamento de notas altas."
            )
        
    if TipoTabela == "MULTIPLA":
        Valores_Agrup = st.text_input(
            label="📝 Informe quais as **variáveis/colunas representam a variável MÚLTIPLA** escolhida (respostas ficam registradas em **várias colunas** no banco de dados). Ex.: Q8_1, Q8_2, Q8_3",
            placeholder="Q8_1, Q8_2, Q8_3",
            key="processamento_unico_valores_agrup",
            help="ℹ️ Importante! Quando o Tipo de Tabela processada for MULTIPLA, o nome da variável deverá ser diferente das colunas de múltipla resposta. Ex.: Se as colunas múltiplas são 'Q8_1, Q8_2, Q8_3' então, o nome da coluna da variável que deverá constar na linha será 'Q8'."
        )

        Fecha_100 = st.selectbox(
            label="📝 Deseja que a tabela feche os percentuais em 100% (**contabiliza o nº de respostas**) ou, acima de 100% (**contabiliza o nº de respondentes**)?", 
            options=["NAO", "SIM"], 
            key="processamento_unico_fecha_100",
            help="ℹ️ Escolha a opção desejada se a tabela retornará os percentuais fechando 100% ou não."
        )
        st.write("")

    coluna5, coluna6 = st.columns(2, border=True)
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
    if TipoTabela in ("IPA_10", "IPA_5"):
        kwargs["valores_BTB"] = st.session_state.get("processamento_unico_valores_btb", "1, 2, 3")
        kwargs["valores_TTB"] = st.session_state.get("processamento_unico_valores_ttb", "8, 9, 10")

    if TipoTabela == "MULTIPLA":
        kwargs["Valores_Agrup"] = st.session_state.get("processamento_unico_valores_agrup", "Q8_1, Q8_2, Q8_3")
        kwargs["Fecha_100"] = st.session_state.get("processamento_unico_fecha_100", "SIM")

    tabela_processada = processar_tabela(**kwargs)
    st.dataframe(tabela_processada, hide_index=False)

    st.write("")
    # Salvar em Excel com formatação
    excel_data = salvar_excel_aba_unica(tabela_processada, TipoTabela=TipoTabela, Var_linha=Var_linha)
    st.download_button(
            label="📥 Baixar tabela processada em Excel",
            data=excel_data,
            file_name=f'Tabela_processada.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            on_click=mensagem_sucesso
        )
    
st.write('')
st.write('')
st.divider()
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg", width="content") # Expertise_Marca_VerdeEscuro_mini.jpg