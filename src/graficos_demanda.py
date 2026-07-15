"""Diagnóstico: curvas de demanda de ingredientes (diaria/semanal/mensual).

No forma parte del pipeline de datos (no escribe archivos), es solo exploratorio.
"""

import matplotlib.pyplot as plt
import pandas as pd

from .config import DATA_INTERIM, INGREDIENTES


def _graficar_demanda(datos: pd.DataFrame, titulo: str, ylabel: str) -> None:
    plt.figure(figsize=(12, 6))
    for ingrediente in INGREDIENTES:
        plt.plot(datos.index, datos[ingrediente], label=ingrediente)
    plt.title(titulo, fontsize=16)
    plt.xlabel("Fecha", fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.legend(title="Ingredientes", loc="upper left", bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.show()


def graficar_demanda_ingredientes(interim_dir=DATA_INTERIM) -> None:
    demanda_diaria = pd.read_csv(interim_dir / "demanda_diaria.csv", parse_dates=["date"], index_col="date")
    demanda_semanal = pd.read_csv(interim_dir / "demanda_semanal.csv", parse_dates=["week"], index_col="week")
    demanda_mensual = pd.read_csv(interim_dir / "demanda_mensual.csv", parse_dates=["month"], index_col="month")

    _graficar_demanda(demanda_diaria, "Demanda diaria de ingredientes", "Demanda diaria (g/ml)")
    _graficar_demanda(demanda_semanal, "Demanda semanal de ingredientes", "Demanda semanal (g/ml)")
    _graficar_demanda(demanda_mensual, "Demanda mensual de ingredientes", "Demanda mensual (g/ml)")


if __name__ == "__main__":
    graficar_demanda_ingredientes()
