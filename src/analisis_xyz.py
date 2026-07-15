"""Etapa 3: clasificación XYZ de productos según variabilidad de la demanda mensual.

Entrada:  data/interim/Bakery sales- Clean.csv
Salida:   data/results/ANALISIS XYZ.csv
"""

import pandas as pd

from .config import DATA_INTERIM, DATA_RESULTS


def clasificar_xyz(coeficiente_variacion: float) -> str:
    if coeficiente_variacion <= 50:
        return "X"
    if coeficiente_variacion <= 100:
        return "Y"
    return "Z"


def analizar_xyz(
    entrada=DATA_INTERIM / "Bakery sales- Clean.csv",
    salida=DATA_RESULTS / "ANALISIS XYZ.csv",
) -> pd.DataFrame:
    ventas = pd.read_csv(entrada)
    ventas["date"] = pd.to_datetime(ventas["date"])
    ventas["month"] = ventas["date"].dt.month

    ventas_mensuales = ventas.groupby(["article", "month"])["quantity"].sum().unstack(fill_value=0)

    ventas_mensuales["TOTAL"] = ventas_mensuales.sum(axis=1)
    ventas_mensuales["Promedio de Ventas"] = ventas_mensuales["TOTAL"] / 12
    ventas_mensuales["Desviación Estandar"] = ventas_mensuales.iloc[:, :12].std(axis=1, ddof=0)
    ventas_mensuales["Coeficiente de variación"] = (
        ventas_mensuales["Desviación Estandar"] / ventas_mensuales["Promedio de Ventas"] * 100
    )
    ventas_mensuales["XYZ"] = ventas_mensuales["Coeficiente de variación"].apply(clasificar_xyz)

    ventas_mensuales = ventas_mensuales.reset_index()

    salida.parent.mkdir(parents=True, exist_ok=True)
    ventas_mensuales.to_csv(salida, index=False)
    return ventas_mensuales


if __name__ == "__main__":
    resultado = analizar_xyz()
    print(resultado["XYZ"].value_counts())
