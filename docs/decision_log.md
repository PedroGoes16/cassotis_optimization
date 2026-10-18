# Decision Log

Este documento registra decisões relevantes do projeto. Não deve ser usado apenas para descrever o que foi implementado; deve registrar **por que** cada escolha foi feita.

Estados possíveis: `CONFIRMADA`, `CONSOLIDADA`, `PENDENTE`, `SUPERADA`.

---

## D001 — Unidade da variável de decisão

**Status:** CONSOLIDADA

**Decisão:** representar \(x_{ip}\) como número de caminhões do minério \(i\) usados na pilha \(p\).

**Alternativa considerada:** representar diretamente massa em kt.

**Motivação:** cada caminhão possui 2 kt e as disponibilidades do enunciado já são dadas em caminhões. A escolha incorpora naturalmente a integralidade e evita uma restrição adicional de múltiplos de 2 kt.

**Impacto:** massa em kt é calculada como \(2x_{ip}\).

---

## D002 — Interpretação de disponibilidade mínima e máxima

**Status:** CONFIRMADA

**Decisão:** os limites são globais sobre as 10 pilhas:

\[
d_i^{min}\le\sum_p x_{ip}\le d_i^{max}.
\]

**Fonte:** esclarecimento explícito da professora. Se um minério tem mínimo 3, pelo menos 3 caminhões desse minério devem ser utilizados no total; eles podem ser concentrados em uma pilha ou distribuídos entre várias.

**Impacto:** disponibilidade não deve ser verificada separadamente por pilha.

---

## D003 — Representação computacional por slots de caminhão

**Status:** CONSOLIDADA

**Decisão:** representar cada pilha por um vetor com \(M_p/2\) posições; cada posição contém um minério e representa um caminhão.

**Alternativa considerada:** armazenar apenas a matriz de contagens \(x_{ip}\).

**Motivação:** o enunciado define N1 e N2 em termos de posições no vetor de composição. A representação por slots torna os movimentos naturais e preserva massa.

**Impacto:** a matriz \(x_{ip}\) continua útil, mas é derivada da solução.

---

## D004 — Tratamento da massa

**Status:** CONSOLIDADA

**Decisão:** preservar massa por construção mantendo fixo o tamanho do vetor de cada pilha.

**Motivação:** não há benefício em explorar estados com massa incorreta quando a representação pode eliminar essa classe de inviabilidade sem reduzir a expressividade da solução.

---

## D005 — Elegibilidade logística

**Status:** CONSOLIDADA

**Decisão:** N1, N2 e futuras vizinhanças devem impedir inserção de minério em grupo para o qual ele não seja elegível sempre que isso puder ser garantido diretamente pelo operador.

**Motivação:** elegibilidade é uma condição discreta simples e pode ser preservada sem introduzir trade-off útil.

---

## D006 — FeT

**Status:** CONSOLIDADA

**Decisão:** manter FeT nos dados, cálculos e visualizações, mas não tratá-lo como restrição ativa na instância de exemplo.

**Motivação:** o enunciado informa limites 0%–100% e declara que FeT não influencia a otimização neste case.

---

## D007 — Política de tratamento de inviabilidade de qualidade e disponibilidade

**Status:** CONSOLIDADA

**Escopo:** violações de SiO2, Al2O3 e disponibilidade global.

**Decisão:** regra de viabilidade (dominação por restrições), implementada em `feasibility.feasibility_rule_key` e usada em toda comparação da GVNS:

1. solução viável vence solução inviável;
2. entre viáveis, vence a de menor objetivo;
3. entre inviáveis, vence a de menor \(V(X)\) normalizado (`normalized_violation`); o objetivo desempata.

**Alternativas consideradas:** rejeição pura; penalização \(f+\lambda V\) estática ou dinâmica; reparo; operadores totalmente preservadores; estratégia em duas fases.

**Motivação:**

