"""Etapa 1: limpieza del dataset crudo de ventas de la panadería.

Entrada:  data/raw/Bakery sales.csv
Salida:   data/interim/Bakery sales- Clean.csv
"""

import pandas as pd

from .config import DATA_INTERIM, DATA_RAW


def limpiar_ventas(
    entrada=DATA_RAW / "Bakery sales.csv",
    salida=DATA_INTERIM / "Bakery sales- Clean.csv",
) -> pd.DataFrame:
    ventas = pd.read_csv(entrada)

    ventas.columns = ventas.columns.str.lower().str.replace(" ", "_")
    ventas = ventas.drop(columns=["unnamed:_0"])

    ventas["date"] = pd.to_datetime(ventas["date"], format="%Y-%m-%d")
    ventas["unit_price"] = (
        ventas["unit_price"].str.replace("€", "").str.replace(",", ".").astype(float)
    )
    ventas["revenue"] = round(ventas["quantity"] * ventas["unit_price"], 2)

    ventas = ventas.dropna()
    ventas = ventas[(ventas["quantity"] > 0) & (ventas["unit_price"] > 0)]
    ventas = ventas[~ventas["article"].str.strip().isin(["", "."])]

    # Outliers de cantidad: 3*IQR para ser conservadores (ventas de panadería son volátiles)
    q1, q3 = ventas["quantity"].quantile([0.25, 0.75])
    iqr = q3 - q1
    ventas = ventas[
        (ventas["quantity"] >= q1 - 3 * iqr) & (ventas["quantity"] <= q3 + 3 * iqr)
    ]

    salida.parent.mkdir(parents=True, exist_ok=True)
    ventas.to_csv(salida, index=False)
    return ventas


if __name__ == "__main__":
    resultado = limpiar_ventas()
    print(resultado.head())
    print(resultado.info())
