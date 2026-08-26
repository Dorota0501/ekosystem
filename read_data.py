# plik do odczytywania danych do jednego data frame
import pandas as pd

# Wczytanie danych
df_woda = pd.read_excel("dane.xlsx", sheet_name=1, engine="openpyxl")
df_rosliny = pd.read_excel("dane.xlsx", sheet_name=2, engine="openpyxl")
df_ptaki = pd.read_excel("dane.xlsx", sheet_name=3, engine="openpyxl")
df_ssaki = pd.read_excel("dane.xlsx", sheet_name=4, engine="openpyxl")
df_bezkregowce = pd.read_excel("dane.xlsx", sheet_name=5, engine="openpyxl")
df_wyniki = pd.read_csv("wyniki321.csv")

id_col = df_woda.columns[0]
value_cols = df_woda.columns[1:]

id_col_rosliny = df_rosliny.columns[0]
value_cols_rosliny = df_rosliny.columns[1:]

id_col_ptaki = df_ptaki.columns[0]
value_cols_ptaki = df_ptaki.columns[1:]

id_col_ssaki = df_ssaki.columns[0]
value_cols_ssaki = df_ssaki.columns[1:]

id_col_bezkregowce = df_bezkregowce.columns[0]
value_cols_bezkregowce = df_bezkregowce.columns[1:]

df_all = pd.DataFrame
df_all = df_woda
i = -1
for row_idx, row in df_all.iterrows():
    record_name = row['Name']
    i += 1
    for row_idx1, row1 in df_rosliny.iterrows():
        if record_name == row1['Name']:
            df_all.loc[i, value_cols_rosliny[0:30]] = row1.values[1:31]
            break
    for row_idx1, row1 in df_ptaki.iterrows():
        if record_name == row1['Name']:
            df_all.loc[i, value_cols_ptaki[0:30]] = row1.values[1:31]
            break

    for row_idx1, row1 in df_ssaki.iterrows():
        if record_name == row1['Name']:
            df_all.loc[i, value_cols_ssaki[0:30]] = row1.values[1:31]
            break

    for row_idx1, row1 in df_bezkregowce.iterrows():
        if record_name == row1['Name']:
            df_all.loc[i, value_cols_bezkregowce[0:30]] = row1.values[1:31]
            break

    for row_idx1, row1 in df_wyniki.iterrows():
        if record_name == row1['Name']:
            df_all.loc[i, "wynik"] = row1.values[2]
print(df_all)
df_all.to_csv("dane_do_uczenia.csv",
              index=False,
              encoding="utf-8-sig",
              sep=",")
