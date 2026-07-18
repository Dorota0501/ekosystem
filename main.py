import pandas as pd

# Wczytanie danych
df = pd.read_excel("dane.xlsx", sheet_name=4, engine="openpyxl")

id_col = df.columns[0]
value_cols = df.columns[1:]

tab_weights = []


def get_weight(col_name) -> float:
    if not isinstance(col_name, str):
        return 0
    if "R1" in col_name:
        return 1
    elif "R2" in col_name:
        return 3
    elif "R3" in col_name:
        return 5
    return 0

records = []
for row_idx, row in df.iterrows():
    record = []
    record_name = [row['Name']]
    for col_name in value_cols:
        value = row[col_name]
        weight = get_weight(col_name)
        if weight != 0:
            record.append(value * weight)
        #record["values"][col_name] = {"value": value, "weight": weight}
    record = record_name + record
    record.append(sum(record[1:]))
    if record[-1] <= 81:
        record.append("zly")
    elif 81 < record[-1] <= 117:
        record.append("slaby")
    elif 117 < record[-1] <= 153:
        record.append("umiarkowany")
    elif 153 < record[-1] <= 189:
        record.append("dobry")
    elif record[-1] > 189:
        record.append("bardzo dobry")

    records.append(record)
# Stworzenie nowej tabeli (DataFrame) z wszystkich danych

# Utworzenie tabeli
tabela = pd.DataFrame(records)

# Zapis do pliku CSV
tabela.to_csv(
    "ptaki1.csv",
    index=False,
    encoding="utf-8-sig",
    sep=","
)