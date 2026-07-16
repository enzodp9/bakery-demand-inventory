import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from utils import (
    CMAX,
    COSTO_FIJO_ORDEN,
    INGREDIENTES_HUMEDOS,
    INGREDIENTES_SECOS,
    VMAX_HUMEDOS,
    VMAX_SECOS,
    VOLUMEN_POR_KG,
    calcular_costos,
    cargar_plan_inventario,
    recalcular_plan,
    solver_ipopt_disponible,
)

st.set_page_config(page_title="Plan de inventario", page_icon="📦", layout="wide")
st.title("📦 Plan de inventario")

st.markdown(
    """
Modelo NLP en Pyomo sobre un horizonte de 4 semanas: decide cuánto pedir (`Q`) y cuánto
queda en stock (`S`) por ingrediente y semana, minimizando compra + almacenamiento + un
costo de ordenar cóncavo, sujeto a capacidad de almacenamiento (seco/húmedo) y a un tope
de capital inmovilizado. Detalle en `src/inventario.py`.
"""
)


def _utilizacion_capacidad(plan: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for semana in sorted(plan["semana"].unique()):
        stock_semana = plan[plan["semana"] == semana]
        secos = sum(VOLUMEN_POR_KG[i] * stock_semana[stock_semana["ingrediente"] == i]["S"].sum() for i in INGREDIENTES_SECOS)
        humedos = sum(VOLUMEN_POR_KG[i] * stock_semana[stock_semana["ingrediente"] == i]["S"].sum() for i in INGREDIENTES_HUMEDOS)
        filas.append({"semana": semana, "tipo": "Secos", "uso": secos})
        filas.append({"semana": semana, "tipo": "Húmedos", "uso": humedos})
    return pd.DataFrame(filas)


def _mostrar_plan(
    plan: pd.DataFrame, vmax_secos: float, vmax_humedos: float, costo_fijo_orden: float, key_prefix: str
) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cantidad a pedir (Q) por semana")
        fig = px.bar(plan, x="semana", y="Q", color="ingrediente", barmode="group")
        fig.update_layout(xaxis_title="Semana", yaxis_title="Q (kg)", height=420)
        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_q")
    with col2:
        st.subheader("Inventario (S) por semana")
        fig = px.line(plan, x="semana", y="S", color="ingrediente", markers=True)
        fig.update_layout(xaxis_title="Semana", yaxis_title="S (kg)", height=420)
        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_s")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Desglose de costos")
        costos = calcular_costos(plan, costo_fijo_orden=costo_fijo_orden)
        fig = px.pie(
            names=["Compra", "Almacenamiento", "Orden"],
            values=[costos["compra"], costos["almacenamiento"], costos["orden"]],
            hole=0.4,
        )
        fig.update_layout(height=380)
        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_costos")
        st.metric("Costo total (4 semanas)", f"${costos['total']:,.0f}".replace(",", "."))
    with col2:
        st.subheader("Uso de capacidad de almacenamiento")
        uso = _utilizacion_capacidad(plan)
        vmax = {"Secos": vmax_secos, "Húmedos": vmax_humedos}
        uso["límite"] = uso["tipo"].map(vmax)
        uso["% utilizado"] = uso["uso"] / uso["límite"] * 100
        fig = px.bar(uso, x="semana", y="% utilizado", color="tipo", barmode="group")
        fig.update_layout(xaxis_title="Semana", yaxis_title="% de capacidad", height=380)
        fig.add_hline(y=100, line_dash="dash", line_color="red")
        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_capacidad")

    with st.expander("Ver plan en detalle"):
        st.dataframe(
            plan.pivot(index="semana", columns="ingrediente", values=["Q", "S"]).round(1),
            width="stretch",
            key=f"{key_prefix}_detalle",
        )


tab_plan, tab_simulador = st.tabs(["Plan calculado", "Simulador what-if"])

with tab_plan:
    plan_base = cargar_plan_inventario()
    _mostrar_plan(plan_base, VMAX_SECOS, VMAX_HUMEDOS, COSTO_FIJO_ORDEN, key_prefix="base")

with tab_simulador:
    if not solver_ipopt_disponible():
        st.warning(
            "El solver `ipopt` no está disponible en este entorno, así que no se puede "
            "re-resolver el modelo en vivo. Instalalo (`conda install -c conda-forge ipopt`) "
            "y corré la app localmente para usar el simulador."
        )
    else:
        st.caption("Ajustá los parámetros y re-resolvé el modelo NLP en vivo (unos segundos).")
        col1, col2, col3, col4 = st.columns(4)
        vmax_secos = col1.slider("Capacidad secos (m³)", 1, 20, int(VMAX_SECOS))
        vmax_humedos = col2.slider("Capacidad húmedos (m³)", 1, 20, int(VMAX_HUMEDOS))
        cmax = col3.number_input("Capital inmovilizado máx. ($)", value=float(CMAX), step=1e7, format="%.0f")
        costo_fijo_orden = col4.number_input("Costo de ordenar de referencia ($)", value=float(COSTO_FIJO_ORDEN), step=1e4, format="%.0f")

        if st.button("Recalcular plan", type="primary"):
            with st.spinner("Resolviendo el modelo NLP con ipopt..."):
                plan_simulado = recalcular_plan(vmax_secos, vmax_humedos, cmax, costo_fijo_orden)
            st.session_state["plan_simulado"] = (plan_simulado, vmax_secos, vmax_humedos, costo_fijo_orden)

        if "plan_simulado" in st.session_state:
            plan_simulado, vs, vh, k = st.session_state["plan_simulado"]
            _mostrar_plan(plan_simulado, vs, vh, k, key_prefix="simulado")
        else:
            st.info("Ajustá los parámetros de arriba y apretá **Recalcular plan**.")
