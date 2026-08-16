# Planificador inteligente de cobertura móvil — Perú

Herramienta para analizar brechas territoriales de cobertura móvil en el Perú y
evaluar posibles ubicaciones para nuevas estaciones.

El proyecto combina datos públicos de OSIPTEL, modelos de propagación
radioeléctrica y optimización matemática. El caso de estudio principal corresponde
a la provincia de Huarochirí, Lima.

## Objetivo

Identificar centros poblados con baja cobertura 4G/5G y generar escenarios de
expansión de red que ayuden a priorizar ubicaciones candidatas.

## Funcionalidades

- Exploración de cobertura por departamento, provincia y distrito.
- Comparación de cobertura por operador y tecnología.
- Clasificación territorial de centros poblados según su nivel de cobertura.
- Cálculo de presupuesto de enlace.
- Modelos FSPL, Okumura-Hata y COST-231 Hata.
- Optimización de ubicaciones mediante OR-Tools.
- Visualización geográfica de brechas y sitios propuestos.
- Descarga de resultados en formato CSV.

## Datos

Se procesan 108 115 centros poblados del Perú. La fuente principal es el conjunto
**Porcentaje de cobertura móvil por centro poblado, empresa operadora y
tecnología**, publicado por OSIPTEL:

<https://www.datosabiertos.gob.pe/dataset/porcentaje-de-cobertura-m%C3%B3vil-por-centro-poblado-empresa-operadora-y-tecnolog%C3%ADa>

El repositorio incluye los datos procesados en formatos Parquet y DuckDB, además
de los scripts necesarios para reconstruirlos desde la fuente.

## Tecnologías

- Python 3.12
- pandas, NumPy y GeoPandas
- Parquet, DuckDB y SQL
- Streamlit, Plotly y PyDeck
- OR-Tools
- pytest y Ruff

## Ejecución

```powershell
git clone https://github.com/rafadz4/planificador-cobertura-movil-peru.git
cd planificador-cobertura-movil-peru
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
streamlit run app.py
```

La aplicación utiliza el archivo incluido en
`data/processed/coverage_centers.parquet`.

## Pruebas

```powershell
ruff check .
pytest -q
```

## Alcance

Los resultados representan una priorización territorial. No sustituyen estudios
de campo, mediciones de señal, análisis de interferencia ni planificación RF de
detalle.

## Documentación

- [Informe técnico](docs/INFORME_FINAL.md)
- [Diccionario de datos](docs/DATA_DICTIONARY.md)
- [Atribución de la fuente](NOTICE.md)

## Licencia

El código está disponible bajo la [licencia MIT](LICENSE).

