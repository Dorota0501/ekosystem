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

#podziel dane tak, aby były podzielone na dwa zbiory: LS



klasy = dane_np[:, -1].astype(np.int32)
dane_np = dane_np[:, 1:-1].astype(np.float32)

liczba_klas = len(np.unique(klasy))

# --- konfiguracja walidacji krzyżowej ---
K = 5
kfold = StratifiedKFold(n_splits=K, shuffle=True, random_state=42)


def zbuduj_model(liczba_cech, liczba_klas):
    model = Sequential([
        Dense(64, activation='relu', input_shape=(liczba_cech,)),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dropout(0.2),
        Dense(liczba_klas, activation='softmax')
    ])
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


# --- przechowywanie wyników z każdego foldu ---
wyniki_accuracy = []
wszystkie_y_true = []
wszystkie_y_pred = []

for fold_nr, (idx_train, idx_test) in enumerate(kfold.split(dane_np, klasy), start=1):
    print(f"\n===== Fold {fold_nr}/{K} =====")

    X_train, X_test = dane_np[idx_train], dane_np[idx_test]
    y_train, y_test = klasy[idx_train], klasy[idx_test]

    # standaryzacja — dopasowana TYLKO na danych treningowych tego foldu
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    model = zbuduj_model(X_train.shape[1], liczba_klas)

    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True
    )

    model.fit(
        X_train, y_train,
        validation_split=0.2,
        epochs=100,
        batch_size=32,
        callbacks=[early_stop],
        verbose=0  # ciszej, bo mamy 5 pełnych treningów pod rząd
    )

    y_pred_proba = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_pred_proba, axis=1)

    acc = accuracy_score(y_test, y_pred)
    wyniki_accuracy.append(acc)
    print(f"Dokładność na foldzie {fold_nr}: {acc:.4f}")

    wszystkie_y_true.extend(y_test)
    wszystkie_y_pred.extend(y_pred)

# --- podsumowanie po wszystkich foldach ---
wyniki_accuracy = np.array(wyniki_accuracy)
print("\n===== PODSUMOWANIE K-FOLD =====")
print(f"Dokładność w każdym foldzie: {np.round(wyniki_accuracy, 4)}")
print(f"Średnia dokładność: {wyniki_accuracy.mean():.4f} (+/- {wyniki_accuracy.std():.4f})")

print("\nZbiorcza macierz pomyłek (wszystkie fold-y razem):")
print(confusion_matrix(wszystkie_y_true, wszystkie_y_pred))

print("\nZbiorczy raport klasyfikacji (wszystkie fold-y razem):")
print(classification_report(wszystkie_y_true, wszystkie_y_pred))