- a solução inicial da construtiva é inviável (SiO2 ≈ 7,1% nas pilhas do Sinter 1, limite 6,2%), o que descarta a rejeição pura;
- não há coeficiente \(\lambda\) para calibrar, o que evita três calibrações dependentes da escala (custo ~10^7 R$ contra desvios ~1);
- a regra não depende da escala do objetivo, então pode ser reutilizada nas escalarizações da Entrega 2;
- equivale a uma estratégia em duas fases (primeiro reduzir \(V\), depois otimizar \(f\)) sem precisar de uma troca explícita de fase.

**Consequências:** depois de viável, a solução corrente não volta a ser inviável, e a travessia de regiões inviáveis fica limitada (Aula 04, slide 14). A perturbação pode gerar soluções inviáveis, que a VND usa como ponto de partida. \(V(X)\) permanece a soma linear das violações normalizadas (não a soma de quadrados da Aula 04), porque só é usado para ordenar soluções inviáveis entre si.

**Evidência:** ainda não há evidência experimental da configuração consolidada. Ela será produzida na calibração e nas execuções finais (D017).

Ver `docs/feasibility_strategy.md` e `docs/gvns_decisoes.md`.

---

## D008 — Terceira vizinhança N3

**Status:** CONSOLIDADA

**Decisão:** utilizar uma vizinhança de realocação com substituição em cadeia.

O movimento seleciona duas pilhas distintas \(p_a\) e \(p_b\), contendo respectivamente os minérios \(m_x\) e \(m_y\), e um novo minério \(m_z\). O movimento realiza:

\[
p_a: m_x \rightarrow m_z
\]

\[
p_b: m_y \rightarrow m_x
\]

desde que \(m_z\) seja elegível para \(p_a\) e \(m_x\) seja elegível para \(p_b\).

**Alternativas consideradas:** ciclo entre três pilhas, dupla substituição dentro de uma pilha e movimentos guiados diretamente pela medida de inviabilidade \(V(X)\).

**Motivação:** N3 combina, em uma única transição, duas características que aparecem separadamente em N1 e N2: alteração da composição global de minérios e realocação entre pilhas. O movimento pode modificar diretamente \(f_1\), \(f_2\) e \(f_3\), sendo também adequado para reutilização nas etapas multiobjetivo.

A execução coordenada evita depender da aceitação de estados intermediários que seriam necessários ao decompor o movimento em aplicações sucessivas de outras vizinhanças.

**Impacto:** a massa das pilhas e a elegibilidade são preservadas por construção. O consumo global de \(m_x\) permanece inalterado, enquanto o consumo de \(m_y\) diminui em uma unidade e o de \(m_z\) aumenta em uma unidade. Portanto, o movimento pode gerar violações de disponibilidade e qualidade, que deverão ser tratadas pela política definida em D007.

O movimento pode alterar o custo segundo:

\[
\Delta f_1 = 2000(c_z-c_y).
\]

**Implementação:** `algorithms/vizinhancas.py` (`n3_moves`, `sample_n3_move`, `n3_relocate_replace`). Os movimentos são definidos sobre os minérios distintos de cada pilha (ver D014).

---

## D009 — VNS ou GVNS

**Status:** CONSOLIDADA

**Decisão:** GVNS (Aula 02, slides 36–38): perturbação P_k seguida de VND sobre N1 → N2 → N3, com troca de vizinhança "melhorou → volta para k=1 / ℓ=1; senão → próxima".

**Alternativas consideradas:** VNS básica com uma única vizinhança de refinamento; RVNS.

**Motivação:** o enunciado exige três vizinhanças. Na GVNS as três participam da busca local, e a perturbação tem estruturas próprias (D015). As vizinhanças são complementares: N1 altera o consumo global, N2 só redistribui entre pilhas, N3 faz as duas coisas.

**Implementação:** `algorithms/gvns.py`.

---

## D010 — Critério de parada e orçamento experimental

**Status:** CONSOLIDADA

**Decisão:** o critério de parada é um orçamento fixo de **200.000 avaliações de soluções candidatas por execução**, igual para \(f_1\), \(f_2\) e \(f_3\), sem critério auxiliar. O tempo de execução é registrado como informação complementar.

**Alternativas consideradas:** tempo de parede; número de iterações da GVNS; iterações sem melhoria; orçamentos de 50.000 e 100.000 avaliações.

