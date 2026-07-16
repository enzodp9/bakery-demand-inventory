import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from utils import cargar_analisis_abc, cargar_analisis_xyz, cargar_ventas_limpias

st.set_page_config(
    page_title="Demanda e inventario de panadería",
    page_icon="🥖",
    layout="wide",
)

st.title("🥖 Análisis y pronóstico de demanda para inventario de panadería")

st.markdown(
    """
Este tablero recorre un pipeline completo de punta a punta: dos años de ventas de una
panadería se convierten en un plan semanal de compras de ingredientes, combinando tres
técnicas de Investigación Operativa:

1. **Clasificación ABC-XYZ** — qué productos concentran la facturación y qué tan
   variable es su demanda.
2. **Pronóstico SARIMA** — proyección semanal de demanda de cada ingrediente.
3. **Optimización de inventario (NLP)** — cuánto pedir y cuánto stockear cada semana,
   minimizando costos sujeto a capacidad de almacenamiento y capital inmovilizado.

Usá el menú de la izquierda para recorrer cada etapa.
"""
)

ventas = cargar_ventas_limpias()
abc = cargar_analisis_abc()
xyz = cargar_analisis_xyz()

productos_clase_a = (abc["ABC_class"] == "A").sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Ventas registradas", f"{len(ventas):,}".replace(",", "."))
col2.metric("Productos distintos", f"{ventas['article'].nunique()}")
col3.metric("Productos clase A", f"{productos_clase_a}", help="Concentran el 80% de la facturación (Pareto)")
col4.metric("Facturación total", f"${ventas['revenue'].sum():,.0f}".replace(",", "."))

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Distribución ABC")
    st.bar_chart(abc["ABC_class"].value_counts().sort_index())
with col2:
    st.subheader("Distribución XYZ")
    st.bar_chart(xyz["XYZ"].value_counts().sort_index())

st.caption(
    "El código completo del pipeline está en `src/`; el informe técnico con la "
    "fundamentación teórica está en `docs/Informe técnico.pdf`."
)
