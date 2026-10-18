# Entrega 2 — executor experimental

Esta rotina executa a grade registrada em `data/protocolo_entrega2.json`, preservando os modos mono-objetivo da Entrega 1.

## Como executar (raiz do repositório)

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/validate_multi_results.py
python scripts/run_multi_experiments.py --phase pilot --dry-run
python scripts/run_multi_experiments.py --phase pilot --max-runs 2 --budget 3000 --out results/multi_novo_smoke
```

Os resultados históricos do piloto estão em `results/multi_pilot/`. Para novas rodadas, o script retoma execuções pelo `config_hash` versão 2 e rejeita diferenças de configuração, conteúdo da instância ou código. A assinatura normaliza CRLF/LF e não depende do caminho absoluto, mas não registra versões do Python nem das bibliotecas. O processo pode ser interrompido e retomado na mesma pasta com os mesmos conteúdos.

**Estado histórico:** o piloto foi analisado, a D021 foi consolidada e o protocolo congelado antes da execução oficial. Os 160 resultados gerados com o código `d5e0d94` estão em `results/multi_final/` e devem ser preservados. Para reproduzir uma nova rodada com a versão atual, use uma pasta nova:

```bash
python scripts/run_multi_experiments.py --phase final --out results/multi_repro
```

O executor **não permite** reduzir o orçamento ou executar somente parte da grade na fase oficial. O mesmo protocolo fixa seeds 2021–2025 e 200.000 avaliações, totalizando 160 execuções GVNS, desde que ambas as abordagens estejam selecionadas.

**Compatibilidade:** os registros oficiais antigos usam uma assinatura diferente, que incluía o caminho absoluto da instância. Eles não são migrados nem retomados pelo executor atual, mesmo que os dados sejam iguais. A mensagem de assinatura divergente protege os arquivos existentes; não os apague ou sobrescreva para fazer a reprodução. Uma nova rodada pode diferir em versão de código registrada e em tempos de execução. Para reproduzir o ambiente histórico com máxima fidelidade, utilize o commit original e registre também as versões de Python e bibliotecas.

O validador é somente leitura: recalcula objetivos e factibilidade a partir de cada composição, verifica a normalização, os escalares e o atendimento a ε, confronta as estatísticas por configuração e refaz os filtros de Pareto. A conferência não é uma nova rodada da GVNS nem prova de ótimo global.

## Artefatos

- `runs/<run_id>.json`: valores originais/normalizados, objetivo escalar, as duas condições de factibilidade, violação, parâmetro, composição, histórico e informações de reprodutibilidade.
- `summary.csv`: um registro por GVNS.
- `pareto_weighted_sum.csv`, `pareto_epsilon_restricted.csv`: vetores não dominados em **três** objetivos originais, com a procedência das seeds/configurações.
- `pareto_<metodo>_f1_f2.png`, `..._f1_f3.png`, `..._f2_f3.png`: seis projeções bidimensionais dos pontos filtrados em 3D.
- `analysis.json`: cobertura de factibilidade por configuração, número de soluções e pontos não dominados.
- `manifest.json`: protocolo, localização da instância e versão do código; novas rodadas também incluem hashes dos arquivos da instância e do código.

Para o ε-restrito, `scalar_feasible` inclui a factibilidade original **e** os limites ε; `original_feasible` verifica somente as restrições físicas e químicas. Não considerar soluções apenas originalmente factíveis como resultados da abordagem ε.

A frente de Pareto é estimada a partir da coleção **das melhores soluções finais** de cada configuração e seed. Não há garantia de Pareto-otimalidade global. Pontos repetidos no gráfico são unificados, preservando seus `run_ids` completos em CSV.

## Regras de execução

- Rodadas exploratórias e finais não se misturam; usar pastas diferentes para smoke e piloto completo.
- As execuções têm avaliação por orçamento, não tempo como condição de parada.
- As duas abordagens usam o mesmo número de configurações e seeds, mas podem apresentar tempos diferentes.
- Recalcular dominância sempre com os três objetivos **originais** e aplicar as projeções depois, não o contrário.
- Mudanças em pesos, epsilons, seeds ou orçamento após iniciar o piloto exigem registrar uma nova versão do protocolo; a assinatura dos resultados auxilia a detectar inconsistência.
