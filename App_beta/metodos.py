import pandas as pd
import numpy as np
from io import BytesIO

# Função para converter DataFrame em arquivo Excel para download
def to_excel(df: pd.DataFrame, lista_de_labels: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="BD_CODIGOS")
        lista_de_labels.to_excel(writer, index=False, sheet_name="Lista de Labels")
    output.seek(0)  # volta pro início do buffer
    return output.getvalue()

COLUNAS_SELECIONADAS = ['SEXO', 'REG_POND']
COL_NAME = 'SEXO_REG'
def criar_bandeira(data, lista_labels, COLUNAS_SELECIONADAS, COL_NAME):
    # Criar a nova coluna de bandeira combinada
    if COL_NAME in data.columns:
        raise ValueError(f"A coluna '{COL_NAME}' já existe no DataFrame.")
    else:
        data[COL_NAME] = data[COLUNAS_SELECIONADAS].astype(str).agg(' - '.join, axis=1)

        # Criar um dicionário para mapear os códigos para labels
        dict_nova_bandeira = {'Coluna': [], 'Codigo': [], 'Label': []}
        for i, valor in enumerate(sorted(data[COL_NAME].unique())):
            dict_nova_bandeira['Coluna'].append(COL_NAME)
            dict_nova_bandeira['Codigo'].append(i + 1)

            # Obter os labels correspondentes para cada parte da combinação
            col_1label = lista_labels.loc[(lista_labels['Coluna'] == COLUNAS_SELECIONADAS[0]) & (lista_labels['Codigo'] == int(valor.split(' - ')[0])), 'Label'].values[0]
            col_2label = lista_labels.loc[(lista_labels['Coluna'] == COLUNAS_SELECIONADAS[1]) & (lista_labels['Codigo'] == int(valor.split(' - ')[1])), 'Label'].values[0]

            combined_label = f"{col_1label} - {col_2label}"
            dict_nova_bandeira['Label'].append(combined_label)

        # Adicionar os novos labels à lista_labels
        lista_labels_nova = pd.DataFrame(dict_nova_bandeira)
        lista_labels = pd.concat([lista_labels, lista_labels_nova], axis=0, ignore_index=True)

        # Mapear os códigos na nova coluna
        codigo_map = {valor: i + 1 for i, valor in enumerate(sorted(data[COL_NAME].unique()))}
        data[COL_NAME] = data[COL_NAME].map(codigo_map)

        return data, lista_labels
    

# Criar uma função para fazer um recode simples baseado em uma coluna e um mapeamento fornecido
# def recode_variavel(data, lista_labels, COLUNA_RECODE, NOVA_BANDEIRA, mapping):
#     if NOVA_BANDEIRA in data.columns:
#         raise ValueError(f"A coluna '{NOVA_BANDEIRA}' já existe no DataFrame.")
#     else:
#         data[NOVA_BANDEIRA] = np.nan

#         # Aplicar o mapeamento para criar a nova bandeira
#         for codigo_original, codigo_novo in mapping.items():
#             data.loc[data[COLUNA_RECODE] == codigo_original, NOVA_BANDEIRA] = codigo_novo

#         # Criar os labels para a nova bandeira
#         dict_nova_bandeira = {'Coluna': [], 'Codigo': [], 'Label': []}
#         for codigo_novo in sorted(mapping.values()):
#             dict_nova_bandeira['Coluna'].append(NOVA_BANDEIRA)
#             dict_nova_bandeira['Codigo'].append(codigo_novo)

#             # Obter o label correspondente do código original
#             codigo_original = [k for k, v in mapping.items() if v == codigo_novo][0]
#             label_original = lista_labels.loc[(lista_labels['Coluna'] == COLUNA_RECODE) & (lista_labels['Codigo'] == codigo_original), 'Label'].values[0]

#             dict_nova_bandeira['Label'].append(label_original)

#         # Adicionar os novos labels à lista_labels
#         lista_labels_nova = pd.DataFrame(dict_nova_bandeira)
#         lista_labels = pd.concat([lista_labels, lista_labels_nova], axis=0, ignore_index=True)

#         return data, lista_labels

# Criar uma função para fazer um recode simples baseado em uma coluna e um mapeamento fornecido
def recode_variavel(data, lista_labels, COLUNA_ORIGINAL, NOVA_BANDEIRA, dataframe_recode):
    if NOVA_BANDEIRA in data.columns:
        raise ValueError(f"A coluna '{NOVA_BANDEIRA}' já existe no DataFrame.")
    else:
        data[NOVA_BANDEIRA] = np.nan

    # Criar o mapping (de-para) a partir do dataframe de recode
    mapping_de_para = dict(zip(dataframe_recode['Codigo'], dataframe_recode['Codigo_novo']))
    mapping_de_para

    # Aplicar o mapeamento para criar a nova bandeira
    for codigo_original, codigo_novo in mapping_de_para.items():
        data.loc[data[COLUNA_ORIGINAL] == codigo_original, NOVA_BANDEIRA] = codigo_novo

    # Criar a mini lista de labels para a nova variável
    mapping_lista_labels = dict(zip(dataframe_recode['Codigo_novo'], dataframe_recode['Label_novo']))

    novo_recode = {
        'Coluna': [],
        'Codigo': [],
        'Label': []
    }

    for codigo, label in mapping_lista_labels.items():
        novo_recode['Coluna'].append(NOVA_BANDEIRA)
        novo_recode['Codigo'].append(codigo)
        novo_recode['Label'].append(label)

    lista_labels = pd.concat([lista_labels, pd.DataFrame(novo_recode)], axis=0, ignore_index=True)
    return data, lista_labels


if __name__ == "__main__":
    # Teste da função criar_bandeira e fazer recode
    data_file = r'C:\Users\rayner.santos\Downloads\Consistencia e Processamento\BD_CNP_Recall de campanha_v12.xlsx'
    data = pd.read_excel(data_file, sheet_name='Códigos')
    lista_labels = pd.read_excel(data_file, sheet_name='Variáveis Labels')
    lista_labels = lista_labels.iloc[1:, :].copy()
    lista_labels.columns = ['Coluna', 'Codigo', 'Label']
    lista_labels["Coluna"] = lista_labels["Coluna"].ffill().str.strip()

    # data, lista_labels = criar_bandeira(data, lista_labels)

    # print(data[['SEXO', 'REG_POND', 'SEXO_REG']].head(), "\n")
    # print(data['SEXO_REG'].value_counts(), "\n")
    # print(lista_labels[lista_labels['Coluna'] == 'SEXO_REG'], "\n") 

    data, lista_labels = recode_variavel(
        data, lista_labels, 'Q7', 'NOVA_BANDEIRA', {1: 12, 2: 12, 3: 12, 4: 12, 5: 10, 6: 9, 7: 8, 8: 4, 9: 12, 10: 12, 11: 12, 13: 2, 14: 12, 15: 12, 16: 5, 17: 12, 18: 12, 19: 3, 20: 11, 21: 7, 22: 12, 23: 12 , 24: 6, 25: 1, 26: 12, 27: 12})

    print(data[['Q7', 'NOVA_BANDEIRA']], "\n")
    print(data['NOVA_BANDEIRA'].value_counts(), "\n")
    print(lista_labels[lista_labels['Coluna'] == 'NOVA_BANDEIRA'], "\n")
    print("Tamanho lista_labels:", len(lista_labels[lista_labels['Coluna'] == 'NOVA_BANDEIRA']))
