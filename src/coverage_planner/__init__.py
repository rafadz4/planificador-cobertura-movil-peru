"""Herramientas para analizar y planificar cobertura móvil en el Perú."""

from coverage_planner.features import build_features
from coverage_planner.optimization import OptimizationResult, solve_max_coverage
from coverage_planner.rf import LinkBudget, estimate_radius_km

__all__ = [
    "LinkBudget",
    "OptimizationResult",
    "build_features",
    "estimate_radius_km",
    "solve_max_coverage",
]

__version__ = "1.0.0"
