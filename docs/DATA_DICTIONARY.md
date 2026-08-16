# Diccionario de datos procesados

## Identificación y geografía

| Campo | Significado |
|---|---|
| `center_id` | Identificador/ubigeo del centro poblado de la fuente. |
| `department`, `province`, `district` | División administrativa declarada. |
| `center_name` | Nombre del centro poblado. |
| `classification` | Clasificación `RURAL` o `URBANO`. |
| `latitude`, `longitude` | Coordenadas WGS84. |

## Cobertura original normalizada

Las columnas siguen el patrón `{operador}_{tecnología}_{tipo}`:

- Operadores: `bitel`, `claro`, `entel`, `movistar`.
- Tecnologías: `2g`, `3g`, `4g`, `5g` cuando la fuente la reporta.
- `cg`: cobertura garantizada.
- `total`: cobertura garantizada más capacidad adicional de red (`CG+CAR`).

Los valores pertenecen al intervalo 0-1 y representan proporciones del área
poblada correspondiente.

## Características derivadas

| Campo | Definición |
|---|---|
| `max_4g_cg` | Mayor cobertura 4G garantizada entre operadores. |
| `max_4g_total` | Mayor cobertura 4G total entre operadores. |
| `max_5g_total` | Mayor cobertura 5G total entre operadores. |
| `operator_count_4g_total` | Operadores con cobertura 4G total ≥80 %. |
| `guaranteed_4g_gap` | `1 - max_4g_cg`. |
| `total_4g_gap` | `1 - max_4g_total`. |
| `total_5g_gap` | `1 - max_5g_total`. |
| `competition_gap` | `1 - operator_count_4g_total / 4`. |
| `rural_priority` | 1 para rural y 0 para urbano. |
| `priority_score` | Índice territorial ponderado de 0 a 100. |
| `coverage_category` | Brecha crítica (<20 %), parcial (<80 %) o alta. |

## Limitación fundamental

No existe una variable de población en la fuente utilizada. El puntaje representa
prioridad territorial por centro poblado y no cantidad de personas beneficiadas.

