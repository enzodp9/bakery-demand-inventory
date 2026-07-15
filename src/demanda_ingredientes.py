"""Etapa 4: demanda de ingredientes derivada de las ventas de productos clase A.

RECETAS es la fuente de verdad de composición de ingredientes por producto (gramos/mL
por unidad vendida). Si la clasificación ABC cambia y un producto nuevo pasa a ser
clase A, su receta debe agregarse acá o contribuirá demanda cero silenciosamente.

Entrada:  data/results/Analisis ABC.csv, data/interim/Bakery sales- Clean.csv
Salida:   data/interim/demanda_{diaria,semanal,mensual}.csv
"""

import pandas as pd

from .config import DATA_INTERIM, DATA_RESULTS, INGREDIENTES

RECETAS = {
    "TRADITIONAL BAGUETTE": {"harina": 300, "agua": 200, "leche": 0, "levadura": 5, "sal": 5, "manteca": 0, "azucar": 0, "chocolate": 0},
    "FORMULE SANDWICH": {"harina": 250, "agua": 150, "leche": 0, "levadura": 4, "sal": 3, "manteca": 20, "azucar": 5, "chocolate": 0},
    "CROISSANT": {"harina": 250, "agua": 0, "leche": 150, "levadura": 5, "sal": 3, "manteca": 100, "azucar": 30, "chocolate": 0},
    "PAIN AU CHOCOLAT": {"harina": 250, "agua": 0, "leche": 150, "levadura": 5, "sal": 3, "manteca": 100, "azucar": 30, "chocolate": 250},
    "BANETTE": {"harina": 300, "agua": 220, "leche": 0, "levadura": 6, "sal": 4, "manteca": 0, "azucar": 0, "chocolate": 0},
    "BAGUETTE": {"harina": 300, "agua": 200, "leche": 0, "levadura": 5, "sal": 5, "manteca": 0, "azucar": 0, "chocolate": 0},
    "SPECIAL BREAD": {"harina": 300, "agua": 180, "leche": 0, "levadura": 5, "sal": 5, "manteca": 20, "azucar": 10, "chocolate": 0},
    "SANDWICH COMPLET": {"harina": 250, "agua": 150, "leche": 0, "levadura": 4, "sal": 3, "manteca": 20, "azucar": 5, "chocolate": 0},
    "TRAITEUR": {"harina": 200, "agua": 100, "leche": 0, "levadura": 4, "sal": 3, "manteca": 50, "azucar": 20, "chocolate": 0},
    "GRAND FAR BRETON": {"harina": 150, "agua": 0, "leche": 500, "levadura": 0, "sal": 2, "manteca": 50, "azucar": 100, "chocolate": 0},
    "TARTELETTE": {"harina": 200, "agua": 0, "leche": 100, "levadura": 0, "sal": 2, "manteca": 50, "azucar": 50, "chocolate": 0},
    "BRIOCHE": {"harina": 300, "agua": 0, "leche": 150, "levadura": 5, "sal": 4, "manteca": 80, "azucar": 40, "chocolate": 0},
    "VIK BREAD": {"harina": 300, "agua": 250, "leche": 0, "levadura": 6, "sal": 5, "manteca": 0, "azucar": 0, "chocolate": 0},
    "CEREAL BAGUETTE": {"harina": 300, "agua": 220, "leche": 0, "levadura": 5, "sal": 5, "manteca": 0, "azucar": 0, "chocolate": 0},
    "GD KOUIGN AMANN": {"harina": 300, "agua": 0, "leche": 0, "levadura": 0, "sal": 2, "manteca": 150, "azucar": 80, "chocolate": 0},
    "CAMPAGNE": {"harina": 350, "agua": 250, "leche": 0, "levadura": 6, "sal": 6, "manteca": 0, "azucar": 0, "chocolate": 0},
    "BOULE 400G": {"harina": 400, "agua": 280, "leche": 0, "levadura": 8, "sal": 6, "manteca": 0, "azucar": 0, "chocolate": 0},
    "MOISSON": {"harina": 300, "agua": 220, "leche": 0, "levadura": 5, "sal": 5, "manteca": 0, "azucar": 0, "chocolate": 0},
    "ECLAIR": {"harina": 200, "agua": 0, "leche": 200, "levadura": 0, "sal": 3, "manteca": 80, "azucar": 50, "chocolate": 125},
    "SAND JB EMMENTAL": {"harina": 250, "agua": 150, "leche": 0, "levadura": 4, "sal": 3, "manteca": 20, "azucar": 5, "chocolate": 0},
    "COMPLET": {"harina": 350, "agua": 250, "leche": 0, "levadura": 6, "sal": 5, "manteca": 0, "azucar": 0, "chocolate": 0},
    "KOUIGN AMANN": {"harina": 300, "agua": 0, "leche": 0, "levadura": 0, "sal": 2, "manteca": 150, "azucar": 80, "chocolate": 0},
    "PAIN BANETTE": {"harina": 300, "agua": 200, "leche": 0, "levadura": 5, "sal": 5, "manteca": 0, "azucar": 0, "chocolate": 0},
    "DIVERS VIENNOISERIE": {"harina": 250, "agua": 0, "leche": 150, "levadura": 5, "sal": 3, "manteca": 100, "azucar": 30, "chocolate": 0},
    "FINANCIER X5": {"harina": 150, "agua": 0, "leche": 0, "levadura": 0, "sal": 1, "manteca": 100, "azucar": 80, "chocolate": 0},
    "PAIN AUX RAISINS": {"harina": 250, "agua": 0, "leche": 150, "levadura": 5, "sal": 3, "manteca": 100, "azucar": 30, "chocolate": 0},
}


def calcular_demanda_ingredientes(
    ventas_path=DATA_INTERIM / "Bakery sales- Clean.csv",
    abc_path=DATA_RESULTS / "Analisis ABC.csv",
    salida_dir=DATA_INTERIM,
):
    productos_clase_a = pd.read_csv(abc_path)
    productos_clase_a = productos_clase_a[productos_clase_a["ABC_class"] == "A"]["article"]

    ventas = pd.read_csv(ventas_path)
    ventas["date"] = pd.to_datetime(ventas["date"])
    ventas_clase_a = ventas[ventas["article"].isin(productos_clase_a)].copy()

    for ingrediente in INGREDIENTES:
        ventas_clase_a[ingrediente] = ventas_clase_a.apply(
            lambda fila: RECETAS.get(fila["article"], {}).get(ingrediente, 0) * fila["quantity"],
            axis=1,
        )

    salida_dir.mkdir(parents=True, exist_ok=True)

    demanda_diaria = ventas_clase_a.groupby("date")[INGREDIENTES].sum().reset_index()
    demanda_diaria.to_csv(salida_dir / "demanda_diaria.csv", index=False)

    ventas_clase_a["week"] = ventas_clase_a["date"].dt.to_period("W")
    demanda_semanal = ventas_clase_a.groupby("week")[INGREDIENTES].sum().reset_index()
    demanda_semanal.to_csv(salida_dir / "demanda_semanal.csv", index=False)

    ventas_clase_a["month"] = ventas_clase_a["date"].dt.to_period("M")
    demanda_mensual = ventas_clase_a.groupby("month")[INGREDIENTES].sum().reset_index()
    demanda_mensual.to_csv(salida_dir / "demanda_mensual.csv", index=False)

    return demanda_diaria, demanda_semanal, demanda_mensual


if __name__ == "__main__":
    diaria, semanal, mensual = calcular_demanda_ingredientes()
    print(diaria.head())
