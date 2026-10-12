import pandas as pd

# Wczytanie danych
df = pd.read_excel("dane.xlsx", sheet_name=6, engine="openpyxl")

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

def przedzialy(value, nazwa, wagi):
    value = [value]
    if nazwa == "woda_LS" and wagi == 321:
        if value[0] <= 41:
            value.append("zly")
        elif 41 < value[0] <= 73:
            value.append("slaby")
        elif 73 < value[0] <= 84:
            value.append("umiarkowany")
        elif 84 < value[0] <= 97:
            value.append("dobry")
        elif value[0] > 97:
            value.append("bardzo dobry")
    elif nazwa == "woda_NL" and wagi == 321:
        if value[0] <= 49:
            value.append("zly")
        elif 49 < value[0] <= 68:
            value.append("slaby")
        elif 68 < value[0] <= 76:
            value.append("umiarkowany")
        elif 76 < value[0] <= 86:
            value.append("dobry")
        elif value[0] > 86:
            value.append("bardzo dobry")
    elif nazwa == "woda_LS" and wagi == 531:
        if value[0] <= 74:
            value.append("zly")
        elif 74 < value[0] <= 117:
            value.append("slaby")
        elif 117 < value[0] <= 131:
            value.append("umiarkowany")
        elif 131 < value[0] <= 148:
            value.append("dobry")
        elif value[0] > 148:
            value.append("bardzo dobry")
    elif nazwa == "woda_NL" and wagi == 531:
        if value[0] <= 72:
            value.append("zly")
        elif 72 < value[0] <= 107:
            value.append("slaby")
        elif 107 < value[0] <= 124:
            value.append("umiarkowany")
        elif 124 < value[0] <= 147:
            value.append("dobry")
        elif value[0] > 147:
            value.append("bardzo dobry")
    elif nazwa == "rosliny_LS" and wagi == 321:
        if value[0] <= 61:
            value.append("zly")
        elif 61 < value[0] <= 66:
            value.append("slaby")
        elif 66 < value[0] <= 74:
            value.append("umiarkowany")
        elif 74 < value[0] <= 82:
            value.append("dobry")
        elif value[0] > 82:
            value.append("bardzo dobry")
    elif nazwa == "rosliny_NL" and wagi == 321:
        if value[0] <= 49:
            value.append("zly")
        elif 49 < value[0] <= 57:
            value.append("slaby")
        elif 57 < value[0] <= 64:
            value.append("umiarkowany")
        elif 64 < value[0] <= 72:
            value.append("dobry")
        elif value[0] > 72:
            value.append("bardzo dobry")
    elif nazwa == "rosliny_LS" and wagi == 531:
        if value[0] <= 79:
            value.append("zly")
        elif 79 < value[0] <= 94:
            value.append("slaby")
        elif 94 < value[0] <= 109:
            value.append("umiarkowany")
        elif 109 < value[0] <= 129:
            value.append("dobry")
        elif value[0] > 129:
            value.append("bardzo dobry")
    elif nazwa == "rosliny_NL" and wagi == 531:
        if value[0] <= 76:
            value.append("zly")
        elif 76 < value[0] <= 93:
            value.append("slaby")
        elif 93 < value[0] <= 110:
            value.append("umiarkowany")
        elif 110 < value[0] <= 134:
            value.append("dobry")
        elif value[0] > 134:
            value.append("bardzo dobry")
    elif nazwa == "ssaki_LS" and wagi == 321:
        if value[0] <= 83:
            value.append("zly")
        elif 83 < value[0] <= 96:
            value.append("slaby")
        elif 96 < value[0] <= 106:
            value.append("umiarkowany")
        elif 106 < value[0] <= 118:
            value.append("dobry")
        elif value[0] > 118:
            value.append("bardzo dobry")
    elif nazwa == "ssaki_NL" and wagi == 321:
        if value[0] <= 77:
            value.append("zly")
        elif 77 < value[0] <= 96:
            value.append("slaby")
        elif 96 < value[0] <= 109:
            value.append("umiarkowany")
        elif 109 < value[0] <= 126:
            value.append("dobry")
        elif value[0] > 126:
            value.append("bardzo dobry")
    elif nazwa == "ssaki_LS" and wagi == 531:
        if value[0] <= 166:
            value.append("zly")
        elif 166 < value[0] <= 195:
            value.append("slaby")
        elif 195 < value[0] <= 220:
            value.append("umiarkowany")
        elif 220 < value[0] <= 245:
            value.append("dobry")
        elif value[0] > 245:
            value.append("bardzo dobry")
    elif nazwa == "ssaki_NL" and wagi == 531:
        if value[0] <= 135:
            value.append("zly")
        elif 135 < value[0] <= 168:
            value.append("slaby")
        elif 168 < value[0] <= 196:
            value.append("umiarkowany")
        elif 196 < value[0] <= 227:
            value.append("dobry")
        elif value[0] > 227:
            value.append("bardzo dobry")
    elif nazwa == "ptaki_LS" and wagi == 321:
        if value[0] <= 35:
            value.append("zly")
        elif 35 < value[0] <= 50:
            value.append("slaby")
        elif 50 < value[0] <= 58:
            value.append("umiarkowany")
        elif 58 < value[0] <= 68:
            value.append("dobry")
        elif value[0] > 68:
            value.append("bardzo dobry")
    elif nazwa == "ptaki_NL" and wagi == 321:
        if value[0] <= 23:
            value.append("zly")
        elif 23 < value[0] <= 34:
            value.append("slaby")
        elif 34 < value[0] <= 44:
            value.append("umiarkowany")
        elif 44 < value[0] <= 58:
            value.append("dobry")
        elif value[0] > 58:
            value.append("bardzo dobry")
    elif nazwa == "ptaki_LS" and wagi == 531:
        if value[0] <= 58:
            value.append("zly")
        elif 58 < value[0] <= 80:
            value.append("slaby")
        elif 80 < value[0] <= 98:
            value.append("umiarkowany")
        elif 98 < value[0] <= 121:
            value.append("dobry")
        elif value[0] > 121:
            value.append("bardzo dobry")
    elif nazwa == "ptaki_NL" and wagi == 531:
        if value[0] <= 35:
            value.append("zly")
        elif 35 < value[0] <= 50:
            value.append("slaby")
        elif 50 < value[0] <= 69:
            value.append("umiarkowany")
        elif 69 < value[0] <= 94:
            value.append("dobry")
        elif value[0] > 94:
            value.append("bardzo dobry")
    elif nazwa == "bezkregowce_LS" and wagi == 321:
        if value[0] <= 31:
            value.append("zly")
        elif 31 < value[0] <= 34:
            value.append("slaby")
        elif 34 < value[0] <= 37:
            value.append("umiarkowany")
        elif 37 < value[0] <= 42:
            value.append("dobry")
        elif value[0] > 42:
            value.append("bardzo dobry")
    elif nazwa == "bezkregowce_NL" and wagi == 321:  # DO POPRAWY
        if value[0] <= 4:
            value.append("zly")
        elif 4 < value[0] <= 15:
            value.append("slaby")
        elif 15 < value[0] <= 33:
            value.append("umiarkowany")
        elif 33 < value[0] <= 47:
            value.append("dobry")
        elif value[0] > 47:
            value.append("bardzo dobry")
    elif nazwa == "bezkregowce_LS" and wagi == 531:
        if value[0] <= 92:
            value.append("zly")
        elif 92 < value[0] <= 98:
            value.append("slaby")
        elif 98 < value[0] <= 107:
            value.append("umiarkowany")
        elif 107 < value[0] <= 118:
            value.append("dobry")
        elif value[0] > 118:
            value.append("bardzo dobry")
    elif nazwa == "bezkregowce_NL" and wagi == 531:
        if value[0] <= 91:
            value.append("zly")
        elif 91 < value[0] <= 94:
            value.append("slaby")
        elif 94 < value[0] <= 99:
            value.append("umiarkowany")
        elif 99 < value[0] <= 105:
            value.append("dobry")
        elif value[0] > 105:
            value.append("bardzo dobry")
    elif nazwa == "ekosystem_LS" and wagi == 321:
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
        if value[0] <= 156:
            value.append("bardzo niski")
        elif 156 < value[0] <= 172:
            value.append("niski")
        elif 172 < value[0] <= 186:
            value.append("umiarkowany")
        elif 186 < value[0] <= 198:
            value.append("wysoki")
        elif value[0] > 198:
            value.append("bardzo wysoki")
    elif nazwa == "korytarze_NL" and wagi == 531:
        if value[0] <= 119:
            value.append("bardzo niski")
        elif 119 < value[0] <= 134:
            value.append("niski")
        elif 134 < value[0] <= 147:
            value.append("umiarkowany")
        elif 147 < value[0] <= 161:
            value.append("wysoki")
        elif value[0] > 161:
            value.append("bardzo wysoki")
    return value

records = []
for row_idx, row in df.iterrows():
    record_LS = []
    record_NL = []
    record_name = row['Name']
    for col_name in value_cols:
        value = row[col_name]
        weight = get_weight(col_name)
        if weight != 0:
            if col_name.__contains__("LS"):
                record_LS.append(value * weight)
            elif col_name.__contains__("NL"):
                record_NL.append(value * weight)
    record_LS = [record_name,  record_LS]
    record_NL = [record_name,  record_NL]
    record_LS_suma = sum(record_LS[1])
    record_NL_suma = sum(record_NL[1])
    record_ls = przedzialy(record_LS_suma, "korytarze_LS", 531)
    record_nl = przedzialy(record_NL_suma, "korytarze_NL", 531)

    records.append([record_LS[0], record_ls[0], record_ls[1], record_NL[0], record_nl[0], record_nl[1]])
    # Stworzenie nowej tabeli (DataFrame) z wszystkich danych

    # Utworzenie tabeli
tabela = pd.DataFrame(records)

# Zapis do pliku CSV
tabela.to_csv(
"korytarze531.csv",
index = False,
encoding = "utf-8-sig",
sep = ","
)