**Motivação:** o número de avaliações independe da máquina, coincide com o eixo x das curvas de convergência e permite comparação justa entre objetivos e execuções.

**Evidência experimental:** após a calibração dos demais parâmetros, foram comparados orçamentos de 50.000, 100.000 e 200.000 avaliações usando as mesmas seeds de calibração. Todas as execuções chegaram à região factível. Entre 100.000 e 200.000 avaliações ainda houve melhora média nos três objetivos, aproximadamente:

- \(f_1\): 0,43%;
- \(f_2\): 0,85%;
- \(f_3\): 0,29%.

Como ainda havia ganho mensurável após 100.000 avaliações e o custo computacional de 200.000 avaliações permaneceu baixo para a instância estudada, adotou-se 200.000 como orçamento final da Entrega 1.

---

## D011 — Reprodutibilidade

**Status:** CONSOLIDADA

**Decisão:** separar fase de calibração de parâmetros da fase de resultados finais e registrar seeds/configurações das execuções finais.

**Motivação:** evitar seleção oportunista de configurações após observar os resultados e permitir reprodução do relatório.
---

## D012 — Separação entre avaliação e objetivo ativo

**Status:** CONSOLIDADA

**Decisão:** a função `evaluate()` calcula simultaneamente \(f_1\), \(f_2\), \(f_3\), qualidade e violações. A função `objective_value()` apenas seleciona qual objetivo será minimizado em uma execução mono-objetivo.

**Motivação:** evitar duplicação de cálculos e desacoplar a definição do problema da metaheurística.

**Impacto:** o mesmo algoritmo poderá ser reutilizado para otimizar \(f_1\), \(f_2\) ou \(f_3\), e a mesma avaliação poderá ser reaproveitada nas etapas multiobjetivo.

---

## D013 — Heurística construtiva

**Status:** CONSOLIDADA

**Decisão:** a solução inicial é construída em duas fases. Primeiro, são atendidas as disponibilidades mínimas globais dos minérios, distribuindo esses caminhões apenas em pilhas elegíveis. Depois, os slots restantes são preenchidos com os minérios elegíveis de menor custo que ainda possuam disponibilidade máxima restante.

**Alternativas consideradas:** não foram comparadas outras construtivas.

**Motivação:** segue a sugestão do enunciado e garante, já na construção, massa correta, elegibilidade e limites globais de disponibilidade. A escolha não se apoia em comparação empírica com outras construtivas, e não se afirma que ela seja superior a elas.

**Consequências:** a solução inicial pode ser inviável quanto aos limites de SiO₂ e Al₂O₃, e isso é tratado pela regra de D007. A construtiva é determinística, então todas as execuções partem da mesma solução.

**Observação:** na instância de exemplo, a solução construída tem custo R$ 59,34 mi, f2 = 14,90 e f3 = 7,00. Ela é inviável em SiO2 nas pilhas do Sinter 1 (≈ 7,1%) e levemente em Al2O3 em P1, P2 e P4.

---

## D014 — Busca local: primeira melhoria e VND N1 → N2 → N3

**Status:** CONSOLIDADA

**Decisão:**

- busca local de primeira melhoria, repetida até que uma passada não encontre movimento de melhoria, com ordem definida pela seed;
- VND na ordem N1 → N2 → N3;
- N1 explorada completamente;
- N2 e N3 exploradas por amostragem uniforme, sem reposição, sobre movimentos distintos;
- `sample_size = 250` movimentos por passada para N2 e N3.

Para N1, uma passada sem melhoria caracteriza ótimo local em N1. Para N2 e N3, uma passada sem melhoria significa apenas que nenhum movimento da amostra analisada melhorou a solução.

**Alternativas consideradas:** melhor melhoria; exploração completa de N2/N3; amostragem baseada em slots; `sample_size` de 250, 500 e 1000.

**Motivação:** N3 possui uma vizinhança muito grande, tornando a exploração completa incompatível com o orçamento de avaliações. A amostragem sem reposição evita reavaliar movimentos equivalentes e não privilegia minérios apenas por aparecerem em mais posições de uma pilha.

