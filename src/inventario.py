"""Etapa 8: optimización del plan de pedidos e inventario (horizonte de 4 semanas).

Entrada:  data/results/PRONOSTICO_UNIFICADO.csv
Salida:   data/results/plan_inventario.csv

Modelo NLP en Pyomo: minimiza costo de compra + costo de mantener inventario +
un costo de ordenar que crece de forma cóncava con la cantidad pedida
(K * (1 - exp(-alpha * Q)), calibrado con Qref para aproximar un costo fijo por
pedido sin necesitar una variable binaria de lote). Sujeto a capacidad de
almacenamiento (seco/húmedo) y a un tope de capital inmovilizado en inventario.

Requiere el solver `ipopt` disponible en el PATH (no se instala vía pip).

Nota histórica: una versión anterior de este modelo usaba una variable binaria
de "pedido realizado" por período con un costo fijo K y se resolvía como MILP.
Se reemplazó por esta formulación continua porque converge más rápido y evita
tener que fijar M (el "número suficientemente grande") de la restricción de
lote mínimo, que resultaba sensible a la escala de cada ingrediente.
"""

from math import log

import pandas as pd
from pyomo.environ import ConcreteModel, Constraint, NonNegativeReals, Objective, Set, Var, exp, minimize
from pyomo.opt import SolverFactory

from .config import DATA_RESULTS

HORIZONTE_SEMANAS = 4

COSTO_COMPRA = {"harina": 460, "leche": 1300, "levadura": 7400, "sal": 475, "manteca": 3200, "azucar": 650, "chocolate": 13000}

# Volumen ocupado por kg (m3/kg)
VOLUMEN_POR_KG = {
    "harina": 0.0525 / 25, "sal": 0.04 / 20, "azucar": 0.045 / 25,
    "leche": 0.04, "levadura": 0.045 / 0.5, "manteca": 0.00097, "chocolate": 0.00077,
}

VMAX_SECOS = 8  # m3 (harina, sal, azucar)
VMAX_HUMEDOS = 5  # m3 (leche, levadura, manteca, chocolate)
CMAX = 5e8  # capital inmovilizado máximo ($)
COSTO_FIJO_ORDEN = 150000  # K de referencia para el costo de ordenar

# Cantidad de referencia por ingrediente para calibrar alpha (ver docstring del módulo)
CANTIDAD_REFERENCIA = {
    "harina": 707.38, "leche": 73.17, "levadura": 11.93,
    "sal": 10.27, "manteca": 59.25, "azucar": 19.38, "chocolate": 51.22,
}

INGREDIENTES_SECOS = ["harina", "sal", "azucar"]
INGREDIENTES_HUMEDOS = ["leche", "levadura", "manteca", "chocolate"]


def _cargar_demanda(pronostico_path, horizonte_semanas: int):
    data = pd.read_csv(pronostico_path)
    data = data.drop(columns=["agua"], errors="ignore")
    data = data.head(horizonte_semanas)

    ingredientes = list(data.columns[1:])
    demanda = {
        (ingrediente, t + 1): data.iloc[t][ingrediente] / 1000
        for t in range(len(data))
        for ingrediente in ingredientes
    }
    return ingredientes, demanda


def construir_modelo(ingredientes, demanda, horizonte_semanas: int) -> ConcreteModel:
    periodos = range(1, horizonte_semanas + 1)
    costo_almacenamiento = {i: COSTO_COMPRA[i] * 0.023 for i in COSTO_COMPRA}
    alpha = {i: -log(0.05) / CANTIDAD_REFERENCIA[i] for i in ingredientes}

    model = ConcreteModel()
    model.ingredientes = Set(initialize=ingredientes)
    model.periodos = Set(initialize=periodos)

    model.Q = Var(model.ingredientes, model.periodos, domain=NonNegativeReals)
    model.S = Var(model.ingredientes, model.periodos, domain=NonNegativeReals)

    def balance_inventario(model, i, t):
        anterior = model.S[i, t - 1] if t > 1 else 0
        return model.S[i, t] == anterior + model.Q[i, t] - demanda[i, t]

    model.balance_inventario = Constraint(model.ingredientes, model.periodos, rule=balance_inventario)

    def capacidad_secos(model, t):
        return sum(VOLUMEN_POR_KG[i] * model.S[i, t] for i in INGREDIENTES_SECOS) <= VMAX_SECOS

    def capacidad_humedos(model, t):
        return sum(VOLUMEN_POR_KG[i] * model.S[i, t] for i in INGREDIENTES_HUMEDOS) <= VMAX_HUMEDOS

    model.capacidad_secos = Constraint(model.periodos, rule=capacidad_secos)
    model.capacidad_humedos = Constraint(model.periodos, rule=capacidad_humedos)

    def capital_inmovilizado(model, t):
        return sum(COSTO_COMPRA[i] * model.S[i, t] for i in model.ingredientes) <= CMAX

    model.capital_inmovilizado = Constraint(model.periodos, rule=capital_inmovilizado)

    def objetivo(model):
        costos_orden = sum(
            COSTO_FIJO_ORDEN * (1 - exp(-alpha[i] * model.Q[i, t]))
            for i in model.ingredientes for t in model.periodos
        )
        costos_compra = sum(
            COSTO_COMPRA[i] * model.Q[i, t] for i in model.ingredientes for t in model.periodos
        )
        costos_stock = sum(
            costo_almacenamiento[i] * model.S[i, t] for i in model.ingredientes for t in model.periodos
        )
        return costos_orden + costos_compra + costos_stock

    model.objetivo = Objective(rule=objetivo, sense=minimize)
    return model


def optimizar_inventario(
    pronostico_path=DATA_RESULTS / "PRONOSTICO_UNIFICADO.csv",
    salida=DATA_RESULTS / "plan_inventario.csv",
    horizonte_semanas: int = HORIZONTE_SEMANAS,
) -> pd.DataFrame:
    ingredientes, demanda = _cargar_demanda(pronostico_path, horizonte_semanas)
    model = construir_modelo(ingredientes, demanda, horizonte_semanas)

    solver = SolverFactory("ipopt")
    solver.options["tol"] = 1e-6
    solver.options["max_iter"] = 10000
    solver.solve(model, tee=True)

    filas = [
        {"ingrediente": i, "semana": t, "Q": model.Q[i, t].value, "S": model.S[i, t].value}
        for i in model.ingredientes
        for t in model.periodos
    ]
    plan = pd.DataFrame(filas)

    salida.parent.mkdir(parents=True, exist_ok=True)
    plan.to_csv(salida, index=False)

    print("\n===== PLAN DE PEDIDOS E INVENTARIOS (kg) =====")
    for fila in filas:
        print(f"{fila['ingrediente']:10s}  semana {fila['semana']}: Q = {fila['Q']:8.1f}  S = {fila['S']:8.1f}")

    return plan


if __name__ == "__main__":
    optimizar_inventario()
