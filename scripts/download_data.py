"""Descarga la fuente oficial de OSIPTEL con validación básica."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import requests

from coverage_planner.constants import SOURCE_URL

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "data" / "raw" / "osiptel_coverage.xlsx"
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Desactiva verificación TLS solo si el proxy local impide la descarga.",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(
        SOURCE_URL,
        headers={"User-Agent": "coverage-planner-peru/1.0"},
        timeout=180,
        verify=not args.insecure,
    )
    response.raise_for_status()
    if len(response.content) < 1_000_000:
        raise RuntimeError("La respuesta es demasiado pequeña para ser el Excel esperado.")
    args.output.write_bytes(response.content)
    digest = hashlib.sha256(response.content).hexdigest()
    print(f"Descargado: {args.output}")
    print(f"Bytes: {len(response.content)}")
    print(f"SHA256: {digest}")


if __name__ == "__main__":
    main()