**Evidência experimental:** foram comparados `sample_size = 250`, `500` e `1000`. A primeira calibração exploratória foi seguida por uma calibração confirmatória, mantendo a perturbação fixa em P1/P2/P3 = 3/4/5 e utilizando cinco novas seeds de calibração.

O valor `250` apresentou o melhor comportamento global entre os três objetivos: permaneceu competitivo em \(f_1\), obteve os melhores resultados médios na confirmação para \(f_2\) e \(f_3\), e permitiu mais ciclos completos da GVNS dentro do mesmo orçamento de avaliações. Por isso `sample_size = 250` foi consolidado.

---

## D015 — Perturbação (SHAKE) com estruturas próprias P1, P2 e P3

**Status:** CONSOLIDADA

**Decisão:** a GVNS utiliza dois níveis separados:

- N1, N2 e N3 são estruturas de vizinhança da VND, responsáveis pela intensificação;
- P1, P2 e P3 são estruturas próprias do SHAKE, responsáveis pela diversificação.

As perturbações consolidadas são:

- **P1 — perturbação pequena:** substituição de `p1_positions = 3` posições por minérios elegíveis;
- **P2 — cadeia de ejeção:** cadeia envolvendo `p2_chain_length = 4` pilhas distintas, preservando elegibilidade em cada elo;
- **P3 — perturbação forte:** permutação cíclica de uma posição em `p3_piles = 5` pilhas do mesmo grupo de sinter.

Logo, as intensidades adotadas são:

\[
P1/P2/P3 = 3/4/5.
\]

P1 e P2 podem alterar o consumo global de minérios e, consequentemente, gerar violações de disponibilidade. P3 preserva o consumo global, pois apenas redistribui minérios entre as cinco pilhas do mesmo grupo. Eventuais inviabilidades são tratadas pela regra definida em D007.

**Alternativas consideradas:** o SHAKE original baseado em aplicações aleatórias de N1/N2/N3; configurações P1/P2/P3 = 1/2/5, 2/3/5 e 3/4/5; reconstrução parcial de pilhas.

**Motivação:** separar as vizinhanças usadas para refinamento das estruturas de perturbação torna explícita a diferença entre intensificação e diversificação. A intensidade crescente 3 → 4 → 5 também permite aumentar progressivamente a distância em relação à solução corrente quando níveis menores não produzem melhora.

**Evidência experimental:** a calibração comparou as configurações 1/2/5, 2/3/5 e 3/4/5 em conjunto com diferentes tamanhos de amostra. A configuração 3/4/5 apresentou comportamento competitivo e equilibrado nos três objetivos e foi mantida na calibração confirmatória. Com essa configuração fixa, `sample_size = 250` também se mostrou adequado. Assim, os valores 3/4/5 foram consolidados para as execuções finais.

---

## D016 — Critério de aceitação

**Status:** CONSOLIDADA

**Decisão:** X'' substitui X somente se for estritamente melhor pela regra de D007, com tolerância relativa de 10^-12 para ignorar ruído de ponto flutuante.

**Alternativas consideradas:** aceitar soluções iguais (movimento lateral); aceitação probabilística do tipo recozimento simulado.

**Motivação:** é a aceitação do pseudocódigo da GVNS visto em aula e não introduz parâmetros. A diversificação vem do SHAKE.

---

## D017 — Sementes e separação entre calibração e resultados finais

**Status:** CONSOLIDADA

**Decisão:**

- calibração e resultados finais utilizam conjuntos de seeds distintos;
- o algoritmo e todos os parâmetros foram congelados antes da definição das seeds finais;
- as cinco seeds oficiais da Entrega 1 são:

\[
2016,\ 2017,\ 2018,\ 2019,\ 2020.
\]

- cada uma será utilizada para \(f_1\), \(f_2\) e \(f_3\), totalizando 15 execuções finais;
- os resultados finais serão gerados com a mesma configuração da GVNS:
  - `max_evaluations = 200000`;
  - `sample_size = 250`;
  - `p1_positions = 3`;
  - `p2_chain_length = 4`;
  - `p3_piles = 5`;
- o desvio-padrão reportado será o amostral (\(n-1\));
- os resultados finais serão armazenados separadamente dos resultados de calibração.

