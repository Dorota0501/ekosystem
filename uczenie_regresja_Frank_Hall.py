import pandas as pd
import numpy as np
from keras import Sequential
from keras.layers import Dense, Dropout
from keras.callbacks import EarlyStopping
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score

# --- wczytanie danych ---
df_dane = pd.read_csv("dane_do_uczenia.csv")
dane_np = df_dane.to_numpy()

klasy = dane_np[:, -1].astype(np.int32)
dane_np = dane_np[:, 1:-1].astype(np.float32)

liczba_klas = len(np.unique(klasy))
liczba_progow = liczba_klas - 1   # dla 5 klas: 4 progi/wyjścia


def zakoduj_porzadkowo(y, liczba_klas):
    """Zamienia etykiety 0..K-1 na macierz binarną progów Frank & Hall."""
    liczba_progow = liczba_klas - 1
    y_kodowane = np.zeros((len(y), liczba_progow), dtype=np.float32)
    for prog in range(liczba_progow):
        y_kodowane[:, prog] = (y > prog).astype(np.float32)
    return y_kodowane


def odkoduj_porzadkowo(y_proba, prog=0.5):
    """Sumuje odpowiedzi 'tak' (prawdopodobieństwo > prog) -> przewidywana klasa."""
    return (y_proba > prog).sum(axis=1)


def zbuduj_model(liczba_cech, liczba_progow):
    model = Sequential([
        Dense(64, activation='relu', input_shape=(liczba_cech,)),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dropout(0.2),
        Dense(liczba_progow, activation='sigmoid')   # K-1 niezależnych wyjść binarnych
    ])
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',   # nie sparse_categorical_crossentropy!
        metrics=['accuracy']
    )
    return model


# --- walidacja krzyżowa ---
K = 5
kfold = StratifiedKFold(n_splits=K, shuffle=True, random_state=42)

wyniki_accuracy = []
wszystkie_y_true = []
wszystkie_y_pred = []

for fold_nr, (idx_train, idx_test) in enumerate(kfold.split(dane_np, klasy), start=1):
    print(f"\n===== Fold {fold_nr}/{K} =====")

    X_train, X_test = dane_np[idx_train], dane_np[idx_test]
    y_train, y_test = klasy[idx_train], klasy[idx_test]

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    y_train_kod = zakoduj_porzadkowo(y_train, liczba_klas)

    model = zbuduj_model(X_train.shape[1], liczba_progow)

    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

    model.fit(
        X_train, y_train_kod,
        validation_split=0.2,
        epochs=100,
        batch_size=32,
        callbacks=[early_stop],
        verbose=0
    )

    y_pred_proba = model.predict(X_test, verbose=0)
    y_pred = odkoduj_porzadkowo(y_pred_proba)

    acc = accuracy_score(y_test, y_pred)
    wyniki_accuracy.append(acc)
    print(f"Dokładność na foldzie {fold_nr}: {acc:.4f}")

    wszystkie_y_true.extend(y_test)
    wszystkie_y_pred.extend(y_pred)

# --- podsumowanie ---
wyniki_accuracy = np.array(wyniki_accuracy)
print("\n===== PODSUMOWANIE K-FOLD (regresja porządkowa) =====")
print(f"Dokładność w każdym foldzie: {np.round(wyniki_accuracy, 4)}")
print(f"Średnia dokładność: {wyniki_accuracy.mean():.4f} (+/- {wyniki_accuracy.std():.4f})")

wszystkie_y_true = np.array(wszystkie_y_true)
wszystkie_y_pred = np.array(wszystkie_y_pred)

print("\nZbiorcza macierz pomyłek:")
print(confusion_matrix(wszystkie_y_true, wszystkie_y_pred))

print("\nZbiorczy raport klasyfikacji:")
print(classification_report(wszystkie_y_true, wszystkie_y_pred))

# dodatkowa metryka: dokładność w tolerancji ±1 klasa
w_tolerancji = np.abs(wszystkie_y_true - wszystkie_y_pred) <= 1
print(f"\nDokładność w tolerancji ±1 klasa: {w_tolerancji.mean():.4f}")

# średni błąd bezwzględny w "jednostkach klas" - jak bardzo model się myli, gdy się myli
mae_klas = np.abs(wszystkie_y_true - wszystkie_y_pred).mean()
print(f"Średni błąd bezwzględny (w jednostkach klas): {mae_klas:.4f}")