import pandas as pd
import numpy as np

df = pd.DataFrame({
    "Label": ["Empresa 1", "Empresa 1", "Empresa 1", "Empresa 2", "Empresa 2", "Empresa 3"],
    "Codigo": [1, 1, 2, 2, 2, 3]
})
print("\ndf:\n", df)

mapping_de_para = dict(zip(df['Label'], df['Codigo']))
print("\nDe-Para", mapping_de_para)

lista_verif = []
for k, v in mapping_de_para.items():
    if v in lista_verif:
        print("Verificar correspondência entre códigos e labels")
    lista_verif.append(v)

print("\nlista_verif: ", lista_verif)

variavel = 'Q8'
valores_agrup = 'Q8_1, Q8_2, Q8_3'
valores_agrup = valores_agrup.split(", ")
if variavel in valores_agrup:
    print(f"\n\n {variavel} está em {valores_agrup}")

