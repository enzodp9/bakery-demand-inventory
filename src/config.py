"""Rutas compartidas por todas las etapas del pipeline.

data/raw       -> dataset original, no se modifica.
data/interim   -> archivos intermedios regenerables (no se versionan en git).
data/results   -> resultados finales del pipeline (se versionan en git).
reports/figures -> gráficos finales generados por el pipeline.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

DATA_RAW = RAIZ / "data" / "raw"
DATA_INTERIM = RAIZ / "data" / "interim"
DATA_RESULTS = RAIZ / "data" / "results"
REPORTS_FIGURES = RAIZ / "reports" / "figures"

INGREDIENTES = ["harina", "agua", "leche", "levadura", "sal", "manteca", "azucar", "chocolate"]

for _dir in (DATA_INTERIM, DATA_RESULTS, REPORTS_FIGURES):
    _dir.mkdir(parents=True, exist_ok=True)
