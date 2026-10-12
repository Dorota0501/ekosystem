import pandas as pd

# Wczytanie danych
df = pd.read_excel("dane.xlsx", sheet_name=7, engine="openpyxl")

id_col = df.columns[0]
value_cols = df.columns[1:]

tab_weights = [2, 1, 1, 5]

records = []

for row_idx, row in df.iterrows():
    record = []
    i = 0
    record_name = row['Name']
    for col_name in value_cols:
        value = row[col_name]
        weight = tab_weights[i]
        i += 1
        if weight != 0:
            record.append(value * weight)
    redord_suma = sum(record)
    records.append([record_name, record, redord_suma])

print(records)

for i in range(records.__len__()):
    if records[i][2] <= 20:
        records[i].append(1)
        continue
    elif 21 <= records[i][2] <= 26:
        records[i].append(2)
        continue
    elif 27 <= records[i][2] <= 31:
        records[i].append(3)
        continue
    elif 32 <= records[i][2] <= 36:
        records[i].append(4)
        continue
    elif 37 <= records[i][2] <= 45:
        records[i].append(5)

print(records)
# Utworzenie tabeli
tabela = pd.DataFrame(records)

# Zapis do pliku CSV
tabela.to_csv(
    "ocena_krajobrazu.csv",
    index=False,
    encoding="utf-8-sig",
    sep=","
)
