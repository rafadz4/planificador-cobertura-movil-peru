"""Construye los artefactos reproducibles que consume la aplicación."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

from coverage_planner.data import load_source
from coverage_planner.features import build_features

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Excel o Parquet original.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed",
        help="Directorio de artefactos procesados.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    source, quality = load_source(args.input)
    featured = build_features(source)
    parquet_path = args.output_dir / "coverage_centers.parquet"
    featured.to_parquet(parquet_path, index=False)

    demo = featured[
        featured["department"].eq("LIMA") & featured["province"].eq("HUAROCHIRI")
    ]
    demo.to_csv(args.output_dir / "huarochiri_demo.csv", index=False, encoding="utf-8-sig")

    quality.update(
        {
            "critical_4g_centers": int(featured["coverage_category"].eq("BRECHA CRITICA").sum()),
            "partial_4g_centers": int(
                featured["coverage_category"].eq("COBERTURA PARCIAL").sum()
            ),
            "high_4g_centers": int(featured["coverage_category"].eq("COBERTURA ALTA").sum()),
            "guaranteed_4g_rate": round(float(featured["has_4g_guaranteed"].mean()), 6),
            "total_5g_rate": round(float(featured["has_5g_total"].mean()), 6),
            "huarochiri_centers": int(len(demo)),
            "source_file": args.input.name,
        }
    )
    (args.output_dir / "quality_report.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    database_path = args.output_dir / "coverage.duckdb"
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("DROP TABLE IF EXISTS coverage_centers")
        connection.execute(
            "CREATE TABLE coverage_centers AS SELECT * FROM read_parquet(?)", [str(parquet_path)]
        )
        connection.execute(
            """
            CREATE OR REPLACE VIEW huarochiri_priority AS
            SELECT center_id, center_name, district, classification, priority_score,
                   max_4g_cg, max_4g_total, max_5g_total, latitude, longitude
            FROM coverage_centers
            WHERE department = 'LIMA' AND province = 'HUAROCHIRI'
            ORDER BY priority_score DESC
            """
        )

    print(json.dumps(quality, ensure_ascii=False, indent=2))
    print(f"Parquet: {parquet_path}")
    print(f"DuckDB: {database_path}")


if __name__ == "__main__":
    main()
