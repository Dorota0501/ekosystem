import pandas as pd



def przedzialy(value, nazwa, wagi):
    value = [value]
    if nazwa == "ekosystem_LS" and wagi == 321:
        if value[0] <= 300:
            value.append("zly")
        elif 300 < value[0] <= 334:
            value.append("slaby")
        elif 334 < value[0] <= 365:
            value.append("umiarkowany")
        elif 365 < value[0] <= 406:
            value.append("dobry")
        elif value[0] > 406:
            value.append("bardzo dobry")
    elif nazwa == "ekosystem_NL" and wagi == 321:
        if value[0] <= 217:
            value.append("zly")
        elif 217 < value[0] <= 272:
            value.append("slaby")
        elif 272 < value[0] <= 313:
            value.append("umiarkowany")
        elif 313 < value[0] <= 375:
            value.append("dobry")
        elif value[0] > 375:
            value.append("bardzo dobry")
    elif nazwa == "ekosystem_LS" and wagi == 531:
        if value[0] <= 422:
            value.append("zly")
        elif 422 < value[0] <= 469:
            value.append("slaby")
        elif 469 < value[0] <= 511:
            value.append("umiarkowany")
        elif 511 < value[0] <= 565:
            value.append("dobry")
        elif value[0] > 565:
            value.append("bardzo dobry")
    elif nazwa == "ekosystem_NL" and wagi == 531:
        if value[0] <= 264:
            value.append("zly")
        elif 264 < value[0] <= 360:
            value.append("slaby")
        elif 360 < value[0] <= 434:
            value.append("umiarkowany")
        elif 434 < value[0] <= 544:
            value.append("dobry")
        elif value[0] > 544:
            value.append("bardzo dobry")
    return value


def read_to_dictionary(pd_table):
    dictionary = {}
    for row_idx, row in pd_table.iterrows():
        record_name = row['0']
        record_value = [row['1'], row['4']]
        dictionary[record_name] = record_value
    return dictionary


# Odczyt danych z pliku CSV
tabela_woda321 = pd.read_csv("woda321.csv", sep=",", encoding="utf-8-sig")
tabela_woda531 = pd.read_csv("woda531.csv", sep=",", encoding="utf-8-sig")
tabela_rosliny321 = pd.read_csv("rosliny321.csv", sep=",", encoding="utf-8-sig")
tabela_rosliny531 = pd.read_csv("rosliny531.csv", sep=",", encoding="utf-8-sig")
tabela_ssaki321 = pd.read_csv("ssaki321.csv", sep=",", encoding="utf-8-sig")
tabela_ssaki531 = pd.read_csv("ssaki531.csv", sep=",", encoding="utf-8-sig")
tabela_ptaki321 = pd.read_csv("ptaki321.csv", sep=",", encoding="utf-8-sig")
tabela_ptaki531 = pd.read_csv("ptaki531.csv", sep=",", encoding="utf-8-sig")
tabela_bezkregowce321 = pd.read_csv("bezkregowce321.csv", sep=",", encoding="utf-8-sig")
tabela_bezkregowce531 = pd.read_csv("bezkregowce531.csv", sep=",", encoding="utf-8-sig")

dict_woda321 = read_to_dictionary(tabela_woda321)
dict_woda531 = read_to_dictionary(tabela_woda531)

dict_rosliny321 = read_to_dictionary(tabela_rosliny321)
dict_rosliny531 = read_to_dictionary(tabela_rosliny531)

dict_ssaki321 = read_to_dictionary(tabela_ssaki321)
dict_ssaki531 = read_to_dictionary(tabela_ssaki531)

dict_ptaki321 = read_to_dictionary(tabela_ptaki321)
dict_ptaki531 = read_to_dictionary(tabela_ptaki531)

dict_bezkregowce321 = read_to_dictionary(tabela_bezkregowce321)
dict_bezkregowce531 = read_to_dictionary(tabela_bezkregowce531)

df_udzial_lasu = pd.read_excel("Udzial_lasu.xlsx", sheet_name=0, engine="openpyxl")
LS_dict = {}
for row_idx, row in df_udzial_lasu.iterrows():
    record_name = row['Name']
    record_value = row['LS/NL']
    LS_dict[record_name] = record_value


def oblicz_wynik(oczko, ls_nl, wagi):
    if wagi == 321:
        woda = dict_woda321[oczko]
        rosliny = dict_rosliny321[oczko]
        ptaki = dict_ptaki321[oczko]
        ssaki = dict_ssaki321[oczko]
        bezkregowce = dict_bezkregowce321[oczko]
        if ls_nl == 'LS':
            suma = woda[0] + rosliny[0] + ptaki[0] + ssaki[0] + bezkregowce[0]
            wynik = przedzialy(suma, 'ekosystem_LS', 321)
        elif ls_nl == 'NL':
            suma = woda[1] + rosliny[1] + ptaki[1] + ssaki[1] + bezkregowce[1]
            wynik = przedzialy(suma, 'ekosystem_NL', 321)
    elif wagi == 531:
        woda = dict_woda531[oczko]
        rosliny = dict_rosliny531[oczko]
        ptaki = dict_ptaki531[oczko]
        ssaki = dict_ssaki531[oczko]
        bezkregowce = dict_bezkregowce531[oczko]
        if ls_nl == 'LS':
            suma = woda[0] + rosliny[0] + ptaki[0] + ssaki[0] + bezkregowce[0]
            wynik = przedzialy(suma, 'ekosystem_LS', 531)
        elif ls_nl == 'NL':
            suma = woda[1] + rosliny[1] + ptaki[1] + ssaki[1] + bezkregowce[1]
            wynik = przedzialy(suma, 'ekosystem_NL', 531)
    return [oczko, wynik]


wynik = []
for key in LS_dict.keys():
    wynik.append(oblicz_wynik(key, LS_dict[key], 531))

wyniki = pd.DataFrame(wynik)
wyniki.to_csv(
    "wyniki531.csv",
    index=False,
    encoding="utf-8-sig",
    sep=","
)
