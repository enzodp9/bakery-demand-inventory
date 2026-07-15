"""Corre el pipeline completo de punta a punta, en orden.

Uso:
    python -m src.pipeline
    python -m src.pipeline --sin-graficos   (no bloquea con ventanas de matplotlib)
"""

import argparse

from .analisis_abc import analizar_abc
from .analisis_xyz import analizar_xyz
from .demanda_ingredientes import calcular_demanda_ingredientes
from .demanda_mensual import resumir_demanda_mensual
from .inventario import optimizar_inventario
from .limpieza import limpiar_ventas
from .pronosticos import pronosticar_todos
from .unificar_pronosticos import unificar_pronosticos


def correr_pipeline(graficar: bool = True) -> None:
    print("1/8 Limpieza de datos")
    limpiar_ventas()

    print("2/8 Análisis ABC")
    analizar_abc(graficar=graficar)

    print("3/8 Análisis XYZ")
    analizar_xyz()

    print("4/8 Demanda de ingredientes (clase A)")
    calcular_demanda_ingredientes()

    print("5/8 Pronóstico SARIMA por ingrediente")
    pronosticar_todos(graficar=graficar)

    print("6/8 Unificación de pronósticos")
    unificar_pronosticos()

    print("7/8 Resumen de demanda mensual")
    resumir_demanda_mensual()

    print("8/8 Optimización del plan de inventario")
    optimizar_inventario()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sin-graficos", action="store_true", help="No mostrar ventanas de gráficos")
    args = parser.parse_args()

    correr_pipeline(graficar=not args.sin_graficos)
