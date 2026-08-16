"""Selección de sitios candidatos mediante máxima cobertura."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from ortools.sat.python import cp_model


@dataclass
class OptimizationResult:
    """Resultado auditable del problema de localización."""

    selected_sites: pd.DataFrame
    covered_centers: pd.DataFrame
    objective_score: float
    total_demand_score: float
    coverage_rate: float
    status: str
    radius_km: float


def haversine_matrix(
    demand_latitude: np.ndarray,
    demand_longitude: np.ndarray,
    candidate_latitude: np.ndarray,
    candidate_longitude: np.ndarray,
) -> np.ndarray:
    """Matriz de distancias geodésicas aproximadas en kilómetros."""
    demand_lat = np.radians(np.asarray(demand_latitude, dtype=float))[:, None]
    demand_lon = np.radians(np.asarray(demand_longitude, dtype=float))[:, None]
    candidate_lat = np.radians(np.asarray(candidate_latitude, dtype=float))[None, :]
    candidate_lon = np.radians(np.asarray(candidate_longitude, dtype=float))[None, :]
    delta_lat = candidate_lat - demand_lat
    delta_lon = candidate_lon - demand_lon
    a = np.sin(delta_lat / 2) ** 2 + np.cos(demand_lat) * np.cos(candidate_lat) * np.sin(
        delta_lon / 2
    ) ** 2
    return 6371.0088 * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def _validate_input(demand: pd.DataFrame, n_sites: int, radius_km: float, weight_col: str) -> None:
    required = {"latitude", "longitude", weight_col}
    missing = sorted(required - set(demand.columns))
    if missing:
        raise ValueError(f"Faltan columnas para optimizar: {', '.join(missing)}")
    if demand.empty:
        raise ValueError("No hay centros poblados en el alcance seleccionado.")
    if n_sites < 1:
        raise ValueError("n_sites debe ser al menos 1.")
    if radius_km <= 0:
        raise ValueError("radius_km debe ser mayor que cero.")
    if (demand[weight_col] < 0).any():
        raise ValueError("Los pesos de demanda no pueden ser negativos.")


def solve_max_coverage(
    demand: pd.DataFrame,
    n_sites: int,
    radius_km: float,
    weight_col: str = "priority_score",
    max_candidates: int = 120,
    time_limit_seconds: float = 12.0,
) -> OptimizationResult:
    """Maximiza prioridad territorial atendida bajo un límite de sitios.

    Los candidatos son los centros con mayor prioridad del alcance. Esta versión
    supone cobertura circular homogénea y no reemplaza una ingeniería de detalle.
    """
    _validate_input(demand, n_sites, radius_km, weight_col)
    if max_candidates < 1:
        raise ValueError("max_candidates debe ser al menos 1.")

    working = demand.reset_index(drop=False).rename(columns={"index": "source_index"})
    candidate_count = min(max_candidates, len(working))
    candidates = working.nlargest(candidate_count, weight_col).reset_index(drop=True)
    n_sites = min(n_sites, candidate_count)

    distances = haversine_matrix(
        working["latitude"].to_numpy(),
        working["longitude"].to_numpy(),
        candidates["latitude"].to_numpy(),
        candidates["longitude"].to_numpy(),
    )
    coverage = distances <= radius_km

    model = cp_model.CpModel()
    site_vars = [model.new_bool_var(f"site_{j}") for j in range(candidate_count)]
    covered_vars = [model.new_bool_var(f"covered_{i}") for i in range(len(working))]
    model.add(sum(site_vars) <= n_sites)

    for i in range(len(working)):
        covering_sites = np.flatnonzero(coverage[i])
        if len(covering_sites):
            model.add(covered_vars[i] <= sum(site_vars[j] for j in covering_sites))
        else:
            model.add(covered_vars[i] == 0)

    integer_weights = np.maximum(1, np.rint(working[weight_col].to_numpy() * 100)).astype(int)
    model.maximize(sum(int(integer_weights[i]) * covered_vars[i] for i in range(len(working))))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 42
    status_code = solver.solve(model)
    status = solver.status_name(status_code)

    selected_positions = [j for j, variable in enumerate(site_vars) if solver.value(variable)]
    covered_positions = [i for i, variable in enumerate(covered_vars) if solver.value(variable)]
    selected = candidates.iloc[selected_positions].copy()
    selected["site_number"] = range(1, len(selected) + 1)
    covered = working.iloc[covered_positions].copy()

    objective = float(covered[weight_col].sum())
    total = float(working[weight_col].sum())
    return OptimizationResult(
        selected_sites=selected,
        covered_centers=covered,
        objective_score=round(objective, 2),
        total_demand_score=round(total, 2),
        coverage_rate=round(objective / total if total else 0.0, 4),
        status=status,
        radius_km=radius_km,
    )

