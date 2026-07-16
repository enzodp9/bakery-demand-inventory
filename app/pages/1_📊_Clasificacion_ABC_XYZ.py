import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.graph_objects as go
import streamlit as st
from utils import cargar_analisis_abc, cargar_analisis_xyz

st.set_page_config(page_title="Clasificación ABC-XYZ", page_icon="📊", layout="wide")
st.title("📊 Clasificación ABC-XYZ")

abc = cargar_analisis_abc()
xyz = cargar_analisis_xyz()[["article", "Coeficiente de variación", "XYZ"]]
combinado = abc.merge(xyz, on="article", how="left")

st.markdown(
    """
**ABC** clasifica productos por facturación acumulada (Pareto): la clase A concentra el
80% de los ingresos y es la única que se modela en detalle (ver demanda de ingredientes).
**XYZ** clasifica por variabilidad de la demanda mensual: X es estable, Z es errático.
"""
)

st.subheader("Pareto de ingresos por producto")
top_n = st.slider("Cantidad de productos a mostrar", 5, len(combinado), 25)
datos = combinado.sort_values("revenue", ascending=False).head(top_n)

fig = go.Figure()
fig.add_bar(x=datos["article"], y=datos["revenue"], name="Ingresos", marker_color="#4C78A8")
fig.add_trace(
    go.Scatter(
        x=datos["article"], y=datos["cumulative_percentage"], name="% acumulado",
        yaxis="y2", mode="lines+markers", line=dict(color="#E45756"),
    )
)
fig.update_layout(
    yaxis=dict(title="Ingresos ($)"),
    yaxis2=dict(title="% acumulado", overlaying="y", side="right", range=[0, 105]),
    xaxis=dict(tickangle=-60),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    height=500,
)
st.plotly_chart(fig, width="stretch")

st.subheader("Matriz ABC × XYZ")
st.caption("Cantidad de productos por combinación de clase")
matriz = combinado.pivot_table(index="ABC_class", columns="XYZ", values="article", aggfunc="count", fill_value=0)
matriz = matriz.reindex(index=["A", "B", "C"], columns=["X", "Y", "Z"], fill_value=0)
st.dataframe(matriz, width="stretch")

st.subheader("Detalle por producto")
col1, col2 = st.columns(2)
filtro_abc = col1.multiselect("Clase ABC", ["A", "B", "C"], default=["A", "B", "C"])
filtro_xyz = col2.multiselect("Clase XYZ", ["X", "Y", "Z"], default=["X", "Y", "Z"])

tabla = combinado[combinado["ABC_class"].isin(filtro_abc) & combinado["XYZ"].isin(filtro_xyz)]
st.dataframe(
    tabla[["article", "revenue", "cumulative_percentage", "ABC_class", "Coeficiente de variación", "XYZ"]]
    .sort_values("revenue", ascending=False)
    .rename(columns={
        "article": "Producto", "revenue": "Ingresos", "cumulative_percentage": "% acum.",
        "ABC_class": "ABC", "XYZ": "XYZ",
    }),
    width="stretch",
    hide_index=True,
)
