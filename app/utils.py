"""Utilidades compartidas por todas las páginas de la app de Streamlit.

Se importa desde cada página como `from utils import ...`. Cada página agrega esta
carpeta (app/) a sys.path antes de importar (Streamlit no lo hace automáticamente
para módulos en app/pages/), y este archivo agrega además la raíz del repo para
poder importar el paquete `src`.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
import streamlit as st

from src.config import DATA_INTERIM, DATA_RAW, DATA_RESULTS, INGREDIENTES
from src.demanda_ingredientes import calcular_demanda_ingredientes
from src.limpieza import limpiar_ventas

__all__ = [
    "DATA_RAW", "DATA_RESULTS", "INGREDIENTES",
    "asegurar_interim", "cargar_ventas_limpias", "cargar_demanda_ingredientes",
    "cargar_analisis_abc", "cargar_analisis_xyz", "cargar_pronosticos",
    "cargar_metricas_pronostico", "cargar_plan_inventario", "solver_ipopt_disponible",
    "recalcular_plan", "calcular_costos", "VMAX_SECOS", "VMAX_HUMEDOS", "CMAX", "COSTO_FIJO_ORDEN",
    "VOLUMEN_POR_KG", "INGREDIENTES_SECOS", "INGREDIENTES_HUMEDOS",
]

from src.inventario import (
    CMAX,
    COSTO_FIJO_ORDEN,
    INGREDIENTES_HUMEDOS,
    INGREDIENTES_SECOS,
    VMAX_HUMEDOS,
    VMAX_SECOS,
    VOLUMEN_POR_KG,
    calcular_costos,
)


@st.cache_data(show_spinner="Preparando datos (limpieza + demanda de ingredientes)...")
def asegurar_interim() -> None:
    """Genera los CSVs intermedios si todavía no existen (no se versionan en git)."""
    archivos_interim = ["Bakery sales- Clean.csv", "demanda_diaria.csv", "demanda_semanal.csv", "demanda_mensual.csv"]
    if all((DATA_INTERIM / f).exists() for f in archivos_interim):
        return
    limpiar_ventas()
    calcular_demanda_ingredientes()


@st.cache_data
def cargar_ventas_limpias() -> pd.DataFrame:
    asegurar_interim()
    return pd.read_csv(DATA_INTERIM / "Bakery sales- Clean.csv", parse_dates=["date"])


@st.cache_data
def cargar_demanda_ingredientes() -> dict[str, pd.DataFrame]:
    asegurar_interim()
    return {
        "diaria": pd.read_csv(DATA_INTERIM / "demanda_diaria.csv", parse_dates=["date"]),
        "semanal": pd.read_csv(DATA_INTERIM / "demanda_semanal.csv"),
        "mensual": pd.read_csv(DATA_INTERIM / "demanda_mensual.csv", parse_dates=["month"]),
    }


@st.cache_data
def cargar_analisis_abc() -> pd.DataFrame:
    return pd.read_csv(DATA_RESULTS / "Analisis ABC.csv")


@st.cache_data
def cargar_analisis_xyz() -> pd.DataFrame:
    return pd.read_csv(DATA_RESULTS / "ANALISIS XYZ.csv")


@st.cache_data
def cargar_pronosticos() -> dict[str, pd.DataFrame]:
    return {
        ingrediente: pd.read_csv(DATA_RESULTS / f"PRONOSTICO_{ingrediente}_SARIMA.csv", parse_dates=["date"])
        for ingrediente in INGREDIENTES
        if (DATA_RESULTS / f"PRONOSTICO_{ingrediente}_SARIMA.csv").exists()
    }


@st.cache_data
def cargar_metricas_pronostico() -> pd.DataFrame:
    return pd.read_csv(DATA_RESULTS / "metricas_pronostico.csv")


@st.cache_data
def cargar_plan_inventario() -> pd.DataFrame:
    return pd.read_csv(DATA_RESULTS / "plan_inventario.csv")


@st.cache_resource(show_spinner=False)
def solver_ipopt_disponible() -> bool:
    try:
        from pyomo.environ import SolverFactory
        return SolverFactory("ipopt").available(exception_flag=False)
    except Exception:
        return False


def recalcular_plan(vmax_secos: float, vmax_humedos: float, cmax: float, costo_fijo_orden: float) -> pd.DataFrame:
    """Re-resuelve el modelo de inventario con parámetros custom, sin pisar el plan versionado."""
    from src.inventario import optimizar_inventario

    return optimizar_inventario(
        vmax_secos=vmax_secos,
        vmax_humedos=vmax_humedos,
        cmax=cmax,
        costo_fijo_orden=costo_fijo_orden,
        guardar=False,
    )
