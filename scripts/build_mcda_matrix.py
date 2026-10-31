"""Gera a matriz D023 com homogeneidade de receitas por grupo de sinter.

Não otimiza novamente nem altera os resultados da GVNS.
Exemplo: python scripts/build_mcda_matrix.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRITERIA = ("f1", "f2", "f3", "c4")
MATRIX_FIELDS = (
    "alternative_id", "f1", "f2", "f3", "c4",
    "representative_run_id", "source_run_ids", "sources_count",
    "method", "configuration", "seed", "composition_sha256",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _json_list(raw: str, label: str) -> list[str]:
    try:
        items = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: JSON inválido") from exc
    if not isinstance(items, list) or not items or not all(isinstance(x, str) for x in items):
        raise ValueError(f"{label}: esperado vetor JSON não vazio de strings")
    if len(items) != len(set(items)):
        raise ValueError(f"{label}: origens repetidas")
    return items


def _composition_signature(composition: dict[str, list[str]]) -> str:
    data = json.dumps(composition, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _validate_composition(
    composition: object,
    pile_specs: dict[str, tuple[str, int]],
) -> tuple[dict[str, list[str]], str]:
    if not isinstance(composition, dict) or set(composition) != set(pile_specs):
        raise ValueError("Conjunto de pilhas diferente do da instância")
    for pile, slots in composition.items():
        if not isinstance(slots, list) or not slots:
            raise ValueError(f"Pilha {pile}: composição inválida")
        if not all(isinstance(m, str) and m for m in slots):
            raise ValueError(f"Pilha {pile}: identificadores de minério inválidos")
        expected = pile_specs[pile][1]
        if len(slots) != expected:
            raise ValueError(f"Pilha {pile}: esperado {expected} caminhões, recebido {len(slots)}")
    return composition, _composition_signature(composition)


def _pile_specs(piles_csv: Path) -> dict[str, tuple[str, int]]:
    if not piles_csv.is_file():
        raise FileNotFoundError(f"Instância de pilhas não encontrada: {piles_csv}")
    rows = _read_csv(piles_csv)
    if not rows:
        raise ValueError("Arquivo de pilhas vazio")
    specs: dict[str, tuple[str, int]] = {}
    for row in rows:
        pile, group = row["pile_id"], row["group_id"]
        trucks = float(row["mass_kt"]) / 2.0
        if not trucks.is_integer() or trucks <= 0 or pile in specs or not group:
            raise ValueError(f"Pilha inválida: {pile}")
        specs[pile] = (group, int(trucks))
    return specs


def recipe_heterogeneity(
    composition: dict[str, list[str]],
    pile_specs: dict[str, tuple[str, int]],
) -> float:
    """C4 = distância de variação total média das receitas à receita do grupo.

    Receita da pilha: r_ip = x_ip/n_p.
    Receita de referência do grupo: R_ig = soma_p x_ip / soma_p n_p.
    Distância por pilha: 0.5 * soma_i |r_ip - R_i,g(p)|.
    C4: média aritmética das distâncias de todas as pilhas (0 <= C4 <= 1).

    É uma proxy operacional, independente das fórmulas de custo e qualidade.
    """
    from collections import defaultdict

    _validate_composition(composition, pile_specs)
    usage_per_group: dict[str, Counter[str]] = defaultdict(Counter)
    total_trucks: Counter[str] = Counter()
    for pile, slots in composition.items():
        group, count = pile_specs[pile]
        usage_per_group[group].update(slots)
        total_trucks[group] += count

    distances = []
    for pile, slots in composition.items():
        group, count = pile_specs[pile]
        this_recipe = Counter(slots)
        group_usage = usage_per_group[group]
        distance = 0.5 * sum(
            abs(this_recipe[mineral] / count - group_usage[mineral] / total_trucks[group])
            for mineral in set(this_recipe) | set(group_usage)
        )
        distances.append(distance)
    return statistics.mean(distances)

def rank_average(values: list[float]) -> list[float]:
    """Postos médios nas ocorrências de empate, em ordem crescente."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        avg_rank = (start + 1 + end) / 2
        for pos in order[start:end]:
            ranks[pos] = avg_rank
        start = end
    return ranks


def spearman(values_x: list[float], values_y: list[float]) -> float | None:
    if len(values_x) != len(values_y) or len(values_x) < 2:
        return None
    x, y = rank_average(values_x), rank_average(values_y)
    avg_x, avg_y = statistics.mean(x), statistics.mean(y)
    cov = sum((a - avg_x) * (b - avg_y) for a, b in zip(x, y))
    xx = sum((a - avg_x) ** 2 for a in x)
    yy = sum((b - avg_y) ** 2 for b in y)
    return cov / math.sqrt(xx * yy) if xx and yy else None


def conflicts(rows: list[dict], criterion: str) -> dict[str, int | float | None]:
    """Pares em que reduzir C4 piora o outro critério (ambos a minimizar)."""
    opposed = 0
    informative = 0
    for i, first in enumerate(rows):
        for second in rows[i + 1:]:
            a = first["c4"] - second["c4"]
            b = first[criterion] - second[criterion]
            if a == 0 or b == 0:
                continue
            informative += 1
            if a * b < 0:
                opposed += 1
    return {
        "informative_pairs": informative,
        "opposed_pairs": opposed,
        "opposed_fraction": opposed / informative if informative else None,
    }


def _float_equal(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-9)


