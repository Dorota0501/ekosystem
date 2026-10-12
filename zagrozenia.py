import pandas as pd

# Wczytanie danych
df = pd.read_excel("dane.xlsx", sheet_name=8, engine="openpyxl")

id_col = df.columns[0]
value_cols = df.columns[1:]

tab_weights = [5, 5, 5, 5, 5, 5, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1]
records = []


df_udzial_lasu = pd.read_excel("Udzial_lasu.xlsx", sheet_name=0, engine="openpyxl")
LS_dict = {}
for row_idx, row in df_udzial_lasu.iterrows():
    record_name = row['Name']
    record_value = row['LS/NL']
    LS_dict[record_name] = record_value

def przedzialy(value, LS_NL):
    value = [value]
    if LS_NL == 'LS':
        if value[0] <= 28:
            value.append(1)
        elif 29 <= value[0] <= 35:
            value.append(2)
        elif 36 <= value[0] <= 44:
            value.append(3)
        elif 45 <= value[0] <= 55:
            value.append(4)
        elif value[0] > 55:
            value.append(5)
    elif LS_NL == 'NL':
        if value[0] <= 36:
            value.append(1)
        elif 37 <= value[0] <= 47:
            value.append(2)
        elif 48 <= value[0] <= 58:
            value.append(3)
        elif 59 <= value[0] <= 71:
            value.append(4)
        elif value[0] > 71:
            value.append(5)
    return value


for row_idx, row in df.iterrows():
    record_LS = []
    record_NL = []
    i = 0
    record_name = row['Name']
    for col_name in value_cols:
        value = row[col_name]
        weight = tab_weights[i]
        i += 1
        if weight != 0:
            if col_name.__contains__("LS"):
                record_LS.append(value * weight)
            elif col_name.__contains__("NL"):
                record_NL.append(value * weight)
    redord_sumaLS = sum(record_LS)
    redord_sumaNL = sum(record_NL)
    record_ls = przedzialy(redord_sumaLS, "LS")
    record_nl = przedzialy(redord_sumaNL, "NL")
    if LS_dict[record_name] == 'LS':
        records.append([record_name, record_ls])
    elif LS_dict[record_name] == 'NL':
        records.append([record_name, record_nl])
print(records)



print(records)
# Utworzenie tabeli
tabela = pd.DataFrame(records)

# Zapis do pliku CSV
tabela.to_csv(
    "zagrozenia.csv",
    index=False,
    encoding="utf-8-sig",
    sep=","
)
