# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

An Operations Research pipeline that turns two years of bakery sales data into an ingredient
replenishment plan: ABC-XYZ classification → SARIMA demand forecasting per ingredient → an NLP
(Pyomo) inventory optimization model. See `README.md` for the full methodology write-up (in
Spanish, matching the codebase and the report in `docs/`).

The pipeline is a package of Python modules under `src/`, each one a pipeline stage with a public
function plus a `if __name__ == "__main__":` guard so it can run standalone. There is no test suite —
correctness is judged by the MAE/RMSE/MAPE/bias printed by `src/pronosticos.py` and by inspecting the
generated CSVs/plots.

## Running

```bash
pip install -r requirements.txt
python -m src.pipeline                 # full pipeline, 8 stages, opens plot windows
python -m src.pipeline --sin-graficos   # same, without blocking on plt.show()
python -m src.analisis_abc              # any single stage can run standalone with -m
```

Modules use relative imports (`from .config import ...`), so they must be run as `python -m
src.<module>` from the repo root — running `python src/<module>.py` directly will fail.

`ipopt` (the NLP solver used by `src/inventario.py`) is not pip-installable; it must be on PATH
separately (e.g. `conda install -c conda-forge ipopt`).

## Pipeline stages (in order — each reads the previous stage's output)

1. `src/limpieza.py` — `data/raw/Bakery sales.csv` → `data/interim/Bakery sales- Clean.csv`.
2. `src/analisis_abc.py` — Pareto/ABC classification by revenue share → `data/results/Analisis ABC.csv`.
3. `src/analisis_xyz.py` — XYZ classification by coefficient of variation → `data/results/ANALISIS XYZ.csv`.
4. `src/demanda_ingredientes.py` — explodes class-A product sales into ingredient demand via the
   `RECETAS` dict (grams/mL per unit sold) → `data/interim/demanda_{diaria,semanal,mensual}.csv`.
   **`RECETAS` is the source of truth for ingredient composition** and only covers class-A products —
   if the ABC classification changes and a new product becomes class A, add its recipe here or it
   silently contributes zero demand.
5. `src/pronosticos.py` — weekly SARIMA(1,1,2)(1,1,0,52) per ingredient (order picked via
   `src/auto_arima.py`), 80/20 train-test metrics, 52-week forecast → one
   `data/results/PRONOSTICO_<ingrediente>_SARIMA.csv` per ingredient, plus
   `data/results/metricas_pronostico.csv` (MAE/RMSE/MAPE/bias per ingredient, consumed by the app).
6. `src/unificar_pronosticos.py` — merges the eight forecast CSVs on `date` → `data/results/PRONOSTICO_UNIFICADO.csv`.
7. `src/demanda_mensual.py` — monthly average demand summary → `data/results/monthly_demand.csv`.
8. `src/inventario.py` — Pyomo NLP over a 4-week horizon: continuous order quantity `Q` and inventory
   `S` per ingredient/period, concave ordering-cost term (no binary lot variable), storage-volume and
   capital-tied-up constraints, solved with `ipopt` → `data/results/plan_inventario.csv`.
   `construir_modelo`/`optimizar_inventario` take `vmax_secos`/`vmax_humedos`/`cmax`/`costo_fijo_orden`
   as optional keyword overrides (default to the module constants) so the Streamlit app's what-if
   simulator can re-solve with custom parameters without touching the versioned plan
   (`optimizar_inventario(..., guardar=False)`). `calcular_costos(plan)` decomposes a solved plan's
   total cost into compra/almacenamiento/orden for display.

`src/series_de_tiempo.py` and `src/graficos_demanda.py` are diagnostic-only (no file outputs, just
`plt.show()`) and aren't part of `src/pipeline.py`.

There is also an independent LINGO formulation of the same inventory problem in `lingo/` (`Modelo de
Inventario.lg4`, `lingo_demand.txt`, plus manually-exported `demanda_*_sin_week.csv` inputs), kept as
cross-validation against the Pyomo results — not reproducible from Python.

## Streamlit app (`app/`)

`streamlit run app/Inicio.py` — a 5-page dashboard (`app/Inicio.py` + `app/pages/`) over the same
data, sharing loaders/constants from `app/utils.py`. It reads `data/results/` directly (versioned,
no recompute needed) and lazily regenerates `data/interim/` on first load via
`asegurar_interim()` (calls `limpieza`/`demanda_ingredientes`, cheap, no `ipopt` needed) since that
folder is gitignored. The inventory page has a what-if tab that calls `recalcular_plan()` (wraps
`src.inventario.optimizar_inventario(..., guardar=False)`) live if `ipopt` is available
(`solver_ipopt_disponible()`), and is hidden behind a warning otherwise.

Each page file starts with a `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))`
before importing `utils` — Streamlit does **not** automatically add `app/` to `sys.path` for modules
imported from `app/pages/*.py`, despite it being a common assumption; without that line `from utils
import ...` raises `ModuleNotFoundError` (caught during development via
`streamlit.testing.v1.AppTest`, not by just curling the running server — the shell HTML returns 200
even when a page's script throws).

When adding widgets to a function called more than once per page run (e.g. `_mostrar_plan()` in the
inventory page, called once for the static plan and once for the simulated one), every
`st.plotly_chart`/`st.dataframe`/etc. needs an explicit unique `key=` — Streamlit auto-generates
element IDs from type + params and raises `StreamlitDuplicateElementId` when two calls produce
identical parameters.

## Data layout

- `data/raw/` — original dataset, never modified.
- `data/interim/` — intermediate files regenerated by the pipeline; gitignored (`data/interim/*` in
  `.gitignore`), so a fresh clone needs `python -m src.pipeline` run at least through stage 4 before
  stages 5+ have their inputs.
- `data/results/` — final outputs, versioned in git.
- `reports/figures/` — final plots, versioned in git.

CSV filenames are the interface between stages (hardcoded relative paths via `src/config.py`, not a
shared schema/config object) — if you rename an output file, update every downstream module that reads it.

## History / things that look like bugs but are documented decisions

- An earlier inventory model formulation (MILP with a binary "order placed" variable `y` and a fixed
  ordering cost) was replaced by the current concave-cost NLP formulation in `src/inventario.py`
  because it converges faster with `ipopt` and avoids tuning a "big-M" constant. Not present in the
  repo anymore; mentioned in the module docstring for context.
- `src/demanda_mensual.py` originally read forecast files under a filename pattern
  (`forecast_<ingrediente>.csv`) that no other script produced — a stale reference from an earlier
  iteration. Fixed during the portfolio cleanup to read the actual
  `PRONOSTICO_<ingrediente>_SARIMA.csv` files.
- A separate reorder-point/EOQ inventory model (outputs like `solucion_optima.csv`,
  `puntos_reorden.csv`, `cantidades_optimas.csv`, `metricas_periodo.csv`) existed in an external
  Colab notebook but was never added to this repo and was intentionally dropped as non-reproducible.
