# D025 — Incremento ELECTRE I (exploratório)

**Escopo deste pacote:** implementar e documentar somente o ELECTRE I.
O AHP D024 não é recalculado nem alterado. PROMETHEE e a análise de
sensibilidade completa ficam para etapas posteriores.

## Arquivos a copiar para a raiz de `cassotis_optimization`

```text
src/cassotis_optimization/mcda/electre.py
data/parametros_electre.json
scripts/run_electre.py
tests/test_electre.py
docs/D025_adicionar_ao_decision_log.md
```

Inclua o texto do último arquivo ao **final** de `docs/decision_log.md`;
não substitua as decisões anteriores.

## Execução

```bash
python -m pip install -e ".[dev]"
python -m pytest tests/test_electre.py -q
python scripts/run_electre.py
python -m pytest -q
```

Saídas (são escritas apenas após executar o script):

- `results/mcda/electre_i_resumo.json`: pesos, limiares, amplitudes,
  vetos equivalentes nas unidades originais, fontes de entrada via SHA256,
  quantidade de sobreclassificações, alternativas não sobreclassificadas,
  eventual núcleo e advertência em caso de ciclos.
- `results/mcda/electre_i_relacoes.csv`: **4.095 pares não ordenados**
  para 91 alternativas, com concordâncias em ambos os sentidos,
  critérios responsáveis por veto e classificação dos pares.

O ELECTRE I **não** produz ranking único. Se o conjunto selecionado tiver
várias alternativas, isso é um resultado legítimo. A futura comparação
com PROMETHEE usará os mesmos pesos e os mesmos critérios.

## Justificativas matemáticas

Todos os critérios são minimizados. Concordância de `a` sobre `b` é a soma
dos pesos dos critérios em que `a` é pelo menos tão boa quanto `b`.
O veto impede sobreclassificação se uma diferença **desfavorável** em
qualquer critério superar 40% da amplitude observada daquele critério.
A normalização é usada **somente para medir a intensidade relativa do veto**,
não para somar os desempenhos brutos.

Com pesos AHP da D024, \(w_{custo}=0,6474\), \(w_{c4}=0,1962\) e
\(w_{f2}=w_{f3}=0,0782\). O limiar inicial de concordância 0,80 impede
aprovação por custo isoladamente, mas ainda prioriza custo no grafo.
Os limiares são **propostas não aprovadas**: revisar, justificar e registrar
antes de consolidar D025.

## Verificação prévia

Na análise preliminar da matriz `matriz_decisao.csv` publicada no GitHub,
o cenário `lambda=0.80`, `veto=0.40` para os quatro critérios gerou
902 relações dirigidas, 3.193 pares incomparáveis e um núcleo acíclico
com 9 alternativas. Os testes unitários do pacote usam entradas
sintéticas e verificam veto, relação, empates e ciclos. O teste
`test_matrix_from_repository_if_present` valida **também os números reais**
quando executado no checkout oficial com a matriz de 91 linhas.

Não se devem apresentar os parâmetros 0,80 e 0,40 como preferências
confirmadas pelo grupo ou exigências da professora.
