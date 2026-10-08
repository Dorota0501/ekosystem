import pandas as pd

# Wczytanie danych
df_woda = pd.read_excel("dane.xlsx", sheet_name=1, engine="openpyxl")
df_rosliny = pd.read_excel("dane.xlsx", sheet_name=2, engine="openpyxl")
df_ptaki = pd.read_excel("dane.xlsx", sheet_name=3, engine="openpyxl")
df_ssaki = pd.read_excel("dane.xlsx", sheet_name=4, engine="openpyxl")
df_bezkregowce = pd.read_excel("dane.xlsx", sheet_name=5, engine="openpyxl")
df_wyniki = pd.read_csv("wyniki_cennosc531.csv")

# Zostawiamy Name + pierwsze 30 zmiennych
df_rosliny = df_rosliny.iloc[:, :31]
df_ptaki = df_ptaki.iloc[:, :31]
df_ssaki = df_ssaki.iloc[:, :31]
df_bezkregowce = df_bezkregowce.iloc[:, :31]

# Rozpoczynamy od tabeli woda
df_all = df_woda.copy()

# Łączenie po identyfikatorze Name
df_all = df_all.merge(
    df_rosliny,
    on="Name",
    how="left"
)

df_all = df_all.merge(
    df_ptaki,
    on="Name",
    how="left"
)

df_all = df_all.merge(
    df_ssaki,
    on="Name",
    how="left"
)

df_all = df_all.merge(
    df_bezkregowce,
    on="Name",
    how="left"
)

# Wynik
df_all = df_all.merge(
    df_wyniki[["Name", df_wyniki.columns[2]]].rename(
        columns={df_wyniki.columns[2]: "wynik"}
    ),
    on="Name",
    how="left"
)

print(df_all)

df_all.to_csv(
    "dane_do_uczenia.csv",
    index=False,
    encoding="utf-8-sig"
)
