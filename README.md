# Análisis y pronóstico de demanda para inventario de panadería

🔗 **[Ver el tablero interactivo en vivo](https://bakery-demand-inventory.streamlit.app/)**

Pipeline de punta a punta que toma dos años de datos de ventas de una panadería y
construye un plan de reposición de ingredientes: qué comprar y cuánto, minimizando
costos de compra, almacenamiento y de ordenar, sin quedarse sin stock.

El pipeline combina tres técnicas de Investigación Operativa:

1. **Clasificación ABC-XYZ** para priorizar qué productos justifican modelar en detalle.
2. **Pronóstico de series de tiempo (SARIMA)** para proyectar la demanda semanal de
   cada ingrediente.
3. **Optimización no lineal (Pyomo + ipopt)** para decidir cantidades de pedido e
   inventario sujeto a capacidad de almacenamiento y capital inmovilizado.

El informe completo con la fundamentación teórica y el análisis de resultados está en
[`docs/Informe técnico.pdf`](docs/Informe%20t%C3%A9cnico.pdf).

## Metodología

### 1. Limpieza (`src/limpieza.py`)

Estandariza columnas, corrige el formato de precios (`€1,50` → `1.50`), descarta filas
inválidas (cantidad/precio en cero, artículo vacío) y filtra outliers de cantidad con
un criterio de 3×IQR.

### 2. Clasificación ABC (`src/analisis_abc.py`)

Ordena los productos por ingresos acumulados (Pareto: A ≤80%, B ≤95%, C resto). Los
productos clase A concentran la mayor parte de la facturación y son los únicos para
los que se modela la demanda de ingredientes.

### 3. Clasificación XYZ (`src/analisis_xyz.py`)

Clasifica los productos según el coeficiente de variación de sus ventas mensuales
(X ≤50% estable, Y ≤100% variable, Z >100% errático), como contexto adicional sobre
qué tan predecible es cada producto.

### 4. Demanda de ingredientes (`src/demanda_ingredientes.py`)

Traduce las ventas de productos clase A a gramos/mL de cada ingrediente (harina, agua,
leche, levadura, sal, manteca, azúcar, chocolate) usando una tabla de recetas, y agrega
la demanda a nivel diario/semanal/mensual.

### 5. Pronóstico SARIMA (`src/pronosticos.py`)

Ajusta un modelo SARIMA(1,1,2)(1,1,0,52) semanal por ingrediente (52 = estacionalidad
anual en semanas), valida con un split 80/20 reportando MAE/RMSE/MAPE/sesgo, y
proyecta 52 semanas a futuro. `src/auto_arima.py` es la herramienta que se usó para
elegir ese orden.

### 6-7. Unificación y resumen (`src/unificar_pronosticos.py`, `src/demanda_mensual.py`)

Combinan los ocho pronósticos individuales en una única serie por fecha y calculan un
resumen de demanda promedio mensual.

### 8. Optimización de inventario (`src/inventario.py`)

Modelo NLP en Pyomo sobre un horizonte de 4 semanas: decide cantidad a pedir (`Q`) e
inventario (`S`) por ingrediente y semana, minimizando costo de compra + costo de
almacenamiento + un costo de ordenar que crece de forma cóncava con la cantidad
pedida (aproxima un costo fijo por pedido sin necesitar variables binarias de lote),
sujeto a:

- capacidad de almacenamiento separada para ingredientes secos y húmedos (m³),
- un tope de capital inmovilizado en inventario.

Como validación cruzada e independiente, el mismo problema también se resolvió con
LINGO (ver [`lingo/`](lingo/)).

## Estructura del repositorio

```
data/
  raw/        dataset original de ventas (no se modifica)
  interim/    intermedios regenerables por el pipeline (no versionados en git)
  results/    resultados finales: clasificación ABC/XYZ, pronósticos, plan de inventario
reports/
  figures/    gráficos finales (Pareto, curvas de demanda, series de tiempo)
src/          pipeline de Python, un módulo por etapa (ver arriba)
app/          tablero interactivo en Streamlit (ver más abajo)
lingo/        formulación alternativa del modelo de inventario en LINGO
docs/         informe completo (docx/pdf) y planillas de análisis ABC-XYZ
```

## Cómo correr el pipeline

Requiere Python 3.11+ y el solver [`ipopt`](https://github.com/coin-or/Ipopt) instalado
y disponible en el PATH (no se instala vía pip; se recomienda `conda install -c
conda-forge ipopt`).

```bash
pip install -r requirements.txt
python -m src.pipeline              # corre las 8 etapas y muestra los gráficos
python -m src.pipeline --sin-graficos  # corre sin abrir ventanas de matplotlib
```

También se puede correr cada etapa por separado, por ejemplo:

```bash
python -m src.analisis_abc
python -m src.inventario
```

## Tablero interactivo (Streamlit)

🔗 **[bakery-demand-inventory.streamlit.app](https://bakery-demand-inventory.streamlit.app/)**
- deployado en Streamlit Community Cloud, se redeploya solo en cada push a `main`.

Para correrlo local:

```bash
streamlit run app/Inicio.py
```

La app lee los resultados ya versionados en `data/results/` (no hace falta correr el
pipeline completo primero); solo recalcula en el momento la demanda histórica de
ingredientes (`data/interim/`, rápido, no requiere `ipopt`) si todavía no existe.

Páginas (`app/pages/`):

1. **📊 Clasificación ABC-XYZ** - gráfico de Pareto interactivo, matriz de cantidad de
   productos por combinación ABC×XYZ, y tabla filtrable por clase.
2. **🌾 Demanda de ingredientes** - curvas de demanda histórica (diaria/semanal/mensual),
   con selección de ingredientes y granularidad.
3. **🔮 Pronóstico de demanda** - demanda histórica + pronóstico SARIMA a 52 semanas por
   ingrediente, con sus métricas de validación (MAE/RMSE/MAPE/sesgo).
4. **📦 Plan de inventario** - el plan calculado (`Q`/`S` por semana, desglose de costos,
   uso de capacidad de almacenamiento) y un **simulador what-if**: ajustá capacidad de
   almacenamiento, capital inmovilizado y costo de ordenar, y volvé a resolver el modelo
   NLP en vivo (unos segundos con `ipopt`) sin pisar el plan versionado en git.

Si `ipopt` no está disponible en el entorno, el simulador se deshabilita automáticamente
y el resto de la app funciona igual (todo lo demás solo lee `data/results/`).

## Licencia

MIT - ver [`LICENSE`](LICENSE).
