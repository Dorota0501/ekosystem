import pandas as pd


def read_to_dictionary(pd_table):
    dictionary = {}
    for row_idx, row in pd_table.iterrows():
        record_name = row['Name']
        record_value = row.iloc[1:].tolist()
        dictionary[record_name] = record_value
    return dictionary


df_udzial_lasu = pd.read_excel("Udzial_lasu.xlsx", sheet_name=0, engine="openpyxl")
LS_dict = {}
for row_idx, row in df_udzial_lasu.iterrows():
    record_name = row['Name']
    record_value = row['LS/NL']
    LS_dict[record_name] = record_value

df_dane = pd.read_csv("dane_do_uczenia.csv")
dict_dane = read_to_dictionary(df_dane)

dane_LS = []
dane_NL = []

for key in LS_dict.keys():
    dane = [key] + dict_dane[key]
    if LS_dict[key] == 'LS':
        dane_LS.append(dane)
    elif LS_dict[key] == 'NL':
        dane_NL.append(dane)

dane_LS = pd.DataFrame(dane_LS)
dane_NL = pd.DataFrame(dane_NL)

dane_LS.to_csv(
    "dane_LS.csv",
    index=False,
    encoding="utf-8-sig",
    sep=","
)

dane_NL.to_csv(
    "dane_NL.csv",
    index=False,
    encoding="utf-8-sig",
    sep=","
)
