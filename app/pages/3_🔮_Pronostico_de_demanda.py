import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils import INGREDIENTES, cargar_demanda_ingredientes, cargar_metricas_pronostico, cargar_pronosticos

st.set_page_config(page_title="Pronóstico de demanda", page_icon="🔮", layout="wide")
st.title("🔮 Pronóstico de demanda (SARIMA)")

st.markdown(
    """
Modelo **SARIMA(1,1,2)(1,1,0,52)** semanal por ingrediente (52 = estacionalidad anual en
semanas), validado con un split 80/20 y proyectado 52 semanas a futuro. El orden se eligió
con búsqueda automática (`src/auto_arima.py`).
"""
)

pronosticos = cargar_pronosticos()
metricas = cargar_metricas_pronostico()
demanda_semanal = cargar_demanda_ingredientes()["semanal"].copy()
demanda_semanal["date"] = pd.date_range(start="2021-01-01", periods=len(demanda_semanal), freq="W")

ingrediente = st.selectbox("Ingrediente", INGREDIENTES, index=INGREDIENTES.index("harina"))

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=demanda_semanal["date"], y=demanda_semanal[ingrediente],
        name="Demanda histórica", mode="lines", line=dict(color="#4C78A8"),
    )
)
if ingrediente in pronosticos:
    pronostico = pronosticos[ingrediente]
    fig.add_trace(
        go.Scatter(
            x=pronostico["date"], y=pronostico["forecast"],
            name="Pronóstico (52 semanas)", mode="lines", line=dict(color="#E45756", dash="dash"),
        )
    )
fig.update_layout(height=500, xaxis_title="Fecha", yaxis_title="Demanda semanal (g/mL)")
st.plotly_chart(fig, width="stretch")

st.subheader("Métricas de validación (80/20 train-test)")
fila = metricas[metricas["ingrediente"] == ingrediente].iloc[0]
col1, col2, col3, col4 = st.columns(4)
col1.metric("MAE", f"{fila['mae']:,.0f}".replace(",", "."))
col2.metric("RMSE", f"{fila['rmse']:,.0f}".replace(",", "."))
col3.metric("MAPE", f"{fila['mape']:.1f}%")
col4.metric("Sesgo", f"{fila['sesgo']:,.0f}".replace(",", "."))

with st.expander("Ver métricas de todos los ingredientes"):
    st.dataframe(
        metricas.rename(columns={
            "ingrediente": "Ingrediente", "mae": "MAE", "rmse": "RMSE", "mape": "MAPE (%)", "sesgo": "Sesgo",
        }),
        width="stretch",
        hide_index=True,
    )