**Motivação:** separar desenvolvimento, calibração e execução final reduz seleção oportunista de configurações e permite reprodução exata dos experimentos.

**Seeds anteriores não utilizadas como seeds finais:** seeds empregadas em testes automatizados, smoke tests e calibrações, incluindo 1–5, 1001–1003, 3001, 3101–3103 e 3201–3205.

---

## D018 — Normalização dos objetivos para a Entrega 2

**Status:** CONSOLIDADA

**Decisão:** utilizar normalização min–max com referências fixas
obtidas das melhores soluções factíveis mono-objetivo da Entrega 1:

\[
\hat f_j(X)=
\frac{f_j(X)-z_j^*}{z_j^{ref}-z_j^*}.
\]

O vetor \(z^*\) contém o menor valor observado de cada objetivo
nas três soluções-âncora. O vetor \(z^{ref}\) contém o maior valor
observado de cada objetivo entre essas soluções.

**Fonte dos dados:** `results/mono_final/summary.csv`,
execuções `f1_seed2018`, `f2_seed2018` e `f3_seed2018`,
versão de código `087e7e3`.

**Alternativas consideradas:** divisão direta pelo ideal,
normalização dinâmica durante a busca e escalonamento por limites
físicos do problema.

**Motivação:** reduzir a diferença de escala entre o custo em reais
e os desvios quadráticos químicos, utilizando referências da Entrega 1
conforme exigência do enunciado. As referências permanecem fixas,
permitindo comparações consistentes entre as abordagens escalares.

**Consequências:**
- Não aplicar clipping em [0,1].
- Admitir valores normalizados negativos ou superiores a 1.
- Usar a precisão original dos resultados experimentais.
- Não interpretar z* como ótimo global comprovado.
- Não interpretar z_ref como nadir verdadeiro.
- Validar que todo intervalo z_ref[j] - z*[j] seja positivo.

**Implementação:** `data/referencias_multiobjetivo.json`,
`multiobjective/multiobjective.py` e
`multiobjective/normalizacao.py`.

**Validação:** testes em `tests/test_normalizacao.py` executados com sucesso na suíte do projeto; referências e resultados oficiais da Entrega 2 estão registrados em `results/multi_final/`.

---

## D019 — Escalarização por Soma Ponderada

**Status:** CONFIRMADA

**Decisão:** implementar a abordagem de Soma Ponderada como
combinação linear dos três objetivos normalizados:

\[
F_w(X)=w_1\hat f_1(X)+w_2\hat f_2(X)+w_3\hat f_3(X).
\]

Os pesos satisfazem:

\[
w_j\geq 0,\qquad \sum_{j=1}^{3}w_j=1.
\]

A normalização segue as referências fixas definidas em D018.

**Alternativas consideradas:** combinar os objetivos sem
normalização; utilizar pesos que não somam 1; adaptar os pesos
dinamicamente durante a busca.

**Motivação:** a Soma Ponderada transforma os três objetivos
conflitantes em um único critério escalar, permitindo reutilizar
a GVNS desenvolvida na Entrega 1. A normalização evita que
a diferença de unidades e magnitudes faça o custo dominar
artificialmente os objetivos químicos.

A restrição de soma unitária facilita a interpretação dos pesos
e a comparação entre configurações.

**Consequências:**

- Cada vetor de pesos define um problema escalar diferente.
- Pesos maiores representam maior prioridade relativa ao objetivo.
- Pesos nulos são permitidos para explorar soluções extremas.
- A abordagem pode não recuperar regiões não convexas da
  fronteira de Pareto em espaços de objetivos discretos.
- Soluções obtidas com pesos nulos podem ser apenas fracamente
  eficientes; a filtragem de dominância será feita posteriormente.
- As restrições originais do problema permanecem inalteradas.
- A política de inviabilidade D007 será reutilizada quando
  houver integração com a GVNS.
- Os pesos serão fixos durante cada execução, não adaptativos.

**Implementação:** `multiobjective/multiobjective.py`
e `multiobjective/soma_ponderada.py`.

**Validação:** `tests/test_soma_ponderada.py`.

