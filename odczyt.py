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
        if value[0] <= 520:
            value.append("zly")
        elif 520 < value[0] <= 587:
            value.append("slaby")
        elif 587 < value[0] <= 646:
            value.append("umiarkowany")
        elif 646 < value[0] <= 717:
            value.append("dobry")
        elif value[0] > 717:
            value.append("bardzo dobry")
    elif nazwa == "ekosystem_NL" and wagi == 531:
        if value[0] <= 440:
            value.append("zly")
        elif 440 < value[0] <= 514:
            value.append("slaby")
        elif 514 < value[0] <= 579:
            value.append("umiarkowany")
        elif 579 < value[0] <= 658:
            value.append("dobry")
        elif value[0] > 658:
            value.append("bardzo dobry")
    elif nazwa == "korytarze_LS" and wagi == 321:
        if value[0] <= 95:
            value.append("bardzo niski")
        elif 95 < value[0] <= 109:
            value.append("niski")
        elif 109 < value[0] <= 117:
            value.append("umiarkowany")
        elif 117 < value[0] <= 126:
            value.append("wysoki")
        elif value[0] > 126:
            value.append("bardzo wysoki")
    elif nazwa == "korytarze_NL" and wagi == 321:
        if value[0] <= 79:
            value.append("bardzo niski")
        elif 79 < value[0] <= 86:
            value.append("niski")
        elif 86 < value[0] <= 94:
            value.append("umiarkowany")
        elif 94 < value[0] <= 104:
            value.append("wysoki")
        elif value[0] > 104:
            value.append("bardzo wysoki")
    elif nazwa == "korytarze_LS" and wagi == 531:
        if value[0] <= 143:
            value.append("bardzo niski")
        elif 143 < value[0] <= 162:
            value.append("niski")
        elif 162 < value[0] <= 176:
            value.append("umiarkowany")
        elif 176 < value[0] <= 189:
            value.append("wysoki")
        elif value[0] > 189:
            value.append("bardzo wysoki")
    elif nazwa == "korytarze_NL" and wagi == 531:
        if value[0] <= 116:
            value.append("bardzo niski")
        elif 116 < value[0] <= 127:
            value.append("niski")
        elif 127 < value[0] <= 139:
            value.append("umiarkowany")
        elif 139 < value[0] <= 154:
            value.append("wysoki")
        elif value[0] > 154:
            value.append("bardzo wysoki")
    return value


def read_to_dictionary(pd_table):
    dictionary = {}
    for row_idx, row in pd_table.iterrows():
        record_name = row['0']
        record_value = [row['1'], row['4']]
        dictionary[record_name] = record_value
    return dictionary


# Odczyt danych z pliku CSV
#tabela_woda321 = pd.read_csv("woda321.csv", sep=",", encoding="utf-8-sig")
tabela_woda531 = pd.read_csv("woda531.csv", sep=",", encoding="utf-8-sig")
# tabela_rosliny321 = pd.read_csv("rosliny321.csv", sep=",", encoding="utf-8-sig")
tabela_rosliny531 = pd.read_csv("rosliny531.csv", sep=",", encoding="utf-8-sig")
# tabela_ssaki321 = pd.read_csv("ssaki321.csv", sep=",", encoding="utf-8-sig")
tabela_ssaki531 = pd.read_csv("ssaki531.csv", sep=",", encoding="utf-8-sig")
# tabela_ptaki321 = pd.read_csv("ptaki321.csv", sep=",", encoding="utf-8-sig")
tabela_ptaki531 = pd.read_csv("ptaki531.csv", sep=",", encoding="utf-8-sig")
# tabela_bezkregowce321 = pd.read_csv("bezkregowce321.csv", sep=",", encoding="utf-8-sig")
tabela_bezkregowce531 = pd.read_csv("bezkregowce531.csv", sep=",", encoding="utf-8-sig")
# tabela_korytarze321 = pd.read_csv("korytarze321.csv", sep=",", encoding="utf-8-sig")
tabela_korytarze531 = pd.read_csv("korytarze531.csv", sep=",", encoding="utf-8-sig")

# dict_woda321 = read_to_dictionary(tabela_woda321)
dict_woda531 = read_to_dictionary(tabela_woda531)

# dict_rosliny321 = read_to_dictionary(tabela_rosliny321)
dict_rosliny531 = read_to_dictionary(tabela_rosliny531)

