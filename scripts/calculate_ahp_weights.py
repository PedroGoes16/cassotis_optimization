"""Calcula os pesos AHP da D024 com a fonte declarativa de seis julgamentos.

Na raiz do repositório: python scripts/calculate_ahp_weights.py
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from cassotis_optimization.mcda.ahp import calculate_ahp

ROOT = Path(__file__).resolve().parents[1]


def validate_reference_ranges(config: dict, matrix_csv: Path) -> None:
    """Confere se as amplitudes documentadas vêm da matriz D023 oficial."""
    with matrix_csv.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 91:
        raise ValueError(f"Esperadas 91 alternativas na D023; encontradas {len(rows)}.")
    for criterion in config["criteria"]:
        key = criterion["id"]
        values = [float(row[key]) for row in rows]
        expected = (criterion["observed_min"], criterion["observed_max"])
        actual = (min(values), max(values))
        if not all(math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
                   for a, b in zip(actual, expected)):
            raise ValueError(f"Intervalo da D024 difere da matriz D023 para {key}: {actual}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "data/preferencias_ahp.json")
    parser.add_argument("--matrix", type=Path, default=ROOT / "results/mcda/matriz_decisao.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "results/mcda/pesos_ahp.json")
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    validate_reference_ranges(config, args.matrix)
    result = calculate_ahp(config)
    if not result["consistent"]:
        raise SystemExit(f"Julgamentos inconsistentes: CR={result['consistency_ratio']:.6f}.")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Pesos AHP (método de colunas normalizadas):")
    for criterion, weight in result["weights"].items():
        print(f"  {criterion}: {weight:.9f} ({100*weight:.4f}%)")
    print(f"CR: {result['consistency_ratio']:.6f} (limite: {result['maximum_consistency_ratio']:.2f})")
    print(f"Resultado: {args.out}")


if __name__ == "__main__":
    main()