**Integração à GVNS:** a configuração `objective="weighted_sum"`
seleciona a soma ponderada dos objetivos normalizados como
critério de comparação entre soluções factíveis.

A factibilidade e a medida de violação originais permanecem
inalteradas. A escolha dos pesos é fixa durante cada execução.

**Implementação:** `GVNSConfig` e `CountingEvaluator` em
`algorithms/gvns.py`.

**Validação da integração:** `tests/test_multiobjective_gvns.py`.

**Grade experimental de pesos:** registrada e consolidada em D021 após o piloto.

---

## D020 — Escalarização pelo método epsilon-restrito

**Status:** CONFIRMADA

**Decisão:** implementar o método epsilon-restrito adotando o
custo normalizado como objetivo principal e transformando os
dois objetivos químicos normalizados em restrições adicionais:

\[
\min_X \hat f_1(X)
\]

sujeito às restrições originais e:

\[
\hat f_2(X)\leq\varepsilon_2,
\qquad
\hat f_3(X)\leq\varepsilon_3.
\]

A normalização utiliza as referências fixas definidas na D018.

**Alternativas consideradas:** utilizar f2 ou f3 como objetivo
principal; alternar o objetivo principal entre configurações;
incorporar epsilon por penalização diretamente na função objetivo.

**Motivação:** minimizar custo respeitando níveis máximos
aceitáveis de desvio químico possui interpretação operacional
direta para o problema de composição de pilhas.

A formulação geral permite escolher qualquer objetivo principal,
mas a configuração inicial do projeto adota f1.

**Tratamento de inviabilidade:** estender a política D007 com
violações adicionais:

\[
v_{\varepsilon_j}(X)=
\max(0,\hat f_j(X)-\varepsilon_j).
\]

Para a comparação de soluções inviáveis, utilizar:

\[
V_\varepsilon(X)=
V_{\mathrm{original}}(X)
+v_{\varepsilon_2}(X)
+v_{\varepsilon_3}(X).
\]

A factibilidade do problema escalar exige simultaneamente
a factibilidade original e o atendimento aos limites epsilon.

**Consequências:**

- evaluation.feasible permanece associado ao problema original.
- A factibilidade epsilon é verificada separadamente.
- Os limites epsilon são expressos na escala normalizada.
- Valores epsilon não são obrigatoriamente limitados a [0,1].
- Configurações muito restritivas podem não produzir solução factível.
- O tratamento de inviabilidade preserva o princípio D007.
- A soma das violações normalizadas é uma escolha heurística,
  não uma garantia de encontrar uma solução factível.
- Os valores experimentais de epsilon foram definidos e consolidados em D021.

**Implementação:** `multiobjective/multiobjective.py`
e `multiobjective/epsilon_restrito.py`.

**Validação:** `tests/test_epsilon_restrito.py`.


**Integração à GVNS:** a configuração
`objective="epsilon_restricted"` seleciona o custo normalizado
como objetivo principal e acrescenta as duas restrições epsilon
ao critério de factibilidade.

`Evaluation.feasible` continua indicando apenas a factibilidade
original. A propriedade `Candidate.feasible` representa a
factibilidade efetiva utilizada na busca.

A violação agregada utilizada entre soluções inviáveis é:

\[
V_\varepsilon(X)=V(X)+v_{\varepsilon_2}(X)+v_{\varepsilon_3}(X).
\]

A agregação por soma é uma escolha heurística. As parcelas epsilon
são medidas na escala normalizada dos objetivos, enquanto V(X)
segue a normalização das restrições originais definida em D007.

**Consequência:** configurações epsilon excessivamente restritivas
podem não alcançar soluções factíveis dentro do orçamento disponível.

**Implementação:** `GVNSConfig`, `Candidate` e `CountingEvaluator`
em `algorithms/gvns.py`.

**Validação da integração:** `tests/test_multiobjective_gvns.py`.

---

## D021 — Planejamento experimental multiobjetivo

**Status:** CONSOLIDADA

**Decisão:** comparar as abordagens Soma Ponderada e
epsilon-restrito com 16 configurações escalares cada, utilizando
cinco sementes por configuração na etapa oficial.

