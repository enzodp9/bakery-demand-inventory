"""Herramienta de diagnóstico: búsqueda automática de orden SARIMA para un ingrediente.

No forma parte del pipeline de datos — se usa manualmente para elegir el
order/seasonal_order que después se hardcodea en pronosticos.py.
"""

import pandas as pd
import pmdarima as pm

from .config import DATA_INTERIM


def buscar_mejor_sarima(ingrediente: str, interim_dir=DATA_INTERIM):
    df = pd.read_csv(interim_dir / "demanda_semanal.csv", parse_dates=["week"], index_col="week")
    df.index = pd.date_range(start="2021-01-01", periods=len(df), freq="W")

    demanda = df[ingrediente]
    train_size = int(len(demanda) * 0.8)
    train = demanda[:train_size]

    modelo_auto = pm.auto_arima(
        train,
        seasonal=True,
        m=52,
        start_p=0, max_p=3,
        start_q=0, max_q=3,
        start_P=0, max_P=2,
        start_Q=0, max_Q=2,
        d=1, D=1,
        trace=True,
        stepwise=True,
    )

    print(f"Mejor ARIMA: {modelo_auto.order}")
    print(f"Mejor SARIMA: {modelo_auto.seasonal_order}")
    return modelo_auto.order, modelo_auto.seasonal_order


if __name__ == "__main__":
    buscar_mejor_sarima("chocolate")
