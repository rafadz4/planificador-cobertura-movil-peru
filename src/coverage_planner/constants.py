"""Constantes y metadatos compartidos por el proyecto."""

import os
from pathlib import Path

_PACKAGE_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_WORKING_PROJECT_ROOT = Path.cwd()
PROJECT_ROOT = (
    _WORKING_PROJECT_ROOT
    if (_WORKING_PROJECT_ROOT / "data" / "processed").exists()
    else _PACKAGE_PROJECT_ROOT
)
PROCESSED_DATA = Path(
    os.getenv(
        "COVERAGE_DATA_PATH",
        str(PROJECT_ROOT / "data" / "processed" / "coverage_centers.parquet"),
    )
)
QUALITY_REPORT = PROCESSED_DATA.with_name("quality_report.json")

SOURCE_URL = (
    "https://www.datosabiertos.gob.pe/sites/default/files/"
    "Porcentaje%20de%20cobertura%20movil%20por%20centro%20poblado%20"
    "empresa%20operadora%20y%20tecnolog%C3%ADa_F.xlsx"
)
SOURCE_PAGE = (
    "https://www.datosabiertos.gob.pe/dataset/"
    "porcentaje-de-cobertura-m%C3%B3vil-por-centro-poblado-empresa-operadora-y-"
    "tecnolog%C3%ADa"
)

OPERATORS = ("bitel", "claro", "entel", "movistar")
TECHNOLOGIES = ("2g", "3g", "4g", "5g")

BASE_COLUMN_MAP = {
    "Ubigeo": "center_id",
    "Departamento": "department",
    "Provincia": "province",
    "Distrito": "district",
    "CentroPoblado": "center_name",
    "Clasificacion": "classification",
    "Latitud": "latitude",
    "Longitud": "longitude",
}

REQUIRED_BASE_COLUMNS = tuple(BASE_COLUMN_MAP.values())

PRIORITY_WEIGHTS = {
    "guaranteed_4g_gap": 0.45,
    "total_4g_gap": 0.20,
    "total_5g_gap": 0.15,
    "competition_gap": 0.10,
    "rural_priority": 0.10,
}
