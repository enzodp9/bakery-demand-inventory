"""Etapa 6: unifica los pronósticos por ingrediente en un único CSV por fecha.

Entrada:  data/results/PRONOSTICO_<ingrediente>_SARIMA.csv (uno por ingrediente)
Salida:   data/results/PRONOSTICO_UNIFICADO.csv
"""

import pandas as pd

from .config import DATA_RESULTS, INGREDIENTES


def unificar_pronosticos(resultados_dir=DATA_RESULTS) -> pd.DataFrame:
    df_por_ingrediente = {}

    for ingrediente in INGREDIENTES:
        archivo = resultados_dir / f"PRONOSTICO_{ingrediente}_SARIMA.csv"
        if not archivo.exists():
            continue
        df = pd.read_csv(archivo)
        if {"date", "forecast"}.issubset(df.columns):
            df = df.rename(columns={"forecast": ingrediente})
            df_por_ingrediente[ingrediente] = df[["date", ingrediente]]

    df_final = pd.DataFrame()
    for df in df_por_ingrediente.values():
        df_final = df if df_final.empty else df_final.merge(df, on="date", how="outer")

    df_final = df_final.sort_values(by="date")

    salida = resultados_dir / "PRONOSTICO_UNIFICADO.csv"
    df_final.to_csv(salida, index=False)
    print(f"Archivo generado correctamente: {salida}")
    return df_final


if __name__ == "__main__":
    unificar_pronosticos()
