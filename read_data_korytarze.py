import pandas as pd

# Wczytanie danych
df_korytarze = pd.read_excel(
    "dane.xlsx",
    sheet_name=6,
    engine="openpyxl"
)

df_wyniki = pd.read_csv("wyniki_korytarze531.csv")


# Zostawiamy dane korytarzy jako tabelę bazową
df_all = df_korytarze.copy()


# Dołączamy wynik na podstawie identyfikatora Name
df_all = df_all.merge(
    df_wyniki[["Name", df_wyniki.columns[2]]].rename(
        columns={df_wyniki.columns[2]: "wynik"}
    ),
    on="Name",
    how="left"
)


print(df_all)


# Zapis
df_all.to_csv(
    "dane_do_uczenia_korytarze.csv",
    index=False,
    encoding="utf-8-sig",
    sep=","
)