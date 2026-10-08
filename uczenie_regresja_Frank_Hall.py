import pandas as pd
import numpy as np
from keras import Sequential, regularizers
from keras.layers import Dense, Dropout
from keras.callbacks import EarlyStopping
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score

# --- wczytanie danych ---
df_dane_LS = pd.read_csv("dane_do_uczenia.csv")
dane_np_LS = df_dane_LS.to_numpy()

klasy_LS = dane_np_LS[:, -1].astype(np.int32)
dane_np_LS = dane_np_LS[:, 1:-1].astype(np.float32)

liczba_klas = len(np.unique(klasy_LS))
liczba_progow = liczba_klas - 1

liczebnosci = dict(zip(*np.unique(klasy_LS, return_counts=True)))
print("Liczność klas:", {int(k): int(v) for k, v in liczebnosci.items()})


def zakoduj_porzadkowo(y, liczba_klas):
    liczba_progow = liczba_klas - 1
    y_kodowane = np.zeros((len(y), liczba_progow), dtype=np.float32)
    for prog in range(liczba_progow):
        y_kodowane[:, prog] = (y > prog).astype(np.float32)
    return y_kodowane


def odkoduj_porzadkowo(y_proba, prog=0.5):
    return (y_proba > prog).sum(axis=1)


def wagi_probek(y, liczebnosci):
    n_total = len(y)
    n_klas = len(liczebnosci)
    return np.array([n_total / (n_klas * liczebnosci[klasa]) for klasa in y], dtype=np.float32)


def zbuduj_model(liczba_cech, liczba_progow):
    l2 = regularizers.l2(0.001)
    model = Sequential([
        Dense(64, activation='relu', input_shape=(liczba_cech,), kernel_regularizer=l2),
        Dropout(0.2),
        Dense(32, activation='relu', kernel_regularizer=l2),
        Dropout(0.1),
        Dense(liczba_progow, activation='sigmoid')
    ])
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    return model


K = 5
POWTORZENIA = 4
kfold = RepeatedStratifiedKFold(n_splits=K, n_repeats=POWTORZENIA, random_state=42)

wyniki_accuracy = []
wyniki_train_accuracy = []
wszystkie_y_true = []
wszystkie_y_pred = []

for fold_nr, (idx_train, idx_test) in enumerate(kfold.split(dane_np_LS, klasy_LS), start=1):
    X_train, X_test = dane_np_LS[idx_train], dane_np_LS[idx_test]
    y_train, y_test = klasy_LS[idx_train], klasy_LS[idx_test]

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    y_train_kod = zakoduj_porzadkowo(y_train, liczba_klas)
    wagi_treningowe = wagi_probek(y_train, liczebnosci)

    model = zbuduj_model(X_train.shape[1], liczba_progow)

    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

    model.fit(
        X_train, y_train_kod,
        sample_weight=wagi_treningowe,
        validation_split=0.2,
        epochs=150,
        batch_size=16,
        callbacks=[early_stop],
        verbose=0
    )

    y_pred_proba = model.predict(X_test, verbose=0)
    y_pred = odkoduj_porzadkowo(y_pred_proba)

    y_pred_proba_train = model.predict(X_train, verbose=0)
    y_pred_train = odkoduj_porzadkowo(y_pred_proba_train)
    train_acc = accuracy_score(y_train, y_pred_train)

    acc = accuracy_score(y_test, y_pred)
    wyniki_accuracy.append(acc)
    wyniki_train_accuracy.append(train_acc)

    if fold_nr % K == 0:
        print(f"Ukończono {fold_nr}/{K * POWTORZENIA} przebiegów "
              f"(ostatni: train={train_acc:.3f}, test={acc:.3f})")

    wszystkie_y_true.extend(y_test)
    wszystkie_y_pred.extend(y_pred)

wyniki_accuracy = np.array(wyniki_accuracy)
wyniki_train_accuracy = np.array(wyniki_train_accuracy)
wszystkie_y_true = np.array(wszystkie_y_true)
wszystkie_y_pred = np.array(wszystkie_y_pred)

print(f"\n===== PODSUMOWANIE {K}x{POWTORZENIA} WALIDACJI KRZYŻOWEJ (sample_weight + L2=0.05) =====")
print(f"Średnia dokładność testowa:    {wyniki_accuracy.mean():.4f} (+/- {wyniki_accuracy.std():.4f})")
print(f"Średnia dokładność treningowa: {wyniki_train_accuracy.mean():.4f} (+/- {wyniki_train_accuracy.std():.4f})")
print(f"Średnia luka (train - test):   {(wyniki_train_accuracy - wyniki_accuracy).mean():.4f}")

print("\nZbiorcza macierz pomyłek:")
print(confusion_matrix(wszystkie_y_true, wszystkie_y_pred))

print("\nZbiorczy raport klasyfikacji:")
print(classification_report(wszystkie_y_true, wszystkie_y_pred))

w_tolerancji = np.abs(wszystkie_y_true - wszystkie_y_pred) <= 1
print(f"\nDokładność w tolerancji ±1 klasa: {w_tolerancji.mean():.4f}")

mae_klas = np.abs(wszystkie_y_true - wszystkie_y_pred).mean()
print(f"Średni błąd bezwzględny (w jednostkach klas): {mae_klas:.4f}")