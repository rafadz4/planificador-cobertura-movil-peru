"""Ingeniería de características e índice territorial de prioridad."""

from __future__ import annotations

import numpy as np
import pandas as pd

from coverage_planner.constants import OPERATORS, PRIORITY_WEIGHTS, TECHNOLOGIES


def _ensure_coverage_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Añade como cero combinaciones no reportadas por la fuente."""
    result = df.copy()
    for operator in OPERATORS:
        for technology in TECHNOLOGIES:
            for coverage_type in ("cg", "total"):
                column = f"{operator}_{technology}_{coverage_type}"
                if column not in result:
                    result[column] = 0.0
    return result


def _max_and_best_operator(
    df: pd.DataFrame, technology: str, coverage_type: str
) -> tuple[pd.Series, pd.Series]:
    columns = [f"{operator}_{technology}_{coverage_type}" for operator in OPERATORS]
    values = df[columns]
    best_column = values.idxmax(axis=1)
    best_operator = best_column.str.split("_").str[0].str.title()
    return values.max(axis=1), best_operator


def build_features(df: pd.DataFrame, service_threshold: float = 0.80) -> pd.DataFrame:
    """Construye indicadores comparables y una prioridad territorial 0-100.

    El índice no usa población porque la fuente de OSIPTEL no contiene esa variable.
    Cada centro poblado es una unidad territorial y la condición rural recibe una
    ponderación explícita, documentada y configurable.
    """
    if not 0 < service_threshold <= 1:
        raise ValueError("service_threshold debe pertenecer al intervalo (0, 1].")

    result = _ensure_coverage_columns(df)
    result = result.copy()

    for technology in ("4g", "5g"):
        for coverage_type in ("cg", "total"):
            maximum, best_operator = _max_and_best_operator(result, technology, coverage_type)
            result[f"max_{technology}_{coverage_type}"] = maximum.clip(0, 1)
            result[f"best_operator_{technology}_{coverage_type}"] = best_operator
            columns = [f"{operator}_{technology}_{coverage_type}" for operator in OPERATORS]
            result[f"operator_count_{technology}_{coverage_type}"] = (
                result[columns].ge(service_threshold).sum(axis=1).astype("int8")
            )

    result["guaranteed_4g_gap"] = 1.0 - result["max_4g_cg"]
    result["total_4g_gap"] = 1.0 - result["max_4g_total"]
    result["total_5g_gap"] = 1.0 - result["max_5g_total"]
    result["competition_gap"] = 1.0 - result["operator_count_4g_total"] / len(OPERATORS)
    result["rural_priority"] = result["classification"].eq("RURAL").astype(float)

    result["priority_score"] = 100.0 * sum(
        PRIORITY_WEIGHTS[component] * result[component]
        for component in PRIORITY_WEIGHTS
    )
    result["priority_score"] = result["priority_score"].clip(0, 100).round(2)

    result["coverage_category"] = np.select(
        [result["max_4g_total"] < 0.20, result["max_4g_total"] < 0.80],
        ["BRECHA CRITICA", "COBERTURA PARCIAL"],
        default="COBERTURA ALTA",
    )
    result["has_4g_guaranteed"] = result["max_4g_cg"].ge(service_threshold)
    result["has_5g_total"] = result["max_5g_total"].ge(service_threshold)
    return result

