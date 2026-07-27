import pandas as pd

# Odczyt danych z pliku CSV
tabela_woda = pd.read_csv(
    "woda.csv",
    sep=",",
    encoding="utf-8-sig"
)

tabela_rosliny = pd.read_csv(
    "rosliny.csv",
    sep=",",
    encoding="utf-8-sig"
)

tabela_ssaki = pd.read_csv(
    "ssaki.csv",
    sep=",",
    encoding="utf-8-sig"
)

tabela_ptaki = pd.read_csv(
    "ptaki.csv",
    sep=",",
    encoding="utf-8-sig"
)

tabela_bezkregowce = pd.read_csv(
    "bezkregowce.csv",
    sep=",",
    encoding="utf-8-sig"
)
wyniki = []
suma_woda = 0
for i in range(tabela_woda.__len__() - 1):
    zly = 0
    slaby = 0
    umiarkowany = 0
    dobry = 0
    bardzo_dobry = 0

    print(tabela_woda.columns)
    # woda

    # popraw średnią
    # sprawdź wyniki dla wag 1,2,3
    # XGBoost
    # KNN, Sieci głębokie
    suma_woda_LS = tabela_woda.loc[i + 1]["31"]
    suma_woda_NL = tabela_woda.loc[i + 1]["31"]
    if tabela_woda.loc[i + 1]["32"] == 0:
        zly += 1
    elif tabela_woda.loc[i + 1]["32"] == 1:
        slaby += 1
    elif tabela_woda.loc[i + 1]["32"] == 2:
        umiarkowany += 1
    elif tabela_woda.loc[i + 1]["32"] == 3:
        dobry += 1
    elif tabela_woda.loc[i + 1]["32"] == 4:
        bardzo_dobry += 1

    # rosliny
    suma_rosliny = tabela_rosliny.loc[i + 1]["31"]
    if tabela_rosliny.loc[i + 1]["32"] == 0:
        zly += 1
    elif tabela_rosliny.loc[i + 1]["32"] == 1:
        slaby += 1
    elif tabela_rosliny.loc[i + 1]["32"] == 2:
        umiarkowany += 1
    elif tabela_rosliny.loc[i + 1]["32"] == 3:
        dobry += 1
    elif tabela_rosliny.loc[i + 1]["32"] == 4:
        bardzo_dobry += 1

    # ssaki
    suma_ssaki = tabela_ssaki.loc[i + 1]["31"]
    if tabela_ssaki.loc[i + 1]["32"] == 0:
        zly += 1
    elif tabela_ssaki.loc[i + 1]["32"] == 1:
        slaby += 1
    elif tabela_ssaki.loc[i + 1]["32"] == 2:
        umiarkowany += 1
    elif tabela_ssaki.loc[i + 1]["32"] == 3:
        dobry += 1
    elif tabela_ssaki.loc[i + 1]["32"] == 4:
        bardzo_dobry += 1

    # ptaki
    suma_ptaki = tabela_ptaki.loc[i + 1]["31"]
    if tabela_ptaki.loc[i + 1]["32"] == 0:
        zly += 1
    elif tabela_ptaki.loc[i + 1]["32"] == 1:
        slaby += 1
    elif tabela_ptaki.loc[i + 1]["32"] == 2:
        umiarkowany += 1
    elif tabela_ptaki.loc[i + 1]["32"] == 3:
        dobry += 1
    elif tabela_ptaki.loc[i + 1]["32"] == 4:
        bardzo_dobry += 1

    # bezkregowce
    suma_bezkregowce = tabela_bezkregowce.loc[i + 1]["31"]
    if tabela_bezkregowce.loc[i + 1]["32"] == 0:
        zly += 1
    elif tabela_bezkregowce.loc[i + 1]["32"] == 1:
        slaby += 1
    elif tabela_bezkregowce.loc[i + 1]["32"] == 2:
        umiarkowany += 1
    elif tabela_bezkregowce.loc[i + 1]["32"] == 3:
        dobry += 1
    elif tabela_bezkregowce.loc[i + 1]["32"] == 4:
        bardzo_dobry += 1

    suma = suma / 5
    wynik = ""
    if suma <= 81:
        wynik = "zly"
    elif 81 < suma <= 117:
        wynik = "slaby"
    elif 117 < suma <= 153:
        wynik = "umiarkowany"
    elif 153 < suma <= 189:
        wynik = "dobry"
    elif suma > 189:
        wynik = "bardzo dobry"

    wyniki.append([tabela_bezkregowce.loc[i + 1]["0"],suma, wynik])
    lista = [zly, slaby, umiarkowany, dobry, bardzo_dobry]

    # indeks = lista.index(max(lista))
    # if indeks == 0:
    #     w = "zly"
    # elif indeks == 1:
    #     w = "slaby"
    # elif indeks == 2:
    #     w ="umiarkowany"
    # elif indeks == 3:
    #     w = "dobry"
    # elif indeks == 4:
    #     w = "bardzo dobry"
    # wyniki.append(w)

# Wyświetlenie tabeli

wynik = pd.DataFrame(wyniki)
wynik.to_csv(
    "wyniki_srednia.csv",
    index=False,
    encoding="utf-8-sig",
    sep=","
)
