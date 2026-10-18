# Cassotis Optimization — Teoria da Decisão UFMG 2026/2

Projeto da disciplina **Teoria da Decisão** para o case **Otimização do Custo e Qualidade de Pilhas de Minério**.

O objetivo é desenvolver, documentar e avaliar uma solução baseada em VNS/GVNS para as etapas mono-objetivo e multiobjetivo e, posteriormente, aplicar métodos de apoio multicritério à decisão.

## Estado atual

Entrega 1: formulação, GVNS, calibração e 15 execuções finais implementadas e registradas em `results/mono_final/`. O relatório em `report/main.tex` é cumulativo e inclui também a Entrega 2.

Entrega 2: normalização, Soma Ponderada, ε-restrito, filtro de Pareto e executor implementados. A rodada oficial em `results/multi_final/` reúne 160 execuções: 16 configurações por método, cinco seeds por configuração, 200.000 avaliações por execução. O protocolo foi congelado antes da rodada (D021). As frentes são aproximações e não certificados de ótimo global.

Consolidados:

- variável de decisão em número de caminhões (2 kt cada);
- disponibilidade mínima e máxima global por minério, considerando as 10 pilhas;
- representação por posições de caminhão, que preserva massa;
- elegibilidade preservada pelos operadores de vizinhança;
- FeT mantido no domínio, mas não ativo como restrição na instância de exemplo;
- N3: realocação com substituição em cadeia (D008);
- heurística construtiva sugerida no enunciado (D013);
- tratamento de inviabilidade: regra de viabilidade (D007);
- GVNS com VND N1 → N2 → N3, primeira melhoria (D009, D014);
- SHAKE com estruturas próprias P1, P2, P3 (D015);
- aceitação por melhoria estrita (D016);
- parada por número de avaliações (D010);
- separação entre seeds de calibração e seeds finais (D017).

Configuração final: orçamento de 200 mil avaliações, amostra 250, SHAKE 3/4/5; seeds 2016–2020 na Entrega 1 e 2021–2025 na Entrega 2.

As decisões da GVNS estão explicadas em linguagem direta em [`docs/gvns_decisoes.md`](docs/gvns_decisoes.md). O registro formal está em [`docs/decision_log.md`](docs/decision_log.md).

Pendentes: revisão e submissão da Entrega 2; métodos de decisão multicritério, atributo adicional, Streamlit e relatório final da Entrega 3. Não há apresentação oral na Entrega 2.

## Fonte do problema

A especificação principal é o enunciado do case da disciplina. Os dados em `data/example_instance/` correspondem ao **exemplo apresentado no anexo do enunciado** e não devem ser confundidos com uma eventual instância definitiva fornecida posteriormente.

Há também uma clarificação da professora sobre disponibilidade: os limites mínimo e máximo de cada minério são globais sobre todas as pilhas. Se um minério tiver disponibilidade mínima 3, devem ser utilizados pelo menos 3 caminhões desse minério no total, distribuídos livremente entre as 10 pilhas, respeitando as demais restrições.

## Estrutura

```text
.
├── data/example_instance/        # instância do anexo do enunciado (CSV)
├── docs/
│   ├── decision_log.md           # registro formal das decisões
│   ├── gvns_decisoes.md          # explicação das decisões da GVNS
│   ├── problem_formulation.md
│   ├── feasibility_strategy.md
│   ├── experiment_protocol.md
│   ├── deliverables_checklist.md
│   └── source_notes.md
├── src/cassotis_optimization/
│   ├── domain.py, io.py, validation.py, solution.py
│   ├── evaluator.py              # núcleo único: custo, qualidade, violações
│   ├── objectives.py             # seleção de f1/f2/f3
│   ├── feasibility.py            # violação normalizada e regra de viabilidade
│   ├── visualization.py          # figuras (convergência, solução)
│   └── algorithms/
│       ├── constructive.py       # heurística construtiva
│       ├── vizinhancas.py        # N1, N2, N3 (enumeração e amostragem uniforme)
│       ├── perturbacoes.py       # P1, P2, P3 (SHAKE)
│       └── gvns.py               # GVNS + VND
│   └── multiobjective/           # normalização, escalarizações, grades e Pareto
├── scripts/
│   ├── validate_instance.py
│   ├── run_mono_experiments.py   # 5 execuções × f1/f2/f3, tabelas e figuras
│   ├── run_multi_experiments.py  # protocolo multiobjetivo e figuras
│   └── validate_multi_results.py # auditoria dos resultados multiobjetivo
├── tests/
├── app/                          # Streamlit (Entrega 3)
├── notebooks/
└── results/                      # saídas geradas pelos scripts
```

## Preparação do ambiente

Requer Python 3.11 ou superior.

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,app]"
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,app]"
```

## Validação inicial

```bash
python scripts/validate_instance.py
pytest
```

## Experimentos da Entrega 1

```bash
python scripts/run_mono_experiments.py --seeds S1 S2 S3 S4 S5
```

As seeds são obrigatórias. As seeds finais da Entrega 1, registradas em D017 antes da rodada oficial, foram 2016–2020. Para um teste rápido:

```bash
python scripts/run_mono_experiments.py --seeds 1 2 --budget 5000 --out results/teste
```

O script gera, na pasta de saída (padrão `results/mono/`):

- o JSON de cada execução;
- `summary.csv` e `summary.md` (mín/std/máx);
- as curvas de convergência;
- a figura da melhor solução de cada objetivo.

Parâmetros: `--seeds`, `--budget`, `--objectives`, `--out`.

## Experimentos da Entrega 2

Consulte [`docs/entrega2_experimentos.md`](docs/entrega2_experimentos.md) para instalação, testes, protocolo, artefatos e comandos. Para reproduzir sem modificar os resultados históricos, indique uma pasta nova, por exemplo `--phase final --out results/multi_repro`. A assinatura dos resultados antigos era baseada no caminho absoluto; o executor atual não os migra nem os sobrescreve automaticamente.

## Relatório cumulativo

O código-fonte é `report/main.tex` e o PDF compilado é `report/main.pdf`. Para compilar novamente, instale uma distribuição TeX com os pacotes usados pelo documento e execute, dentro de `report/`, `tectonic main.tex` ou `pdflatex main.tex` duas vezes. As figuras mono-objetivo estão em `report/figures/`; as multiobjetivo são lidas de `results/multi_final/`, portanto mantenha essa estrutura de pastas.

## Regra de desenvolvimento

Nenhuma decisão de modelagem ou algoritmo deve ser alterada silenciosamente. Mudanças relevantes devem ser registradas em `docs/decision_log.md` com motivação, alternativas consideradas e impacto esperado.

A lógica central deve permanecer em `src/`. Notebooks e Streamlit devem consumir essa implementação, e não recriar fórmulas ou regras paralelas.