### Soma Ponderada

Gerar os pesos pela malha:

\[
w_j=k_j/4,\quad
k_j\in\{0,1,2,3,4\},\quad
\sum_j k_j=4.
\]

Acrescentar o vetor central (1/3, 1/3, 1/3), totalizando
16 configurações.

**Justificativa:** representar soluções extremas, compromissos
entre dois objetivos e compromissos simultâneos entre três
objetivos. O ponto central representa prioridades iguais.

### Epsilon-restrito

Manter f1 como objetivo principal e utilizar:

\[
\varepsilon_2,\varepsilon_3
\in\{0.25,0.50,0.75,1.00\}.
\]

O produto cartesiano gera 16 configurações.

**Justificativa:** explorar níveis progressivamente mais
restritivos dos dois desvios químicos, na escala normalizada
definida em D018.

A viabilidade das configurações deverá ser investigada.
A ausência de solução factível em uma execução não constitui
prova de inexistência de solução factível.

### Execução exploratória

- Seeds: 4001 e 4002.
- Orçamento: 50.000 avaliações por execução.
- Mesmo conjunto de configurações proposto para a fase final.
- Resultados armazenados separadamente dos resultados oficiais.

Objetivos da exploração: validar a execução dos métodos,
verificar obtenção de factibilidade e identificar eventuais
problemas de cobertura do espaço de objetivos.

A grade poderá ser revista nesta fase, desde que as alterações
sejam justificadas e registradas antes das execuções oficiais.

### Execução oficial

- Seeds: 2021, 2022, 2023, 2024 e 2025.
- Orçamento: 200.000 avaliações por execução.
- sample_size = 250.
- SHAKE P1/P2/P3 = 3/4/5.
- 16 configurações por abordagem.
- 80 execuções e 16 milhões de avaliações por abordagem.

As mesmas seeds serão utilizadas em todas as configurações.
Os parâmetros serão congelados após a fase exploratória.

O orçamento em avaliações será igual entre as abordagens,
embora o tempo de execução possa variar.

### Análise de resultados

Reunir as melhores soluções finais de cada configuração e
semente, preservando a identificação da execução que as gerou.

Considerar apenas soluções factíveis para o respectivo problema
escalar. Identificar a não dominância usando os três objetivos
originais (f1, f2, f3), todos minimizados.

A filtragem de dominância será feita em três dimensões, antes
de construir as projeções bidimensionais:

- f1 x f2;
- f1 x f3;
- f2 x f3.

Os conjuntos não dominados serão produzidos separadamente
para Soma Ponderada e epsilon-restrito.

Soluções duplicadas poderão ser unificadas na visualização,
sem perder o registro das seeds e configurações de origem.

### Alternativas consideradas

- Apenas 15 configurações de pesos;
- grades de pesos e epsilon com tamanhos diferentes;
- grades mais refinadas;
- orçamentos diferentes entre abordagens;
- utilização das seeds oficiais da Entrega 1.

**Motivação:** produzir uma comparação controlada,
reproduzível e com esforço experimental equivalente,
sem selecionar configurações após observar os resultados finais.

**Protocolo:** `data/protocolo_entrega2.json`.

**Geração das grades:** `multiobjective/planejamento.py`.

**Validação:** `tests/test_planejamento_multiobjetivo.py`.

**Critério de consolidação:** concluir o piloto, documentar
eventuais alterações, congelar o protocolo e somente então
executar as cinco replicações oficiais.


### Consolidação após execução exploratória

Foram comparados três orçamentos de avaliações:
50.000, 100.000 e 200.000, mantendo constantes as
16 configurações de cada abordagem, as seeds 4001 e 4002
e os parâmetros da GVNS.

Todas as 64 execuções foram factíveis nos três orçamentos.

Entre 100.000 e 200.000 avaliações, 27 das 32 execuções
de cada abordagem melhoraram seu objetivo escalar.
Nenhuma apresentou piora.

No epsilon-restrito, as inversões de monotonicidade do
custo entre configurações aninhadas diminuíram de
7 (50k) para 4 (100k) e 2 (200k).

Essas inversões são atribuídas à natureza heurística da
busca e não representam violação da formulação matemática.

