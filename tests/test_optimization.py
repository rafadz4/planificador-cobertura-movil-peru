import pandas as pd

from coverage_planner.optimization import haversine_matrix, solve_max_coverage


def demand_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "center_name": ["A", "B", "C"],
            "district": ["X", "X", "Y"],
            "latitude": [-12.000, -12.005, -12.200],
            "longitude": [-76.000, -76.005, -76.200],
            "priority_score": [100.0, 80.0, 20.0],
        }
    )


def test_haversine_matrix_shape_and_zero_distance() -> None:
    frame = demand_frame()
    distances = haversine_matrix(
        frame["latitude"].to_numpy(),
        frame["longitude"].to_numpy(),
        frame["latitude"].to_numpy(),
        frame["longitude"].to_numpy(),
    )
    assert distances.shape == (3, 3)
    assert distances.diagonal().max() < 1e-6


def test_optimizer_selects_high_value_cluster() -> None:
    result = solve_max_coverage(
        demand_frame(), n_sites=1, radius_km=2.0, max_candidates=3, time_limit_seconds=2
    )
    assert result.status in {"OPTIMAL", "FEASIBLE"}
    assert set(result.covered_centers["center_name"]) == {"A", "B"}
    assert result.objective_score == 180.0

