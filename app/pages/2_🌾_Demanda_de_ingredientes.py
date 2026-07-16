import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.express as px
import streamlit as st
from utils import INGREDIENTES, cargar_demanda_ingredientes

st.set_page_config(page_title="Demanda de ingredientes", page_icon="🌾", layout="wide")
st.title("🌾 Demanda de ingredientes")

st.markdown(
    """
Demanda histórica de ingredientes derivada de las ventas de productos **clase A**,
usando la tabla de recetas (gramos/mL por unidad vendida) en `src/demanda_ingredientes.py`.
"""
)

demanda = cargar_demanda_ingredientes()

col1, col2 = st.columns([1, 3])
granularidad = col1.radio("Granularidad", ["Diaria", "Semanal", "Mensual"], index=1)
ingredientes_sel = col2.multiselect("Ingredientes", INGREDIENTES, default=INGREDIENTES)

clave_columna = {"Diaria": "date", "Semanal": "week", "Mensual": "month"}[granularidad]
df = demanda[granularidad.lower()][[clave_columna, *ingredientes_sel]] if ingredientes_sel else None

if df is None or df.empty:
    st.info("Seleccioná al menos un ingrediente.")
else:
    df_largo = df.melt(id_vars=clave_columna, var_name="Ingrediente", value_name="Demanda (g/mL)")
    fig = px.line(df_largo, x=clave_columna, y="Demanda (g/mL)", color="Ingrediente")
    fig.update_layout(height=550, xaxis_title="Fecha", legend_title="Ingrediente")
    st.plotly_chart(fig, width="stretch")

    with st.expander("Ver datos"):
        st.dataframe(df, width="stretch", hide_index=True)