**Decisão consolidada:** manter 200.000 avaliações por
execução, 16 configurações por abordagem, cinco seeds
finais (2021 a 2025), sample_size=250 e SHAKE 3/4/5.

As referências de normalização da D018 permanecem fixas.
A grade experimental e o algoritmo ficam congelados antes
de produzir os resultados oficiais.

**Evidências:** results/multi_pilot,
results/multi_smoke100k e results/multi_smoke200k.

**Resultado oficial:** `results/multi_final/` registra 160 execuções, 80 por método e cinco por configuração, todas reportadas factíveis. A execução usou o código `d5e0d94`; as frentes individuais contêm 45 e 49 vetores distintos. Esses resultados não implicam otimalidade global.


---

## D022 — Executor multiobjetivo, reprodutibilidade e filtro de Pareto

**Status:** CONFIRMADA (execução histórica conferida; validação contínua por testes)

**Decisão:** executar cada configuração de pesos e limites ε com todas as seeds definidas na D021, armazenando um JSON por execução, um CSV agregado, a análise de factibilidade e os vetores não dominados por abordagem.

**Implementação:** `scripts/run_multi_experiments.py`; `multiobjective/pareto.py`.

**Justificativa:** cada execução deve ser rastreável e retomável. O mesmo orçamento de avaliações por configuração permite comparação controlada entre Soma Ponderada e ε-restrito. A busca não fornece certificado de ótimo global, portanto as frentes são aproximadas.

**Regras de análise:**

- Identificar factibilidade original separadamente da factibilidade do problema escalar; no ε-restrito só a segunda permite incluir o resultado na frente.
- Identificar dominância no espaço completo `(f1, f2, f3)` original, com três critérios minimizados; somente então gerar as projeções em pares.
- A frente não dominada é computada separadamente para cada método. As melhores soluções finais de cada configuração e seed constituem o conjunto candidato; não se afirma que as frentes são globalmente Pareto-ótimas.
- Colapsar na visualização vetores objetivo numericamente coincidentes, preservando todos os identificadores de origem.
- Manter pilotos, smoke e execuções oficiais em pastas separadas.
- Persistir resultados a cada execução e impedir a reutilização de um mesmo arquivo quando a assinatura da configuração divergir.

**Condição para execução final:** somente depois de analisar o piloto e registrar/congelar D021. O executor rejeita `--phase final` enquanto `data/protocolo_entrega2.json` estiver com status diferente de `CONGELADO`.

**Alternativas consideradas:** gerar apenas figuras sem histórico por execução; filtrar separadamente cada projeção 2D; misturar seeds de calibração e oficiais; rodar a fase final antes de avaliar a factibilidade da grade.

**Consequências:** a execução completa gera muitos arquivos, mas permite auditoria/reprodução. As projeções 2D podem conter pontos que seriam dominados naquele par isoladamente, pois o filtro correto foi calculado em 3D.

**Validação:** `tests/test_pareto_multiobjetivo.py`, `tests/test_planejamento_multiobjetivo.py`, `tests/test_multiobjective_gvns.py`, execução exploratória da D021 e `scripts/validate_multi_results.py`. Este último recalcula as 160 composições e confere os escalares, a factibilidade, as estatísticas e as três frentes salvas, sem substituir os resultados originais.

**Atualização de reprodutibilidade:** os arquivos históricos assinavam o caminho absoluto da instância e não podem ser retomados automaticamente em outro diretório. Para novas execuções, a assinatura versão 2 utiliza o conteúdo normalizado dos três CSVs da instância, do executor e do núcleo Python, além da configuração, referências e protocolo. Alternativas consideradas: manter o caminho absoluto; aceitar registros legados sem identificar seu conteúdo; ou migrar os registros históricos. A assinatura por conteúdo permite retomar em outro diretório e detecta alterações relevantes, sem confiar silenciosamente em registros antigos. Como consequência, os resultados legados são preservados e devem ser consultados como históricos; novas rodadas usam uma pasta de saída distinta. A assinatura não fixa a versão do Python nem das dependências. A rodada oficial não foi refeita por essa alteração.

