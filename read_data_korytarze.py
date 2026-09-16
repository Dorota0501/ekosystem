import pandas as pd

df_korytarze = pd.read_excel("dane.xlsx", sheet_name=6, engine="openpyxl")
df_wyniki = pd.read_csv("wyniki_korytarze321.csv")

id_col = df_korytarze.columns[0]
value_cols = df_korytarze.columns[1:]

df_all = pd.DataFrame
df_all = df_korytarze
i = -1
for row_idx, row in df_korytarze.iterrows():
    record_name = row['Name']
    i += 1
    for row_idx1, row1 in df_wyniki.iterrows():
        if record_name == row1['Name']:
            df_all.loc[i, "wynik"] = row1.values[2]
            break

print(df_all)
df_all.to_csv("dane_do_uczenia_korytarze.csv",
              index=False,
              encoding="utf-8-sig",
              sep=",")
