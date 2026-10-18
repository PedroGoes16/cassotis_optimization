# Protocolo experimental

Este documento separa requisitos do enunciado de decisões experimentais do grupo. O registro formal das decisões e da evidência é `docs/decision_log.md`.

## Entrega 1 — requisitos já definidos

Para cada objetivo \(f_1\), \(f_2\) e \(f_3\):

- executar o método estocástico 5 vezes;
- apresentar mínimo, desvio-padrão e máximo dos valores finais;
- apresentar as 5 curvas de convergência sobrepostas;
- apresentar uma visualização da melhor solução encontrada.

## Regras de reprodutibilidade adotadas

Resultados finais devem registrar:

```text
run_id
git_commit
instance
objective
seed
algorithm
parameters
stopping_rule
evaluation_budget
runtime_seconds
feasible
f1
f2
f3
total_violation
```

As seeds das execuções finais foram fixadas antes da produção dos resultados reportados.

Calibração de parâmetros deve ser separada do conjunto de execuções finais.

## Decisões da Entrega 1

- critério de parada: 200.000 avaliações, sem critério auxiliar (D010);
- política de inviabilidade: regra de viabilidade (D007);
- parâmetros da GVNS: amostra 250 e P1/P2/P3 = 3/4/5 (D014–D016);
- curva de convergência: registrada a cada melhoria da melhor solução encontrada;
- seeds: calibração e resultados finais com conjuntos disjuntos; seeds oficiais 2016–2020 (D017);
- resultados finais: `results/mono_final/`, incorporados separadamente da implementação.

Ordem cumprida: calibrar → congelar → registrar seeds → executar → commit de resultados.

Execução: `python scripts/run_mono_experiments.py --seeds S1 S2 S3 S4 S5`.

## Convenção para curvas

A curva principal deverá usar no eixo x o número acumulado de avaliações de soluções candidatas sempre que possível. Isso reduz a dependência da máquina usada e facilita comparação entre configurações.

Tempo de execução deve ser mantido como informação complementar.

## Entrega 2

A normalização dos objetivos deverá usar referências obtidas na Entrega 1, conforme exigido no enunciado.

O protocolo D021 está consolidado em `data/protocolo_entrega2.json`: 16 configurações por método, cinco seeds oficiais (2021–2025), 200.000 avaliações e filtragem de dominância em três objetivos antes das projeções. A execução oficial e a análise estão em `results/multi_final/`. A grade é uma decisão do grupo, não uma quantidade exigida pelo enunciado.

## Entrega 3

Os métodos multicritério e a análise de sensibilidade terão protocolo próprio. Nenhum peso de decisão deve ser escolhido silenciosamente ou apresentado como consequência da otimização.
