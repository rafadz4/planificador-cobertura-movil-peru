# Informe final — Planificador inteligente de cobertura móvil

**Proyecto de portafolio:** Ingeniería Electrónica, telecomunicaciones y ciencia de datos  
**Caso piloto:** provincia de Huarochirí, Lima  
**Cobertura del dataset:** Perú, 2025  
**Fecha de cierre:** 15 de agosto de 2026

## 1. Resumen ejecutivo

Se desarrolló una aplicación reproducible que transforma datos públicos de
OSIPTEL en una herramienta de apoyo para identificar brechas de cobertura móvil,
explorar modelos de propagación y proponer ubicaciones candidatas para nuevas
estaciones mediante optimización combinatoria.

El producto final integra 108 115 centros poblados del Perú. El piloto de
Huarochirí contiene 1 326 centros poblados y permite demostrar una cadena completa
de trabajo: adquisición y validación de datos, ingeniería de variables, análisis
geográfico, modelamiento radioeléctrico, optimización, visualización y pruebas.

No es una herramienta de ingeniería de detalle ni reemplaza mediciones de campo.
Su propósito es producir una primera priorización territorial transparente y
reproducible.

## 2. Problema y objetivo

Los porcentajes de cobertura publicados por operador, tecnología y centro poblado
son útiles, pero no responden directamente tres preguntas de planificación:

1. ¿En qué localidades existe una brecha territorial más severa?
2. ¿Qué alcance aproximado tendría una estación bajo distintos supuestos de RF?
3. ¿Qué conjunto limitado de ubicaciones candidatas cubre la mayor prioridad?

El proyecto responde esas preguntas con un índice interpretable, tres modelos de
propagación y un modelo de máxima cobertura.

## 3. Stack utilizado y justificación

| Componente | Tecnología | Motivo |
|---|---|---|
| Lenguaje | Python 3.12 | Ecosistema común a datos, RF, optimización y aplicaciones |
| Procesamiento | pandas y NumPy | Limpieza, validación e ingeniería de variables |
| Datos espaciales | GeoPandas, Shapely y PyProj | Operaciones geográficas y sistemas de coordenadas |
| Almacenamiento | Parquet y DuckDB | Consultas rápidas y formato compacto, sin administrar un servidor |
| Modelos RF | Implementación propia validada | FSPL, Okumura-Hata y COST-231 Hata con parámetros visibles |
| Optimización | OR-Tools CP-SAT | Resolución exacta del problema discreto de máxima cobertura |
| Aplicación | Streamlit | Prototipo interactivo reproducible con poco código de interfaz |
| Gráficos y mapas | Plotly y PyDeck | Visualizaciones interactivas y mapas geográficos |
| Calidad | pytest, Ruff y GitHub Actions | Pruebas, estilo consistente e integración continua |
| Portabilidad | Docker | Entorno de ejecución repetible |

Este stack prioriza reproducibilidad y facilidad para una demostración de
portafolio. PostGIS o una arquitectura distribuida serían innecesarios para el
volumen actual, aunque podrían incorporarse en una versión empresarial.

## 4. Fuente y preparación de datos

La fuente principal es el recurso **Porcentaje de cobertura móvil por centro
poblado, empresa operadora y tecnología**, publicado por OSIPTEL en la Plataforma
Nacional de Datos Abiertos:

<https://www.datosabiertos.gob.pe/dataset/porcentaje-de-cobertura-m%C3%B3vil-por-centro-poblado-empresa-operadora-y-tecnolog%C3%ADa>

Los campos distinguen cobertura garantizada (`CG`) y cobertura total
(`CG+CAR`). El flujo conserva los datos originales, normaliza nombres, valida
rangos, genera indicadores derivados y publica archivos Parquet y DuckDB.

### Controles de calidad

| Control | Resultado |
|---|---:|
| Filas procesadas | 108 115 |
| Departamentos | 25 |
| Provincias | 196 |
| Distritos | 1 734 |
| Celdas nulas | 0 |
| IDs de centro poblado duplicados | 0 |
| Centros rurales | 104 361 |
| Centros urbanos | 3 754 |
| Columnas de cobertura | 28 |

Las coordenadas y los porcentajes quedaron dentro de rangos válidos. La fuente no
incluye una columna 5G para Movistar; en comparaciones agregadas esa combinación
no reportada se completa con cero y queda registrada en el reporte de calidad.

### Integridad de artefactos

| Archivo | Tamaño | SHA-256 |
|---|---:|---|
| Excel oficial descargado | 23 647 019 bytes | `5F395875486B3FED23CEC56946B3ABAF8BA0549087D0383CD05FC7AC398A5349` |
| `coverage_centers.parquet` | 10 310 685 bytes | `9F5D233D472ABE7AD52E7C8653DFC18F19C4BD7C3A5E0CE48FA03A8869FA1F6C` |
| `coverage.duckdb` | 9 711 616 bytes | `BB37F08AF9ECA9F599B7D092E4E1D7C75A540260F7823F526D46C1C795B6FCF7` |

## 5. Metodología

### Índice de prioridad territorial

El puntaje de 0 a 100 utiliza una suma ponderada:

- 45 %: brecha de cobertura 4G garantizada.
- 20 %: brecha de cobertura 4G total.
- 15 %: brecha de cobertura 5G total.
- 10 %: baja diversidad de operadores 4G.
- 10 %: prioridad rural explícita.

