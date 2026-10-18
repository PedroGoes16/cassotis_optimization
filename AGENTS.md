# AGENTS.md

Este arquivo orienta revisores humanos e agentes/LLMs que trabalhem neste repositório.

## Prioridade das fontes

Ao analisar ou modificar o projeto, use esta ordem de precedência:

1. enunciado oficial do case;
2. esclarecimentos explícitos da professora;
3. `docs/decision_log.md`;
4. `docs/problem_formulation.md`;
5. implementação e testes.

Se código e documentação divergirem, não escolha silenciosamente um deles. Identifique a divergência.

## Regras para decisões

Não transformar uma questão pendente em decisão definitiva sem registrar a mudança.

Toda decisão relevante de modelagem, metaheurística, tratamento de inviabilidade, parametrização, normalização, método multicritério ou protocolo experimental deve ser registrada em `docs/decision_log.md`.

Cada registro deve indicar:

- status;
- decisão;
- alternativas consideradas;
- motivação;
- consequências;
- evidência experimental, quando existir.

## Separação entre requisito e escolha do grupo

Sempre distinguir:

- o que é exigido pelo enunciado;
- o que foi confirmado pela professora;
- o que é decisão do grupo;
- o que ainda está pendente.

Não justificar escolhas do grupo como se fossem exigências do enunciado.

## Reprodutibilidade

Resultados experimentais finais devem registrar, no mínimo:

- versão do código;
- instância usada;
- objetivo/configuração;
- seed;
- orçamento/critério de parada;
- parâmetros da metaheurística;
- valor final dos objetivos;
- viabilidade;
- tempo de execução, quando medido.

## Arquitetura

A implementação de custo, qualidade, restrições e avaliação deve existir em um único núcleo reutilizável.

Não duplicar fórmulas em notebooks, Streamlit, algoritmos mono-objetivo e algoritmos multiobjetivo.

## Estado de decisões relevantes

Consolidadas:

- variável de decisão: número de caminhões por minério e pilha;
- capacidade de caminhão: 2 kt;
- disponibilidade mínima/máxima: global nas 10 pilhas;
- massa das pilhas: preservada pela representação;
- elegibilidade: deve ser preservada pelos operadores sempre que aplicável;
- FeT: calculado/armazenado, mas restrição não ativa na instância de exemplo.

Consolidadas na Entrega 1 (ver D007–D017):

- N3: realocação com substituição em cadeia;
- construtiva: a sugerida no enunciado (não comparada com outras);
- inviabilidade: regra de viabilidade;
- GVNS com VND N1 → N2 → N3, primeira melhoria; N1 completa, N2/N3 amostradas sem reposição sobre movimentos distintos;
- SHAKE com estruturas próprias P1 (pequena), P2 (cadeia), P3 (permutação em 5 pilhas do grupo);
- aceitação: melhoria estrita;
- parada: número de avaliações;
- separação entre seeds de calibração e seeds finais;
- orçamento 200.000, amostra 250, SHAKE 3/4/5 e seeds finais 2016–2020.

Na Entrega 2 (ver D018–D022):

- normalização por referências mono-objetivo fixas; Soma Ponderada e ε-restrito;
- D021 consolidada: 16 configurações por abordagem, seeds 2021–2025 e 200.000 avaliações por execução;
- as 160 execuções oficiais estão em `results/multi_final/`; preservar os resultados legados.

Pendente:

- revisão e entrega do relatório cumulativo e dos códigos da Entrega 2;
- métodos multicritério e atributo adicional da Entrega 3.

Antes de recomendar qualquer uma dessas escolhas, consultar `docs/feasibility_strategy.md` e `docs/decision_log.md`.


## Componentes implementados

- `evaluator.py`: calcula todos os objetivos, qualidades e violações;
- `objectives.py`: seleciona f1, f2 ou f3 sem recalcular a solução;
- `algorithms/constructive.py`: contém a heurística construtiva baseline atual;
- `algorithms/vizinhancas.py`: N1, N2 e N3 (enumeração completa, amostragem e aplicação de movimentos);
- `algorithms/perturbacoes.py`: estruturas P1, P2 e P3 do SHAKE;
- `algorithms/gvns.py`: GVNS com VND e contagem de avaliações;
- `feasibility.py`: violação normalizada e regra de viabilidade;
- `visualization.py`: figuras de convergência e de solução.
- `multiobjective/`: normalização, escalarizações, grades e filtro de Pareto;
- `scripts/run_multi_experiments.py`: execução e análise experimental multiobjetivo.

A heurística construtiva foi consolidada por seguir a sugestão do enunciado (D013); não deve ser apresentada como empiricamente superior a outras construtivas.
