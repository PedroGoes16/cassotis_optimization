# D024 — AHP para pesos (incremento isolado)

**Conteúdo:**

- `data/preferencias_ahp.json`: fonte dos 6 julgamentos pareados, com a preferência, intensidade e justificativa explícitas.
- `src/cassotis_optimization/mcda/ahp.py`: cálculo dos pesos por média de colunas normalizadas e CR por autovalor principal.
- `scripts/calculate_ahp_weights.py`: gerador que confere os intervalos contra `results/mcda/matriz_decisao.csv`.
- `tests/test_ahp.py`: testes automatizados.
- `docs/D024_adicionar_ao_decision_log.md`: **acrescentar ao final** de `docs/decision_log.md` (não substitui o arquivo).
- `results/mcda/pesos_ahp.json`: resultado calculado a partir dos seis julgamentos (o script confere os intervalos da matriz oficial quando executado no checkout).

## Instalação / execução

Extrair os arquivos sobre a raiz de `peddrinn/cassotis_optimization`. Os caminhos respeitam a organização já existente. O projeto já tem NumPy como dependência. Instalar antes as dependências de desenvolvimento (`python -m pip install -e ".[dev]"`), se ainda não estiverem instaladas.

```bash
python -m pytest tests/test_ahp.py -q
python scripts/calculate_ahp_weights.py
python -m pytest -q
ruff check src/cassotis_optimization/mcda/ahp.py scripts/calculate_ahp_weights.py tests/test_ahp.py
```

O comando de cálculo grava o JSON em `results/mcda/pesos_ahp.json`.

**Importante:** esta etapa NÃO define rankings nem aplica ELECTRE/PROMETHEE. Os seis julgamentos foram assumidos pelo grupo para um cenário acadêmico, não apresentados como preferências oficiais da empresa. Para corrigir uma comparação, editar `data/preferencias_ahp.json` e recalcular; se CR exceder 0,10, rever os julgamentos antes de usar os pesos.
