import pandas as pd
import numpy as np
from keras import Sequential
from keras.layers import Dense, Dropout
from keras.callbacks import EarlyStopping
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score

# --- wczytanie danych ---
df_dane = pd.read_csv("dane_do_uczenia_korytarze.csv")
dane_np = df_dane.to_numpy()

klasy = dane_np[:, -1].astype(np.int32)
dane_np = dane_np[:, 1:-1].astype(np.float32)

liczba_klas = len(np.unique(klasy))

K = 5
kfold = StratifiedKFold(n_splits=K, shuffle=True, random_state=42)


def zbuduj_model(liczba_cech, liczba_klas):
    model = Sequential([
        Dense(96, activation='relu', input_shape=(liczba_cech,)),   # 64->128->96 (środek)
        Dropout(0.2),                                                 # 0.3->0.1->0.2 (środek)
        Dense(48, activation='relu'),                                 # 32->64->48 (środek)
        Dropout(0.15),                                                # 0.2->0.1->0.15 (środek)
        Dense(24, activation='relu'),                                 # zostaje dodatkowa warstwa
        Dense(liczba_klas, activation='softmax')
    ])
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


wyniki_accuracy = []
wyniki_train_accuracy = []
wszystkie_y_true = []
wszystkie_y_pred = []

for fold_nr, (idx_train, idx_test) in enumerate(kfold.split(dane_np, klasy), start=1):
    print(f"\n===== Fold {fold_nr}/{K} =====")

    X_train, X_test = dane_np[idx_train], dane_np[idx_test]
    y_train, y_test = klasy[idx_train], klasy[idx_test]

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    model = zbuduj_model(X_train.shape[1], liczba_klas)

    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=15,
        restore_best_weights=True
    )

    historia = model.fit(
        X_train, y_train,
        validation_split=0.2,
        epochs=200,
        batch_size=16,
        callbacks=[early_stop],
        verbose=0
    )

    liczba_epok = len(historia.history['loss'])
    train_acc_koncowa = historia.history['accuracy'][-1]
    val_acc_koncowa = historia.history['val_accuracy'][-1]
    train_loss_koncowa = historia.history['loss'][-1]
    val_loss_koncowa = historia.history['val_loss'][-1]

    print(f"Trening zatrzymany po {liczba_epok} epokach (limit: 200)")
    print(f"  train accuracy: {train_acc_koncowa:.4f}  |  val accuracy: {val_acc_koncowa:.4f}")
    print(f"  train loss:     {train_loss_koncowa:.4f}  |  val loss:     {val_loss_koncowa:.4f}")

    y_pred_proba = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_pred_proba, axis=1)

    acc = accuracy_score(y_test, y_pred)
    wyniki_accuracy.append(acc)
    wyniki_train_accuracy.append(train_acc_koncowa)
    print(f"Dokładność na zbiorze TESTOWYM (fold {fold_nr}): {acc:.4f}")

    wszystkie_y_true.extend(y_test)
    wszystkie_y_pred.extend(y_pred)

wyniki_accuracy = np.array(wyniki_accuracy)
wyniki_train_accuracy = np.array(wyniki_train_accuracy)

print("\n===== PODSUMOWANIE K-FOLD =====")
print(f"Dokładność testowa w każdym foldzie:     {np.round(wyniki_accuracy, 4)}")
print(f"Dokładność treningowa w każdym foldzie:  {np.round(wyniki_train_accuracy, 4)}")
print(f"Średnia dokładność testowa:    {wyniki_accuracy.mean():.4f} (+/- {wyniki_accuracy.std():.4f})")
print(f"Średnia dokładność treningowa: {wyniki_train_accuracy.mean():.4f} (+/- {wyniki_train_accuracy.std():.4f})")
print(f"Średnia luka (train - test):   {(wyniki_train_accuracy - wyniki_accuracy).mean():.4f}")

print("\nZbiorcza macierz pomyłek:")
print(confusion_matrix(wszystkie_y_true, wszystkie_y_pred))

print("\nZbiorczy raport klasyfikacji:")
print(classification_report(wszystkie_y_true, wszystkie_y_pred))