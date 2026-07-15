"""Etapa 5: pronóstico semanal de demanda de ingredientes con SARIMA.

Entrada:  data/interim/demanda_semanal.csv
Salida:   data/results/PRONOSTICO_<ingrediente>_SARIMA.csv (52 semanas a futuro)

Los órdenes (order/seasonal_order) se eligieron previamente con auto_arima.py.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_error, mean_squared_error

from .config import DATA_INTERIM, DATA_RESULTS, INGREDIENTES

ORDER = (1, 1, 2)
SEASONAL_ORDER = (1, 1, 0, 52)
SEMANAS_A_PRONOSTICAR = 52


def pronosticar_ingrediente(
    ingrediente: str,
    df: pd.DataFrame,
    salida_dir=DATA_RESULTS,
    graficar: bool = True,
) -> pd.DataFrame:
    demanda = df[ingrediente]
    train_size = int(len(demanda) * 0.8)
    train, test = demanda[:train_size], demanda[train_size:]

    modelo = sm.tsa.SARIMAX(
        train,
        order=ORDER,
        seasonal_order=SEASONAL_ORDER,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    ajuste = modelo.fit()

    pronostico_test = ajuste.predict(start=len(train), end=len(train) + len(test) - 1)

    mae = mean_absolute_error(test, pronostico_test)
    rmse = np.sqrt(mean_squared_error(test, pronostico_test))
    mape = np.mean(np.abs((test - pronostico_test) / test)) * 100
    sesgo = np.mean(pronostico_test - demanda)

    print(f"Métricas para {ingrediente}: MAE={mae:.2f} RMSE={rmse:.2f} MAPE={mape:.2f}% Sesgo={sesgo:.2f}")

    pronostico_futuro = ajuste.predict(start=len(demanda), end=len(demanda) + SEMANAS_A_PRONOSTICAR - 1)

    df_pronostico = pd.DataFrame({"date": pronostico_futuro.index, "forecast": pronostico_futuro.values})
    salida_dir.mkdir(parents=True, exist_ok=True)
    df_pronostico.to_csv(salida_dir / f"PRONOSTICO_{ingrediente}_SARIMA.csv", index=False)

    if graficar:
        _graficar_pronostico(ingrediente, demanda, test, pronostico_test, pronostico_futuro)

    return df_pronostico


def _graficar_pronostico(ingrediente, demanda, test, pronostico_test, pronostico_futuro) -> None:
    import matplotlib.pyplot as plt

    plt.figure(figsize=(12, 6))
    plt.plot(demanda, label="Datos reales", color="green")
    plt.plot(test.index, pronostico_test, label="Pronóstico (test)", color="blue", linestyle="--")
    plt.plot(pronostico_futuro, label=f"Pronóstico futuro ({SEMANAS_A_PRONOSTICAR} semanas)", color="red", linestyle="--")
    plt.title(f"Pronóstico SARIMA de {ingrediente}")
    plt.xlabel("Fecha")
    plt.ylabel("Demanda (g/mL)")
    plt.legend()
    plt.show()


def pronosticar_todos(interim_dir=DATA_INTERIM, salida_dir=DATA_RESULTS, graficar: bool = True) -> None:
    df = pd.read_csv(interim_dir / "demanda_semanal.csv", parse_dates=["week"], index_col="week")
    df.index = pd.date_range(start="2021-01-01", periods=len(df), freq="W")

    for ingrediente in INGREDIENTES:
        print(f"Procesando ingrediente: {ingrediente}")
        pronosticar_ingrediente(ingrediente, df, salida_dir=salida_dir, graficar=graficar)


if __name__ == "__main__":
    pronosticar_todos()
