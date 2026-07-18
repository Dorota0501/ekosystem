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
for i in range(tabela_woda.__len__() - 1):
    zly = 0
    slaby = 0
    umiarkowany = 0
    dobry = 0
    bardzo_dobry = 0

    print(tabela_woda.columns)
    # woda
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

    lista = [zly, slaby, umiarkowany, dobry, bardzo_dobry]
    lista_sr = [zly, slaby * 2, umiarkowany * 3, dobry * 4, bardzo_dobry * 5]
    wynik_sr = sum(lista_sr) / 5
    if wynik_sr <= 1.5:
        w = "zly"
    elif 1.5 <= wynik_sr < 2.5:
        w = "slaby"
    elif 2.5 <= wynik_sr < 3.5:
        w = "umiarkowany"
    elif 3.5 <= wynik_sr < 4.5:
        w = "dobry"
    elif wynik_sr > 4.5:
        w = "bardzo dobry"

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
    wyniki.append([tabela_woda.loc[i + 1]["0"], w])
    # wyniki.append(w)
# Wyświetlenie tabeli

wynik = pd.DataFrame(wyniki)
wynik.to_csv(
    "wyniki_srednia.csv",
    index=False,
    encoding="utf-8-sig",
    sep=","
)
