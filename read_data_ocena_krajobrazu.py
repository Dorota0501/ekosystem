import pandas as pd
import numpy as np
from keras import Sequential
from keras.layers import Dense, Dropout
from keras.callbacks import EarlyStopping
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score

df_zagrozenia = pd.read_excel("dane.xlsx", sheet_name=7, engine="openpyxl")
df_wyniki = pd.read_csv("ocena_krajobrazu.csv")

df_all = df_zagrozenia.merge(
    df_wyniki[["Name", df_wyniki.columns[6]]].rename(
        columns={df_wyniki.columns[6]: "wynik"}
    ),
    on="Name",
    how="left"
)

df_all.to_csv(
    "dane_do_uczenia_ocena_krajobrazu.csv",
    index=False,
    encoding="utf-8-sig"
)





















