"""Interactive explorer for the Cassotis optimization project."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from cassotis_optimization.evaluator import evaluate
from cassotis_optimization.io import load_instance
from cassotis_optimization.solution import Solution
from cassotis_optimization.visualization import plot_solution

ROOT = Path(__file__).resolve().parents[1]
DECISION_DIR = ROOT / "results" / "decision_final"
MULTI_DIR = ROOT / "results" / "multi_final"
INSTANCE_DIR = ROOT / "data" / "example_instance"
CRITERIA = ("f1", "f2", "f3", "heterogeneity")
LABELS = {
    "f1": "Custo total (R$)",
    "f2": "Desvio quadrático de SiO₂",
    "f3": "Desvio quadrático de Al₂O₃",
    "heterogeneity": "Heterogeneidade das receitas",
}


@st.cache_data
def load_artifacts() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    alternatives = pd.read_csv(DECISION_DIR / "alternatives.csv")
    promethee = pd.read_csv(DECISION_DIR / "promethee_ranking.csv")
    electre = pd.read_csv(DECISION_DIR / "electre_ranking.csv")
    sensitivity = pd.read_csv(DECISION_DIR / "sensitivity.csv")
    analysis = json.loads((DECISION_DIR / "analysis.json").read_text(encoding="utf-8"))
    return alternatives, promethee, electre, sensitivity, analysis


@st.cache_resource
def get_instance():
    return load_instance(INSTANCE_DIR)


@st.cache_data
def load_solution(alternative_id: str, run_ids_json: str) -> Solution:
    run_ids = json.loads(run_ids_json)
    if not run_ids:
        raise ValueError(f"Alternative {alternative_id} has no source run")
    run = json.loads((MULTI_DIR / "runs" / f"{run_ids[0]}.json").read_text(encoding="utf-8"))
    return Solution(
        {pile_id: tuple(minerals) for pile_id, minerals in run["composition"].items()}
    )


def selected_row(alternatives: pd.DataFrame, alternative_id: str) -> pd.Series:
    matches = alternatives.loc[alternatives["alternative_id"] == alternative_id]
    if matches.empty:
        raise KeyError(f"Alternative {alternative_id} not found")
    return matches.iloc[0]


def plot_projection(
    alternatives: pd.DataFrame,
    x: str,
    y: str,
    promethee_choice: str,
    electre_choice: str,
):
    fig, ax = plt.subplots(figsize=(8, 5.2))
    ax.scatter(alternatives[x], alternatives[y], color="#b0b7c3", s=35, alpha=0.8)
    for choice, marker, color, label, size in (
        (promethee_choice, "*", "#1565c0", "PROMETHEE II", 230),
        (electre_choice, "X", "#ef6c00", "ELECTRE III", 130),
    ):
        row = selected_row(alternatives, choice)
        ax.scatter(
            row[x],
            row[y],
            marker=marker,
            color=color,
            edgecolor="white",
            linewidth=0.8,
            s=size,
            label=f"{label}: {choice}",
            zorder=3,
        )
    ax.set_xlabel(LABELS[x])
    ax.set_ylabel(LABELS[y])
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    return fig


def normalized_comparison(alternatives: pd.DataFrame, ids: list[str]):
    rows = alternatives.set_index("alternative_id").loc[ids]
    normalized = rows[[f"norm_{criterion}" for criterion in CRITERIA]].copy()
    normalized.columns = [LABELS[criterion] for criterion in CRITERIA]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    normalized.T.plot(kind="bar", ax=ax, width=0.78)
    ax.set_ylabel("Valor normalizado (menor é melhor)")
    ax.set_ylim(0, max(1.0, float(normalized.max().max()) * 1.08))
    ax.tick_params(axis="x", rotation=15)
    ax.grid(axis="y", alpha=0.2)
    ax.legend(title="Alternativa", ncol=min(3, len(ids)))
    fig.tight_layout()
    return fig


def quality_table(solution: Solution) -> pd.DataFrame:
    instance = get_instance()
    evaluation = evaluate(solution, instance)
    rows = []
    for pile_id, quality in evaluation.quality_by_pile.items():
        pile = instance.piles[pile_id]
        rows.append(
            {
                "Pilha": pile_id,
                "Equipamento": pile.group_id,
                "Massa (kt)": pile.mass_kt,
                "FeT (%)": quality.fet_pct,
                "SiO₂ (%)": quality.sio2_pct,
                "Al₂O₃ (%)": quality.al2o3_pct,
            }
        )
    return pd.DataFrame(rows)


def composition_table(solution: Solution) -> pd.DataFrame:
    counts = solution.counts_by_pile()
    table = pd.DataFrame(
        {pile_id: dict(pile_counts) for pile_id, pile_counts in counts.items()}
    ).fillna(0).astype(int)
    table.index.name = "Minério"
    return table


st.set_page_config(
    page_title="Cassotis | Decisão multicritério",
    page_icon="⛏️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
    [data-testid="stMetricValue"] {font-size: 1.55rem;}
    .small-note {color: #59636e; font-size: 0.92rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

required = (
    DECISION_DIR / "alternatives.csv",
    DECISION_DIR / "promethee_ranking.csv",
    DECISION_DIR / "electre_ranking.csv",
    DECISION_DIR / "sensitivity.csv",
    DECISION_DIR / "analysis.json",
)
missing = [path for path in required if not path.exists()]
if missing:
    st.error("Resultados da Entrega 3 não encontrados. Execute `python scripts/run_decision_analysis.py`.")
    st.code("\n".join(str(path) for path in missing))
    st.stop()

alternatives, promethee, electre, sensitivity, analysis = load_artifacts()
baseline = analysis["baseline"]
promethee_choice = baseline["promethee_choice"]
electre_choice = baseline["electre_choice_after_tie_break"]
final_id = baseline["final_recommendation"]
final_row = selected_row(alternatives, final_id)

st.title("Otimização e decisão multicritério de pilhas de minério")
st.caption(
    "Entrega final — GVNS, Soma Ponderada, ε-restrito, PROMETHEE II e ELECTRE III"
)

with st.sidebar:
    st.header("Cenário oficial")
    st.metric("Alternativas", len(alternatives))
    st.metric("Recomendação", final_id)
    st.caption("Pesos iguais: 25% por critério")
    st.caption("q = 5% · p = 20% · veto = 60%")
    st.divider()
    st.markdown(
        "Os resultados são aproximações heurísticas. A aplicação lê os artefatos "
        "oficiais e reutiliza o avaliador central."
    )

overview_tab, pareto_tab, compare_tab, methods_tab, sensitivity_tab, final_tab = st.tabs(
    [
        "Visão geral",
        "Alternativas",
        "Comparar",
        "Métodos",
        "Sensibilidade",
        "Solução final",
    ]
)

with overview_tab:
    cols = st.columns(5)
    cols[0].metric("Alternativa", final_id)
    cols[1].metric("Custo", f"R$ {final_row['f1'] / 1_000_000:.2f} mi")
    cols[2].metric("Desvio SiO₂", f"{final_row['f2']:.4f}")
    cols[3].metric("Desvio Al₂O₃", f"{final_row['f3']:.4f}")
    cols[4].metric("Heterogeneidade", f"{final_row['heterogeneity']:.6f}")

    left, right = st.columns([1.05, 1.45])
    with left:
        st.subheader("Por que A073?")
        st.markdown(
            "A recomendação combina qualidade química intermediária com uma das receitas "
            "mais homogêneas do conjunto. PROMETHEE II e ELECTRE III convergem para A073 "
            "no cenário-base. Ela permanece vencedora em 12/15 cenários PROMETHEE e em "
            "10/15 cenários ELECTRE."
        )
        st.info(
            "Quando custo recebe peso 40%, ambos os métodos passam a recomendar A020. "
            "A decisão é robusta à maior parte das variações, mas não é independente das preferências."
        )
        with st.expander("Protocolo do cenário-base"):
            st.json(
                {
                    "pesos": {criterion: 0.25 for criterion in CRITERIA},
                    "limiar_indiferenca": 0.05,
                    "limiar_preferencia": 0.20,
                    "veto_electre": 0.60,
                    "corte_credibilidade": 0.65,
                }
            )
    with right:
        st.image(DECISION_DIR / "final_solution.png", width="stretch")

with pareto_tab:
    st.subheader("Alternativas não dominadas e escolhas")
    first, second = st.columns(2)
    x = first.selectbox("Eixo horizontal", CRITERIA, format_func=LABELS.get, index=0)
    y_options = [criterion for criterion in CRITERIA if criterion != x]
    y = second.selectbox("Eixo vertical", y_options, format_func=LABELS.get, index=0)
    projection = plot_projection(alternatives, x, y, promethee_choice, electre_choice)
    st.pyplot(projection, width="stretch")
    plt.close(projection)
    st.caption(
        "O conjunto foi filtrado por dominância em f1, f2 e f3. A heterogeneidade foi "
        "adicionada somente na tomada de decisão."
    )
    display = alternatives[["alternative_id", *CRITERIA]].copy()
    display["f1"] = display["f1"] / 1_000_000
    st.dataframe(
        display.rename(
            columns={
                "alternative_id": "Alternativa",
                "f1": "Custo (R$ mi)",
                "f2": "f2",
                "f3": "f3",
                "heterogeneity": "Heterogeneidade",
            }
        ),
        hide_index=True,
        width="stretch",
    )

with compare_tab:
    st.subheader("Comparação direta")
    default_compare = [item for item in (final_id, "A020", "A045") if item in set(alternatives["alternative_id"])]
    selected_ids = st.multiselect(
        "Escolha de duas a cinco alternativas",
        alternatives["alternative_id"].tolist(),
        default=default_compare,
        max_selections=5,
    )
    if len(selected_ids) >= 2:
        chart = normalized_comparison(alternatives, selected_ids)
        st.pyplot(chart, width="stretch")
        plt.close(chart)
        comparison = alternatives.set_index("alternative_id").loc[selected_ids, list(CRITERIA)]
        comparison["f1"] = comparison["f1"] / 1_000_000
        st.dataframe(
            comparison.rename(columns={"f1": "Custo (R$ mi)", "heterogeneity": "H"}),
            width="stretch",
        )
    else:
        st.info("Selecione pelo menos duas alternativas.")

    detail_id = st.selectbox("Inspecionar composição", alternatives["alternative_id"], index=int(final_id[1:]) - 1)
    detail_row = selected_row(alternatives, detail_id)
    detail_solution = load_solution(detail_id, detail_row["run_ids"])
    with st.expander(f"Composição e qualidade de {detail_id}"):
        detail_figure = plot_solution(detail_solution, get_instance(), f"Alternativa {detail_id}")
        st.pyplot(detail_figure, width="stretch")
        plt.close(detail_figure)

with methods_tab:
    st.subheader("Resultados dos métodos")
    left, right = st.columns(2)
    with left:
        st.markdown("#### PROMETHEE II")
        st.metric("Primeira colocada", promethee_choice)
        st.dataframe(
            promethee.head(15).rename(
                columns={
                    "rank": "Posição",
                    "alternative_id": "Alternativa",
                    "positive_flow": "Fluxo +",
                    "negative_flow": "Fluxo −",
                    "net_flow": "Fluxo líquido",
                }
            ),
            hide_index=True,
            width="stretch",
        )
    with right:
        st.markdown("#### ELECTRE III")
        maximal = electre.loc[electre["maximal"], "alternative_id"].tolist()
        st.metric("Alternativas máximas", len(maximal))
        st.caption(", ".join(maximal))
        st.dataframe(
            electre.head(15).rename(
                columns={
                    "display_rank": "Posição exibida",
                    "alternative_id": "Alternativa",
                    "net_credibility": "Credibilidade líquida",
                    "maximal": "Máxima",
                }
            ),
            hide_index=True,
            width="stretch",
        )
    st.warning(
        f"O ELECTRE registrou {baseline['electre_incomparable_pairs']:,} pares incomparáveis. "
        "A posição exibida não elimina a relação parcial; a recomendação é escolhida dentro "
        "do conjunto máximo pela regra adicional registrada."
    )

with sensitivity_tab:
    st.subheader("Sensibilidade a pesos e limiares")
    prom_counts = Counter(sensitivity["promethee_winner"])
    electre_counts = Counter(sensitivity["electre_choice"])
    winners = sorted(set(prom_counts) | set(electre_counts))
    frequency = pd.DataFrame(
        {
            "PROMETHEE II": [prom_counts[winner] for winner in winners],
            "ELECTRE III": [electre_counts[winner] for winner in winners],
        },
        index=winners,
    )
    st.bar_chart(frequency, x_label="Alternativa", y_label="Cenários vencidos")
    st.dataframe(
        sensitivity.rename(
            columns={
                "weight_profile": "Perfil de pesos",
                "threshold_scale": "Escala dos limiares",
                "promethee_winner": "Vencedora PROMETHEE",
                "electre_choice": "Escolha ELECTRE",
                "electre_maximal_count": "Máximas ELECTRE",
                "electre_incomparable_pairs": "Pares incomparáveis",
                "electre_choice_promethee_rank": "Rank PROM. da escolha ELECTRE",
                "electre_choice_display_rank": "Posição exibida ELECTRE",
            }
        ),
        hide_index=True,
        width="stretch",
    )

with final_tab:
    st.subheader(f"Solução recomendada — {final_id}")
    final_solution = load_solution(final_id, final_row["run_ids"])
    evaluation = evaluate(final_solution, get_instance())
    if evaluation.feasible:
        st.success("Solução factível em todas as restrições originais.")
    else:
        st.error("A solução não é factível na versão atual do avaliador.")
    final_figure = plot_solution(final_solution, get_instance(), f"Solução final {final_id}")
    st.pyplot(final_figure, width="stretch")
    plt.close(final_figure)
    quality_col, composition_col = st.columns([1.15, 1])
    with quality_col:
        st.markdown("#### Qualidade por pilha")
        st.dataframe(
            quality_table(final_solution).style.format(precision=3),
            hide_index=True,
            width="stretch",
        )
    with composition_col:
        st.markdown("#### Caminhões por minério e pilha")
        st.dataframe(composition_table(final_solution), width="stretch")

st.divider()
st.caption(
    "Fonte: resultados oficiais em results/multi_final e results/decision_final. "
    "A aplicação não substitui os arquivos reproduzíveis nem afirma otimalidade global."
)
