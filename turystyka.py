import pandas as pd

# Wczytanie danych
df = pd.read_excel("dane.xlsx", sheet_name=9, engine="openpyxl")

id_col = df.columns[0]
value_cols = df.columns[1:]

tab_weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1, -1, -1]

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

for i in range(records.__len__()):
    if records[i][2] <= 15:
        records[i].append(1)
        continue
    elif 16 <= records[i][2] <= 21:
        records[i].append(2)
        continue
    elif 22 <= records[i][2] <= 26:
        records[i].append(3)
        continue
    elif 27 <= records[i][2] <= 32:
        records[i].append(4)
        continue
    elif 33 <= records[i][2] <= 50:
        records[i].append(5)
print(records)
# Utworzenie tabeli
tabela = pd.DataFrame(records)

# Zapis do pliku CSV
tabela.to_csv(
    "turystyka.csv",
    index=False,
    encoding="utf-8-sig",
    sep=","
)
