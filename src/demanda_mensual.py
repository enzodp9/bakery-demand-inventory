"""Etapa 7: resume el pronóstico semanal a demanda promedio mensual (kg/L).

Entrada:  data/results/PRONOSTICO_<ingrediente>_SARIMA.csv
Salida:   data/results/monthly_demand.csv

Nota: el script original (demandaMensual.py) leía archivos "forecast_<ingrediente>.csv"
que ningún otro script del pipeline generaba — un nombre que quedó desactualizado.
Acá se corrige para leer los PRONOSTICO_<ingrediente>_SARIMA.csv reales.
"""

import pandas as pd

from .config import DATA_RESULTS, INGREDIENTES

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def resumir_demanda_mensual(resultados_dir=DATA_RESULTS) -> pd.DataFrame:
    demanda_mensual_df = pd.DataFrame()

    for ingrediente in INGREDIENTES:
        archivo = resultados_dir / f"PRONOSTICO_{ingrediente}_SARIMA.csv"
        if not archivo.exists():
            continue

        df = pd.read_csv(archivo, parse_dates=["date"])
        df["month"] = df["date"].dt.month
        demanda_mensual = (df.groupby("month")["forecast"].mean().round(2) / 1000).reset_index()
        demanda_mensual.columns = ["month", f"demand_{ingrediente}"]

        demanda_mensual_df = (
            demanda_mensual
            if demanda_mensual_df.empty
            else demanda_mensual_df.merge(demanda_mensual, on="month", how="outer")
        )

    demanda_mensual_df["month"] = demanda_mensual_df["month"].map(MESES)
    demanda_mensual_df["month"] = pd.Categorical(
        demanda_mensual_df["month"], categories=MESES.values(), ordered=True
    )
    demanda_mensual_df = demanda_mensual_df.sort_values("month")

    salida = resultados_dir / "monthly_demand.csv"
    demanda_mensual_df.to_csv(salida, index=False)
    return demanda_mensual_df


if __name__ == "__main__":
    resultado = resumir_demanda_mensual()
    print(resultado)