# dict_ssaki321 = read_to_dictionary(tabela_ssaki321)
dict_ssaki531 = read_to_dictionary(tabela_ssaki531)

# dict_ptaki321 = read_to_dictionary(tabela_ptaki321)
dict_ptaki531 = read_to_dictionary(tabela_ptaki531)

# dict_bezkregowce321 = read_to_dictionary(tabela_bezkregowce321)
dict_bezkregowce531 = read_to_dictionary(tabela_bezkregowce531)

# dict_korytarze321 = read_to_dictionary(tabela_korytarze321)
dict_korytarze531 = read_to_dictionary(tabela_korytarze531)

df_udzial_lasu = pd.read_excel("Udzial_lasu.xlsx", sheet_name=0, engine="openpyxl")
LS_dict = {}
for row_idx, row in df_udzial_lasu.iterrows():
    record_name = row['Name']
    record_value = row['LS/NL']
    LS_dict[record_name] = record_value


def oblicz_wynik(oczko, ls_nl, wagi):
    if wagi == 321:
        return
        # woda = dict_woda321[oczko]
        # rosliny = dict_rosliny321[oczko]
        # ptaki = dict_ptaki321[oczko]
        # ssaki = dict_ssaki321[oczko]
        # bezkregowce = dict_bezkregowce321[oczko]
        # if ls_nl == 'LS':
        #     suma = woda[0] + rosliny[0] + ptaki[0] + ssaki[0] + bezkregowce[0]
        #     suma = suma + woda[1] + rosliny[1] + ptaki[1] + ssaki[1] + bezkregowce[1]
        #     wynik = przedzialy(suma, 'ekosystem_LS', 321)
        # elif ls_nl == 'NL':
        #     suma = woda[0] + rosliny[0] + ptaki[0] + ssaki[0] + bezkregowce[0]
        #     suma = suma + woda[1] + rosliny[1] + ptaki[1] + ssaki[1] + bezkregowce[1]
        #     wynik = przedzialy(suma, 'ekosystem_NL', 321)
    if wagi == 531:
        woda = dict_woda531[oczko]
        rosliny = dict_rosliny531[oczko]
        ptaki = dict_ptaki531[oczko]
        ssaki = dict_ssaki531[oczko]
        bezkregowce = dict_bezkregowce531[oczko]
        if ls_nl == 'LS':
            suma = woda[0] + rosliny[0] + ptaki[0] + ssaki[0] + bezkregowce[0]
            suma = suma + woda[1] + rosliny[1] + ptaki[1] + ssaki[1] + bezkregowce[1]
            wynik = przedzialy(suma, 'ekosystem_LS', 531)
        elif ls_nl == 'NL':
            suma = woda[0] + rosliny[0] + ptaki[0] + ssaki[0] + bezkregowce[0]
            suma = suma + woda[1] + rosliny[1] + ptaki[1] + ssaki[1] + bezkregowce[1]
            wynik = przedzialy(suma, 'ekosystem_NL', 531)
    return [oczko, wynik]


def wynik_korytarze(oczko, ls_nl, wagi):
    if wagi == 321:
        return
        # korytarze = dict_korytarze321[oczko]
        # suma = korytarze[0] + korytarze[1]
        # if ls_nl == 'LS':
        #     wynik = przedzialy(suma, 'korytarze_LS', 321)
        # elif ls_nl == 'NL':
        #     wynik = przedzialy(suma, 'korytarze_NL', 321)
    elif wagi == 531:
        korytarze = dict_korytarze531[oczko]
        suma = korytarze[0] + korytarze[1]
        if ls_nl == 'LS':
            wynik = przedzialy(suma, 'korytarze_LS', 531)
        elif ls_nl == 'NL':
            wynik = przedzialy(suma, 'korytarze_NL', 531)
    return [oczko, wynik]


wynik = []
for key in LS_dict.keys():
    wynik.append(wynik_korytarze(key, LS_dict[key], 531))
    #wynik.append(oblicz_wynik(key, LS_dict[key], 531))

wyniki = pd.DataFrame(wynik)
print(wyniki)
wyniki.to_csv(
    "wyniki_korytarze531.csv",
    index=False,
    encoding="utf-8-sig",
    sep=","
)
