"""Etapa 2: clasificación ABC de productos según ingresos acumulados (Pareto).

Entrada:  data/interim/Bakery sales- Clean.csv
Salida:   data/results/Analisis ABC.csv (+ reports/figures/pareto_abc.png)
"""

import matplotlib.pyplot as plt
import pandas as pd

from .config import DATA_INTERIM, DATA_RESULTS, REPORTS_FIGURES


def clasificar_abc(porcentaje_acumulado: float) -> str:
    if porcentaje_acumulado <= 80:
        return "A"
    if porcentaje_acumulado <= 95:
        return "B"
    return "C"


def analizar_abc(
    entrada=DATA_INTERIM / "Bakery sales- Clean.csv",
    salida=DATA_RESULTS / "Analisis ABC.csv",
    graficar: bool = True,
) -> pd.DataFrame:
    ventas = pd.read_csv(entrada)

    ingresos = ventas.groupby("article")["revenue"].sum().reset_index()
    ingresos = ingresos.sort_values(by="revenue", ascending=False)

    total = ingresos["revenue"].sum()
    ingresos["cumulative_revenue"] = ingresos["revenue"].cumsum()
    ingresos["cumulative_percentage"] = ingresos["cumulative_revenue"] / total * 100
    ingresos["ABC_class"] = ingresos["cumulative_percentage"].apply(clasificar_abc)

    salida.parent.mkdir(parents=True, exist_ok=True)
    ingresos.to_csv(salida, index=False)

    if graficar:
        _graficar_pareto(ingresos)

    return ingresos


def _graficar_pareto(ingresos: pd.DataFrame) -> None:
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(ingresos["article"], ingresos["revenue"], color="skyblue")

    ax2 = ax1.twinx()
    ax2.plot(
        ingresos["article"],
        ingresos["cumulative_percentage"],
        color="red",
        marker="o",
        linewidth=2,
    )

    ax1.set_xlabel("Producto")
    ax1.set_ylabel("Ingresos ($)")
    ax2.set_ylabel("Porcentaje acumulado (%)")
    ax1.set_title("Gráfico de Pareto - Ingresos por Producto")
    plt.xticks(rotation=90)
    ax1.legend(["Ingresos"], loc="upper left")
    ax2.legend(["Porcentaje acumulado"], loc="upper right")
    plt.tight_layout()

    REPORTS_FIGURES.mkdir(parents=True, exist_ok=True)
    plt.savefig(REPORTS_FIGURES / "pareto_abc.png")
    plt.show()


if __name__ == "__main__":
    resultado = analizar_abc()
    print(resultado["ABC_class"].value_counts())
    print(resultado.head())
