import pandas as pd
import pytest

from coverage_planner.features import build_features


def base_center() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "center_id": ["1", "2"],
            "department": ["LIMA", "LIMA"],
            "province": ["HUAROCHIRI", "HUAROCHIRI"],
            "district": ["A", "B"],
            "center_name": ["SIN COBERTURA", "CUBIERTO"],
            "classification": ["RURAL", "URBANO"],
            "latitude": [-12.0, -12.1],
            "longitude": [-76.5, -76.6],
            "claro_4g_cg": [0.0, 1.0],
            "claro_4g_total": [0.0, 1.0],
            "claro_5g_total": [0.0, 1.0],
        }
    )


def test_priority_is_bounded_and_interpretable() -> None:
    result = build_features(base_center())
    assert result["priority_score"].between(0, 100).all()
    assert result.loc[0, "priority_score"] > result.loc[1, "priority_score"]
    assert result.loc[0, "coverage_category"] == "BRECHA CRITICA"
    assert result.loc[1, "coverage_category"] == "COBERTURA ALTA"


def test_missing_operator_columns_are_zero_filled() -> None:
    result = build_features(base_center())
    assert "movistar_5g_total" in result
    assert result["movistar_5g_total"].eq(0).all()
    assert result.loc[1, "max_4g_total"] == pytest.approx(1.0)

