"""Carga, normalización y validación de la fuente de OSIPTEL."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from coverage_planner.constants import BASE_COLUMN_MAP, OPERATORS, REQUIRED_BASE_COLUMNS

_COVERAGE_PATTERN = re.compile(
    r"^(Bitel|Claro|Entel|Telefonica)_([2345]G)_(CG(?:\+CAR)?)$",
    re.IGNORECASE,
)


class DataValidationError(ValueError):
    """Indica que la fuente no cumple el contrato de datos esperado."""


def normalize_column_name(column: str) -> str:
    """Convierte una columna original de OSIPTEL al contrato interno."""
    if column in BASE_COLUMN_MAP:
        return BASE_COLUMN_MAP[column]

    match = _COVERAGE_PATTERN.match(str(column))
    if not match:
        return str(column).strip().lower().replace(" ", "_")

    operator, technology, coverage_type = match.groups()
    operator = "movistar" if operator.lower() == "telefonica" else operator.lower()
    suffix = "total" if "+CAR" in coverage_type.upper() else "cg"
    return f"{operator}_{technology.lower()}_{suffix}"


def normalize_source(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres, textos, identificadores y porcentajes de cobertura."""
    normalized = df.rename(columns={column: normalize_column_name(column) for column in df.columns})
    normalized = normalized.copy()

    for column in ("department", "province", "district", "classification"):
        if column in normalized:
            normalized[column] = normalized[column].astype("string").str.strip().str.upper()

    if "center_name" in normalized:
        normalized["center_name"] = (
            normalized["center_name"].astype("string").str.strip().str.upper()
        )
    if "center_id" in normalized:
        normalized["center_id"] = normalized["center_id"].astype("string").str.replace(
            r"\.0$", "", regex=True
        )

    coverage_columns = [
        column
        for column in normalized.columns
        if column.endswith("_cg") or column.endswith("_total")
    ]
    normalized[coverage_columns] = normalized[coverage_columns].apply(
        pd.to_numeric, errors="coerce"
    )
    return normalized


def validate_source(df: pd.DataFrame) -> dict[str, object]:
    """Valida el contrato y devuelve indicadores auditables de calidad."""
    missing = sorted(set(REQUIRED_BASE_COLUMNS) - set(df.columns))
    if missing:
        raise DataValidationError(f"Faltan columnas requeridas: {', '.join(missing)}")

    coverage_columns = [
        column for column in df.columns if column.endswith("_cg") or column.endswith("_total")
    ]
    if not coverage_columns:
        raise DataValidationError("No se encontraron columnas de cobertura.")

    invalid_coordinates = ~(
        df["latitude"].between(-19.0, 1.0) & df["longitude"].between(-82.0, -68.0)
    )
    invalid_coverage = ~df[coverage_columns].apply(lambda series: series.between(0.0, 1.0)).all(
        axis=1
    )

    if invalid_coordinates.any():
        raise DataValidationError(
            f"Hay {int(invalid_coordinates.sum())} coordenadas fuera del rango esperado para Perú."
        )
    if invalid_coverage.any():
        raise DataValidationError(
            f"Hay {int(invalid_coverage.sum())} filas con cobertura fuera del intervalo [0, 1]."
        )
    if df["center_id"].duplicated().any():
        raise DataValidationError("El identificador de centro poblado no es único.")

    missing_5g_operator = [
        operator for operator in OPERATORS if f"{operator}_5g_total" not in df.columns
    ]
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "departments": int(df["department"].nunique()),
        "provinces": int(df["province"].nunique()),
        "districts": int(df["district"].nunique()),
        "null_cells": int(df.isna().sum().sum()),
        "duplicate_centers": int(df["center_id"].duplicated().sum()),
        "rural_centers": int(df["classification"].eq("RURAL").sum()),
        "urban_centers": int(df["classification"].eq("URBANO").sum()),
        "coverage_columns": len(coverage_columns),
        "operators_without_5g_column": missing_5g_operator,
    }


def load_source(path: str | Path) -> tuple[pd.DataFrame, dict[str, object]]:
    """Carga Excel/Parquet, normaliza la fuente y ejecuta las validaciones."""
    source_path = Path(path)
    if not source_path.exists():
        raise FileNotFoundError(f"No existe la fuente: {source_path}")

    if source_path.suffix.lower() == ".parquet":
        source = pd.read_parquet(source_path)
    elif source_path.suffix.lower() in {".xlsx", ".xls"}:
        source = pd.read_excel(source_path, sheet_name="Dataset")
    else:
        raise ValueError("La fuente debe ser .xlsx, .xls o .parquet.")

    normalized = normalize_source(source)
    return normalized, validate_source(normalized)


def load_processed(path: str | Path) -> pd.DataFrame:
    """Carga el dataset procesado que utiliza la aplicación."""
    processed_path = Path(path)
    if not processed_path.exists():
        raise FileNotFoundError(
            f"No existe {processed_path}. Ejecute scripts/build_dataset.py primero."
        )
    return pd.read_parquet(processed_path)

