import pandas as pd

# Wczytanie danych
df = pd.read_excel("dane.xlsx", sheet_name=1, engine="openpyxl")

id_col = df.columns[0]
value_cols = df.columns[1:]

tab_weights = []



def get_weight(col_name) -> float:
    if not isinstance(col_name, str):
        return 0
    if "R1" in col_name:
        return 1
    elif "R2" in col_name:
        return 2
    elif "R3" in col_name:
        return 3
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
        if value[0] <= 57:
            value.append("zly")
        elif 57 < value[0] <= 107:
            value.append("slaby")
        elif 107 < value[0] <= 123:
            value.append("umiarkowany")
        elif 123 < value[0] <= 141:
            value.append("dobry")
        elif value[0] > 141:
            value.append("bardzo dobry")
    elif nazwa == "woda_NL" and wagi == 531:
        if value[0] <= 70:
            value.append("zly")
        elif 70 < value[0] <= 101:
            value.append("slaby")
        elif 101 < value[0] <= 115:
            value.append("umiarkowany")
        elif 115 < value[0] <= 131:
            value.append("dobry")
        elif value[0] > 131:
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
        if value[0] <= 89:
            value.append("zly")
        elif 89 < value[0] <= 98:
            value.append("slaby")
        elif 98 < value[0] <= 106:
            value.append("umiarkowany")
        elif 106 < value[0] <= 118:
            value.append("dobry")
        elif value[0] > 118:
            value.append("bardzo dobry")
    elif nazwa == "rosliny_NL" and wagi == 531:
        if value[0] <= 72:
            value.append("zly")
        elif 72 < value[0] <= 83:
            value.append("slaby")
        elif 83 < value[0] <= 94:
            value.append("umiarkowany")
        elif 94 < value[0] <= 104:
            value.append("dobry")
        elif value[0] > 104:
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
        if value[0] <= 116:
            value.append("zly")
        elif 116 < value[0] <= 134:
            value.append("slaby")
        elif 134 < value[0] <= 151:
            value.append("umiarkowany")
        elif 151 < value[0] <= 170:
            value.append("dobry")
        elif value[0] > 170:
            value.append("bardzo dobry")
    elif nazwa == "ssaki_NL" and wagi == 531:
        if value[0] <= 113:
            value.append("zly")
        elif 113 < value[0] <= 141:
            value.append("slaby")
        elif 141 < value[0] <= 157:
            value.append("umiarkowany")
        elif 157 < value[0] <= 177:
            value.append("dobry")
        elif value[0] > 177:
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
        if value[0] <= 73:
            value.append("zly")
        elif 73 < value[0] <= 84:
            value.append("slaby")
        elif 84 < value[0] <= 98:
            value.append("umiarkowany")
        elif 98 < value[0] <= 111:
            value.append("dobry")
        elif value[0] > 111:
            value.append("bardzo dobry")
    elif nazwa == "ptaki_NL" and wagi == 531:
        if value[0] <= 42:
            value.append("zly")
        elif 42 < value[0] <= 58:
            value.append("slaby")
        elif 58 < value[0] <= 74:
            value.append("umiarkowany")
        elif 74 < value[0] <= 94:
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
        if value[0] <= 46:
            value.append("zly")
        elif 46 < value[0] <= 49:
            value.append("slaby")
        elif 49 < value[0] <= 54:
            value.append("umiarkowany")
        elif 54 < value[0] <= 60:
            value.append("dobry")
        elif value[0] > 60:
            value.append("bardzo dobry")
    elif nazwa == "bezkregowce_NL" and wagi == 531:
        if value[0] <= 4:
            value.append("zly")
        elif 4 < value[0] <= 23:
            value.append("slaby")
        elif 23 < value[0] <= 53:
            value.append("umiarkowany")
        elif 53 < value[0] <= 70:
            value.append("dobry")
        elif value[0] > 70:
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
    record_ls = przedzialy(record_LS_suma, "woda_LS", 321)
    record_nl = przedzialy(record_NL_suma, "woda_NL", 321)

    records.append([record_LS[0], record_ls[0], record_ls[1], record_NL[0], record_nl[0], record_nl[1]])
    # Stworzenie nowej tabeli (DataFrame) z wszystkich danych

    # Utworzenie tabeli
tabela = pd.DataFrame(records)

# Zapis do pliku CSV
tabela.to_csv(
"woda321.csv",
index = False,
encoding = "utf-8-sig",
sep = ","
)
