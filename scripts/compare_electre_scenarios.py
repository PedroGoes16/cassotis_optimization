
import csv
import json
from pathlib import Path

from cassotis_optimization.mcda.electre import electre_i


ROOT = Path(__file__).resolve().parents[1]

with (ROOT / "results/mcda/matriz_decisao.csv").open(
    encoding="utf-8", newline=""
) as file:
    alternatives = list(csv.DictReader(file))

ahp = json.loads(
    (ROOT / "results/mcda/pesos_ahp.json").read_text(
        encoding="utf-8"
    )
)

weights = ahp["weights"]

concordancias = [0.70, 0.80, 0.85]

cenarios_veto = [
    {"f1": 0.40, "f2": 0.40, "f3": 0.40, "c4": 0.40},
    {"f1": 0.20, "f2": 0.30, "f3": 0.40, "c4": 0.60},
    {"f1": 0.20, "f2": 0.40, "f3": 0.30, "c4": 0.60},
    {"f1": 0.20, "f2": 0.50, "f3": 0.50, "c4": 0.60},
    {"f1": 0.20, "f2": 0.45, "f3": 0.45, "c4": 0.60},
]

resultados = []

for concordancia in concordancias:
    for cenario in cenarios_veto:

        resumo, _ = electre_i(
            alternatives=alternatives,
            weights=weights,
            concordance_threshold=concordancia,
            veto_fractions=cenario,            
        )

        nucleo = resumo["choice_kernel"]

        resultados.append({
            "concordancia": concordancia,
            "veto_cenario": cenario,
            "relacoes": resumo["outranking_arcs"],
            "incomparaveis": resumo["pair_types"]["incomparaveis"],
            "grafo_aciclico": resumo["graph_acyclic"],
            "tamanho_nucleo": len(nucleo) if nucleo is not None else "",
            "alternativas": ";".join(nucleo) if nucleo else "",
        })


destino = ROOT / "results/mcda/sensibilidade_electre.csv"

with destino.open("w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=resultados[0].keys())
    writer.writeheader()
    writer.writerows(resultados)

for item in resultados:
    print(
        f"Concordância={item['concordancia']:.0%} | "
        f"Veto F1={item['veto_cenario']['f1']:.0%} | "
        f"Veto F2={item['veto_cenario']['f2']:.0%} | "
        f"Veto F3={item['veto_cenario']['f3']:.0%} | "
        f"Veto C4={item['veto_cenario']['c4']:.0%} | "
        f"Núcleo={item['tamanho_nucleo'] or 'não determinado'} | "
        f"Incomparáveis={item['incomparaveis']}"
    )

print(f"\nResultados salvos em {destino}")
