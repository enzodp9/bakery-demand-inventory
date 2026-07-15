"""Diagnóstico: series de tiempo de ventas diarias de los productos clase A.

No forma parte del pipeline de datos (no escribe archivos), es solo exploratorio.
"""

import matplotlib.pyplot as plt
import pandas as pd

from .config import DATA_INTERIM, DATA_RESULTS


def graficar_series_clase_a(
    abc_path=DATA_RESULTS / "Analisis ABC.csv",
    ventas_path=DATA_INTERIM / "Bakery sales- Clean.csv",
) -> None:
    productos_clase_a = pd.read_csv(abc_path)
    productos_clase_a = productos_clase_a[productos_clase_a["ABC_class"] == "A"]["article"]

    ventas = pd.read_csv(ventas_path)
    ventas_clase_a = ventas[ventas["article"].isin(productos_clase_a)]

    ventas_diarias = ventas_clase_a.groupby(["date", "article"])["quantity"].sum().reset_index()

    plt.figure(figsize=(12, 6))
    for producto in productos_clase_a:
        datos_producto = ventas_diarias[ventas_diarias["article"] == producto]
        plt.plot(datos_producto["date"], datos_producto["quantity"], label=producto)

    plt.title("Series de tiempo de productos clase A", fontsize=16)
    plt.xlabel("Fecha", fontsize=12)
    plt.ylabel("Cantidad vendida", fontsize=12)
    plt.legend(title="Productos", loc="upper left", bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    graficar_series_clase_a()