La clasificación 4G se define con el mejor valor total disponible entre
operadores: crítica por debajo de 20 %, parcial entre 20 % y 80 %, y alta desde
80 %.

### Simulación radioeléctrica

La aplicación implementa FSPL, Okumura-Hata y COST-231 Hata. También calcula un
presupuesto de enlace parametrizable a partir de potencia, ganancias, pérdidas,
sensibilidad y margen. Cada modelo advierte sus rangos de validez; por ejemplo,
Hata se limita a distancias de hasta 20 km.

### Optimización

Se formula un problema de máxima cobertura: elegir como máximo `N` ubicaciones
entre los centros candidatos para maximizar la suma de prioridad cubierta dentro
de un radio seleccionado. OR-Tools CP-SAT resuelve el modelo binario y devuelve
estado, sitios elegidos y cobertura obtenida.

## 6. Resultados

### Panorama nacional

| Indicador | Resultado |
|---|---:|
| Centros con condición 4G crítica | 38 216 |
| Centros con condición 4G parcial | 9 001 |
| Centros con condición 4G alta | 60 898 |
| Centros con 4G garantizada ≥ 80 % | 12,12 % |
| Centros con 5G total ≥ 80 % | 0,33 % |
| Prioridad territorial media | 77,46 / 100 |

### Caso piloto de Huarochirí

| Indicador | Resultado |
|---|---:|
| Centros poblados | 1 326 |
| Distritos | 32 |
| Centros rurales | 1 278 |
| Condición 4G crítica | 597 |
| Condición 4G parcial | 139 |
| Condición 4G alta | 590 |
| Prioridad territorial media | 83,94 / 100 |

### Escenario de optimización demostrativo

Se seleccionaron cinco sitios, un radio de 6 km y los 120 centros con mayor
prioridad como candidatos. El solucionador obtuvo estado **OPTIMAL**:

- 5 sitios seleccionados.
- 257 centros poblados cubiertos.
- 18,71 % de la prioridad territorial total cubierta.
- Puntaje cubierto: 20 820,83 de 111 305,08.
- Sitios candidatos: Moralla (Matucana), Singuna (Callahuanca), Canchayoc
  (Carampoma), Chaucansa (Cuenca) y Aliso (Huarochirí).

Como comprobación algorítmica, se comparó el resultado con 1 000 selecciones
aleatorias de cinco sitios sobre el mismo conjunto candidato. La cobertura media
aleatoria fue 7,91 % y el percentil 95 fue 11,37 %. El modelo optimizado obtuvo
una mejora relativa de 136,59 % frente a la media aleatoria.

Esta comparación valida el comportamiento del optimizador bajo sus supuestos; no
valida cobertura real en campo.

## 7. Producto entregado

La aplicación contiene cuatro secciones:

1. **Brechas:** mapa, filtros territoriales, métricas y comparación por operador.
2. **Simulador RF:** presupuesto de enlace, curvas y alcance aproximado.
3. **Optimizador:** selección de sitios, mapa de resultados y descarga CSV.
4. **Metodología:** fórmulas, supuestos y advertencias.

Además se incluyen scripts de descarga y construcción del dataset, consultas SQL,
diccionario de datos, pruebas automatizadas, configuración de CI y Dockerfile.

## 8. Verificación técnica

- 11 pruebas automatizadas aprobadas.
- Revisión estática con Ruff sin observaciones.
- Prueba automática de carga de la aplicación aprobada.
- Servicio local verificado mediante su endpoint de salud.
- Revisión visual de las pestañas Brechas, Simulador RF y Optimizador.
- Optimización interactiva verificada con el escenario de cinco sitios.

## 9. Limitaciones

- La fuente no contiene población, demanda, tráfico, ingresos ni costos; por ello
  el índice es territorial y no representa impacto poblacional o retorno de
  inversión.
- `CG+CAR` incluye capacidad adicional cuya disponibilidad o desempeño puede ser
  variable; no debe interpretarse como garantía equivalente a `CG`.
- Los radios de cobertura del optimizador son círculos geodésicos simplificados.
- No se incorporan relieve, clutter, edificios, altura real de antenas,
  interferencia, espectro, backhaul ni permisos.
- Los centros seleccionados son candidatos analíticos, no ubicaciones finales de
  torres.
- Los resultados requieren drive test, modelos con terreno y revisión de un
  ingeniero RF antes de cualquier decisión de despliegue.

## 10. Ejecución

Desde la raíz del proyecto, con Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
streamlit run app.py
```

Para verificar el proyecto:

```powershell
ruff check .
pytest -q
```

## 11. Próximas mejoras recomendadas

1. Integrar población de centros poblados del INEI y demanda estimada.
2. Agregar un modelo digital de elevación y perfiles de terreno.
3. Incorporar costos, restricciones de backhaul y capacidad para optimización
   multiobjetivo.
4. Calibrar pérdidas con mediciones o datos de drive test.
5. Publicar una demo y acompañarla con una ficha breve para LinkedIn y GitHub.

## 12. Conclusión

El proyecto cumple su propósito como portafolio interdisciplinario: conecta
telecomunicaciones, programación, ciencia de datos y optimización con un problema
peruano relevante. También mantiene una frontera clara entre priorización
analítica y planificación RF de ingeniería, lo que hace sus resultados útiles sin
presentar estimaciones simplificadas como cobertura real.
