---

## D027 — Análise de sensibilidade do PROMETHEE I/II

**Status:** CONFIRMADA — protocolo e resultados de sensibilidade; **recomenda-se consolidar o cenário-base da D026**, condicionando esta consolidação à aprovação do grupo para os limiares já propostos.

**Escopo:** manter fixos os 91 desempenhos originais da matriz da D023, a função em V com indiferença, e as regras PROMETHEE I/II implementadas na D026. Não reexecutar GVNS, não restringir o PROMETHEE às alternativas do núcleo ELECTRE e não alterar os resultados de ELECTRE. Cada cenário deve ser calculado sobre as mesmas 91 alternativas.

### Experimento A: limiares de preferência

**Decisão de teste:** fixar os pesos oficiais AHP D024 e variar uniformemente os limiares relativos às amplitudes observadas nos quatro critérios, preservando q < p. Os sete cenários têm pares (q%, p%) de (0,20), (1,25) [base], (2,30), (5,25), (0,30), (2,20) e (5,30). Todos são *percentuais da amplitude da amostra*, não porcentagens de custo ou de teores físicos.

**Resultado com a matriz oficial de 91 alternativas:** A020 ocupou a 1ª posição em todos os sete cenários, e A016 ocupou a 2ª. O fluxo líquido de A020 variou de aproximadamente 0,511754 a 0,539273. O número de pares incomparáveis do PROMETHEE I variou de 154 a 257, contra 198 no cenário-base. A002 foi 3ª, 4ª ou 5ª, conforme os limiares. No cenário q=5%, p=25%, A020 foi a única alternativa não superada pelo PROMETHEE I; nos demais ensaios, A020 e A016 não foram superadas.

**Interpretação:** A020 mostrou estabilidade de liderança **dentro desses sete cenários discretos de limiares**, o que apoia manter q=1%, p=25% como configuração acadêmica de referência. Não constitui demonstração de estabilidade em todos os valores admissíveis de q/p nem validação operacional dos limiares.

### Experimento B: pesos com limiares fixos

**Decisão de teste:** manter q=1% e p=25% e variar *somente* o peso do custo de 50% a 80% (50%, 55%, 60%, 65%, 70%, 75%, 80%). Redistribuir o peso restante entre f2, f3 e c4 **proporcionalmente à razão entre seus pesos AHP originais**. Esta regra mantém a soma 1 e o sentido de minimização. Os pesos variantes são cenários hipotéticos, **não são extraídos de novas comparações AHP** e não substituem o vetor confirmado na D024.

**Resultado com a matriz oficial:** A020 ficou em 1º com custo entre 50% e 70%. Quando custo foi aumentado para 75% e 80%, a 1ª posição passou para A002; A020 ficou em 3º e 6º, respectivamente. **A sensibilidade ao peso do custo é real**: a liderança de A020 não é universal.

### Conclusão, decisão e limitações

A análise recomenda a consolidação **do cenário-base D026, q=1% e p=25%** nos quatro critérios, porque não se identificou ganho metodológico ou evidência operacional para substituí-los após variações de limiar. A020 é a principal recomendação **para os julgamentos AHP D024 e os parâmetros D026**, com A016 como alternativa de referência (1º e 2º PROMETHEE II; ambas não superadas no PROMETHEE I). A seleção é compatível com o núcleo de nove alternativas do ELECTRE I D025, mas os métodos não são independentes em seus pesos.

**Não afirmar robustez absoluta.** O resultado resiste aos limiares examinados, mas se altera quando a prioridade de custo atinge 75% na família de cenários de pesos adotada. A liderança também depende das 91 alternativas consideradas; o PROMETHEE não é uma avaliação absoluta da mistura. As preferências modeladas são do grupo acadêmico, não dados validados por decisores da Cassotis.

**Persistência/reprodutibilidade:** `data/protocolo_sensibilidade_promethee.json`, `scripts/analyze_promethee_sensitivity.py`, `tests/test_promethee_sensitivity.py`. Executar o script no checkout oficial gera `results/mcda/sensibilidade_promethee_limiares.csv`, `results/mcda/sensibilidade_promethee_pesos.csv`, `results/mcda/sensibilidade_promethee_resumo.json`, contendo hashes dos arquivos de entrada. Os arquivos `diagnostico_independente_*.csv` entregues no pacote preservam uma conferência independente da mesma matriz oficial; o executor é a fonte reprodutível de resultados no repositório.

**Para consolidar a D026 após aceite do grupo:** em `data/parametros_promethee.json`, definir `status` como `CENARIO_BASE_CONFIRMADO`; indicar em `scenario` que q=1%, p=25% foram assumidos pelo grupo após a sensibilidade D027, sem atribuí-los à Cassotis. Reexecutar `python scripts/run_promethee.py` e `python scripts/analyze_promethee_sensitivity.py` para atualizar os resumos e hashes. Não alterar os limiares nem o vetor AHP.
