import pandas as pd
import pytest

from coverage_planner.data import DataValidationError, normalize_source, validate_source


def raw_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Ubigeo": [101010001],
            "Departamento": ["Amazonas"],
            "Provincia": ["Chachapoyas"],
            "Distrito": ["Chachapoyas"],
            "CentroPoblado": ["Caclic"],
            "Clasificacion": ["Rural"],
            "Latitud": [-6.2],
            "Longitud": [-77.9],
            "Claro_4G_CG": [0.4],
            "Claro_4G_CG+CAR": [0.9],
        }
    )


def test_normalize_source_contract() -> None:
    normalized = normalize_source(raw_frame())
    assert normalized.loc[0, "department"] == "AMAZONAS"
    assert normalized.loc[0, "classification"] == "RURAL"
    assert normalized.loc[0, "center_id"] == "101010001"
    assert normalized.loc[0, "claro_4g_cg"] == pytest.approx(0.4)
    assert normalized.loc[0, "claro_4g_total"] == pytest.approx(0.9)


def test_validate_source_rejects_invalid_coordinates() -> None:
    normalized = normalize_source(raw_frame())
    normalized.loc[0, "latitude"] = 20.0
    with pytest.raises(DataValidationError, match="coordenadas"):
        validate_source(normalized)