def build_matrix(
    results: Path,
    piles_csv: Path,
    expected_alternatives: int | None = 91,
) -> tuple[list[dict], dict]:
    """Reconstrói apenas alternativas de pareto_joint.csv, sem refiltrar objetivos."""
    pareto_path = results / "pareto_joint.csv"
    if not pareto_path.is_file():
        raise FileNotFoundError(f"Frente conjunta ausente: {pareto_path}")
    front = _read_csv(pareto_path)
    if expected_alternatives is not None and len(front) != expected_alternatives:
        raise ValueError(
            f"Esperadas {expected_alternatives} alternativas; frente tem {len(front)}"
        )
    if not front:
        raise ValueError("Frente conjunta vazia")

    piles = _pile_specs(piles_csv)
    matrix = []
    used_run_ids: set[str] = set()
    for idx, point in enumerate(front, 1):
        source_ids = _json_list(point["run_ids"], f"linha {idx}/run_ids")
        values = {k: float(point[k]) for k in ("f1", "f2", "f3")}
        if not all(math.isfinite(v) for v in values.values()):
            raise ValueError(f"linha {idx}: objetivo não finito")

        origin_records = []
        for run_id in source_ids:
            if run_id in used_run_ids:
                raise ValueError(f"Execução em mais de uma alternativa: {run_id}")
            used_run_ids.add(run_id)
            run_path = results / "runs" / f"{run_id}.json"
            if not run_path.is_file():
                raise FileNotFoundError(f"Execução de origem não encontrada: {run_path}")
            run = json.loads(run_path.read_text(encoding="utf-8"))
            if run.get("run_id") != run_id:
                raise ValueError(f"Execução com ID divergente: {run_id}")
            if run.get("original_feasible") is not True or run.get("scalar_feasible") is not True:
                raise ValueError(f"Alternativa não factível: {run_id}")
            if any(not _float_equal(float(run[k]), values[k]) for k in values):
                raise ValueError(f"Objetivos inconsistentes entre frente e execução: {run_id}")
            composition, signature = _validate_composition(run.get("composition"), piles)
            c4 = recipe_heterogeneity(composition, piles)
            origin_records.append((run_id, run, c4, signature))

        # Objetivos iguais NÃO garantem o mesmo plano operacional. Se houver
        # composições distintas, a frente de 3 objetivos exige desambiguação.
        signatures = {x[3] for x in origin_records}
        if len(signatures) != 1:
            raise ValueError(
                "Mesmo vetor de objetivos com composições diferentes: "
                + ", ".join(source_ids)
                + ". Não colapsar soluções físicas distintas sem decisão explícita."
            )

        primary_id, primary_run, c4, signature = origin_records[0]
        matrix.append({
            "alternative_id": "",  # atribuído após ordenação determinística
            **values,
            "c4": c4,
            "representative_run_id": primary_id,
            "source_run_ids": json.dumps(source_ids, ensure_ascii=False),
            "sources_count": len(source_ids),
            "method": primary_run["method"],
            "configuration": primary_run["configuration"],
            "seed": int(primary_run["seed"]),
            "composition_sha256": signature,
        })

    matrix.sort(key=lambda r: (r["f1"], r["f2"], r["f3"]))
    for idx, row in enumerate(matrix, 1):
        row["alternative_id"] = f"A{idx:03d}"

    c4values = [row["c4"] for row in matrix]
    diagnostics = {
        "status": "D023_MATRIZ_GERADA",
        "source": "pareto_joint.csv e runs/<run_id>.json",
        "pareto_sha256": hashlib.sha256(pareto_path.read_bytes()).hexdigest(),
        "alternative_count": len(matrix),
        "origin_run_count": len(used_run_ids),
        "minimize": list(CRITERIA),
        "criterion_c4": {
            "definition": "distancia_variacao_total_media_receitas_ao_grupo",
            "unit": "adimensional_entre_0_e_1",
            "interpretation": (
                "heterogeneidade das proporções de minério entre pilhas do mesmo "
                "grupo de sinter; menor valor significa maior homogeneização"
            ),
            "min": min(c4values),
            "max": max(c4values),
            "mean": statistics.mean(c4values),
            "sample_std": statistics.stdev(c4values) if len(c4values) > 1 else 0.0,
            "distinct_values": len(set(c4values)),
        },
        "correlation_spearman": {
            k: spearman([row["c4"] for row in matrix], [row[k] for row in matrix])
            for k in ("f1", "f2", "f3")
        },
        "pairwise_conflict": {
            k: conflicts(matrix, k) for k in ("f1", "f2", "f3")
        },
        "minimum_c4_alternatives": [
            r["alternative_id"] for r in matrix if r["c4"] == min(c4values)
        ],
        "origin_methods": dict(sorted(Counter(r["method"] for r in matrix).items())),
        "notes": [
            "A correlação não demonstra causalidade.",
            "C4 compara proporções de minérios, não apenas o número de tipos diferentes.",
            "A receita de referência de cada grupo é ponderada por caminhões; as pilhas têm peso igual na média das distâncias.",
            "Os pesos e as funções de preferência serão definidos em D024.",
        ],
    }
    return matrix, diagnostics


def write_outputs(rows: list[dict], audit: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csvpath = output_dir / "matriz_decisao.csv"
    with csvpath.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "diagnostico_d023.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results/multi_final")
    parser.add_argument(
        "--piles", type=Path, default=ROOT / "data/example_instance/piles.csv"
    )
    parser.add_argument("--out", type=Path, default=ROOT / "results/mcda")
    parser.add_argument("--expected", type=int, default=91)
    args = parser.parse_args()
    matrix, audit = build_matrix(args.results, args.piles, args.expected)
    write_outputs(matrix, audit, args.out)
    print(f"D023: {len(matrix)} alternativas; {audit['origin_run_count']} origens")
    print(f"C4 (heterogeneidade): {audit['criterion_c4']['min']:.4f} a {audit['criterion_c4']['max']:.4f}")
    print(f"Arquivos gerados em {args.out}")


if __name__ == "__main__":
    main()
