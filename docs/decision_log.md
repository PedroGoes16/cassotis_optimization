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

**Status:** CONFIRMADA

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

**Validação:** testes em `tests/test_normalizacao.py`.
Promover a CONSOLIDADA após execução bem-sucedida dos testes.

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

**Grade experimental de pesos:** será registrada em D021.
A grade proposta ainda precisa ser validada.

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
- Os valores experimentais de epsilon serão definidos em D021.

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

**Decisão proposta:** comparar as abordagens Soma Ponderada e
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

### Execução oficial proposta

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


---

## D022 — Executor multiobjetivo, reprodutibilidade e filtro de Pareto

**Status:** CONFIRMADA (pendente validação integral da execução no repositório)

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

**Validação:** `tests/test_pareto_multiobjetivo.py`, `tests/test_planejamento_multiobjetivo.py`, `tests/test_multiobjective_gvns.py` e execução exploratória da D021.

---

## D023 — Conjunto de alternativas e quarto critério de decisão

**Status:** CONFIRMADA (pendente conferência dos 91 registros oficiais antes de consolidar)

**Decisão:** utilizar, como conjunto inicial de alternativas da Entrega 3, as 91 soluções não dominadas em três objetivos armazenadas em `results/multi_final/pareto_joint.csv`, com as composições extraídas dos arquivos `results/multi_final/runs/<run_id>.json`. Não reexecutar a GVNS e não filtrar a frente separadamente em duas dimensões.

**Critérios de decisão, todos de minimização:**

1. \(C_1=f_1\), custo total em reais;
2. \(C_2=f_2\), soma dos desvios quadráticos dos teores de SiO₂ em relação aos alvos;
3. \(C_3=f_3\), soma dos desvios quadráticos dos teores de Al₂O₃ em relação aos alvos;
4. \(C_4\), heterogeneidade das receitas de minério **entre pilhas de um mesmo equipamento**.

**Definição do quarto critério:** seja \(x_{ip}\) a quantidade de caminhões do minério \(i\) na pilha \(p\), \(n_p=\sum_i x_{ip}\) a quantidade total de caminhões da pilha e \(g(p)\) seu equipamento. A proporção do minério \(i\) na receita da pilha é

\[
r_{ip}=\frac{x_{ip}}{n_p}.
\]

A receita agregada de referência de cada equipamento \(g\) é ponderada pela quantidade de caminhões das suas pilhas:

\[
R_{ig}=\frac{\sum_{p\in P_g}x_{ip}}{\sum_{p\in P_g}n_p}.
\]

Definir o atributo operacional como a média das distâncias de variação total entre cada receita e a receita de seu equipamento:

\[
\boxed{C_4(X)=\frac{1}{|P|}\sum_{p\in P}\frac12\sum_{i\in I}\left|r_{ip}-R_{i,g(p)}\right|.}
\]

Assim, \(0\le C_4\le 1\), e \(C_4=0\) significa que as pilhas de cada equipamento seguem a mesma receita **em proporções**, embora possam ter massas absolutas diferentes. Valores maiores significam maior heterogeneidade.

**Fundamentação:** a homogeneização de receitas é explicitamente sugerida no enunciado da professora para simplificar manuseio e planejamento das pilhas de um mesmo equipamento. O atributo depende da alocação detalhada de minérios, não de custo nem de indicadores químicos, e é distinto de contar apenas quantos tipos de minérios aparecem em cada pilha. Sua relação de conflito com os outros objetivos será verificada empiricamente na matriz oficial.

**Alternativas consideradas:** número de tipos distintos por pilha (proxy de complexidade, mas insuficiente para identificar diferenças de proporção entre receitas); diferença quadrática entre receitas; distância total entre todas as duplas de pilhas. Preferiu-se a distância de variação total até a receita média de cada grupo por ser adimensional, limitada, direta e interpretável.

**Rastreabilidade e tratamento de empates:** cada linha da matriz conserva `source_run_ids`, identifica uma execução representativa e associa um hash à composição. Vetores de objetivos idênticos **não devem** ser fundidos se corresponderem a composições distintas; nesse caso, o script interrompe a geração e exige decisão explícita. Nos quatro empates de origem identificados na Entrega 2, as composições foram anteriormente conferidas como idênticas.

**Consequências:** as 91 alternativas eram não dominadas no espaço \((f_1,f_2,f_3)\); acrescentar um critério não deve excluir alternativas sem uma justificativa MCDA explícita. A escala do quarto atributo não define seu peso de preferência, que será estabelecido em D024. Não se interpreta \(C_4\) como custo real de manuseio, e sua menor magnitude numérica não deve implicar menor importância.

**Implementação:** `scripts/build_mcda_matrix.py`.

**Saídas:** `results/mcda/matriz_decisao.csv` e `results/mcda/diagnostico_d023.json`.

**Validação:** `tests/test_build_mcda_matrix.py`, comparação dos valores de objetivos e factibilidade dos JSON com o CSV, verificação das massas/pilhas e verificação dos conflitos par-a-par. A medição completa e a consolidação dependem da execução no checkout oficial com as 91 alternativas.

---

## D024 — Elicitação de preferências e pesos dos critérios via AHP

**Status:** CONFIRMADA — cenário-base de preferências fornecido pelo grupo; aplicação em ELECTRE/PROMETHEE e análise de sensibilidade pendentes.

**Objeto da decisão:** obter pesos para os quatro critérios da D023 usando AHP como técnica **auxiliar de elicitação de preferências**. Os dois métodos principais de decisão e comparação de alternativas serão selecionados/implementados separadamente. AHP nesta etapa **não ordena as 91 alternativas**. Todas as alternativas da matriz da D023 permanecem elegíveis.

**Origem dos julgamentos:** matriz de comparações par a par fornecida pelo grupo e inicialmente calculada no SpiceLogic AHP Calculator (`https://spicelogic.com/ahp-calculator`). São **preferências assumidas para o cenário acadêmico**, não preferências verificadas da Cassotis ou da professora. A importância foi interpretada considerando os intervalos observados nas 91 alternativas, e não apenas os nomes isolados dos critérios.

**Critérios e melhorias de referência (pior para melhor valor observado na matriz D023):**

| Critério | Significado | Amplitude de referência |
|---|---|---|
| \(C_1=f_1\) | custo total | R$ 65,82 mi → R$ 59,68 mi; redução R$ 6,14 mi |
| \(C_2=f_2\) | soma de desvios quadráticos de SiO₂ | 6,939554 → 2,372752; redução 4,566802 |
| \(C_3=f_3\) | soma de desvios quadráticos de Al₂O₃ | 6,634568 → 1,421458; redução 5,213110 |
| \(C_4\) | heterogeneidade de receitas entre pilhas | 0,480128 → 0,282871; redução 0,197257 |

Essas diferenças são amplitudes descritivas da amostra, não ganhos que possam ser necessariamente obtidos simultaneamente. SiO₂ e Al₂O₃ são **desvios quadráticos de teores**, não valores diretos de pureza.

### Os seis julgamentos independentes (escala de Saaty)

| Par | Preferência do grupo | Intensidade | Entrada \(a_{ij}\) | Fundamentação do cenário-base |
|---|---|---:|---:|---|
| Custo × SiO₂ | Custo | 7 (muito forte) | 7 | A redução de R$ 6,14 mi é julgada muito mais valiosa do que a melhoria integral observada em \(f_2\). |
| Custo × Al₂O₃ | Custo | 7 (muito forte) | 7 | A mesma prioridade pelo custo é atribuída frente à melhoria integral observada em \(f_3\). |
| Custo × Heterogeneidade | Custo | 5 (forte) | 5 | A redução de custo é julgada mais valiosa que a padronização de receitas, embora esta permaneça relevante. |
| SiO₂ × Al₂O₃ | Igual importância | 1 | 1 | Não há prioridade adicional assumida entre os desvios quadráticos dos dois óxidos. |
| SiO₂ × Heterogeneidade | Heterogeneidade | 3 (moderada) | 1/3 | O grupo atribui importância moderadamente superior à homogeneização das receitas. |
| Al₂O₃ × Heterogeneidade | Heterogeneidade | 3 (moderada) | 1/3 | Mesma justificativa operacional para o par anterior. |

Essas justificativas descrevem **o significado dos julgamentos fornecidos**, sem alegar comprovação econômica externa. O cenário dá peso alto ao custo e considera a padronização de receitas relevante; todas as alternativas da D023 já atendem às restrições químicas originais. Mesmo assim, menor desvio químico continua sendo desejável e sua baixa prioridade relativa exigirá análise de sensibilidade.

**Matriz de comparações** (linhas e colunas na ordem \(f_1,f_2,f_3,C_4\)):

\[
A=\begin{pmatrix}
1&7&7&5\\
1/7&1&1&1/3\\
1/7&1&1&1/3\\
1/5&3&3&1
\end{pmatrix}.
\]

Para todo par distinto, \(a_{ji}=1/a_{ij}\). O registro declarativo em `data/preferencias_ahp.json` guarda os seis julgamentos, critério favorecido, intensidade e justificativa; não armazena apenas os pesos finais.

**Extração dos pesos:** normalizar cada coluna da matriz e tomar a média aritmética das linhas (método de *aproximação por colunas normalizadas*, correspondente aos pesos apresentados pelo SpiceLogic). Se \(s_j=\sum_i a_{ij}\), então:

\[
\widetilde{a}_{ij}=a_{ij}/s_j,
\qquad
w_i=\frac{1}{4}\sum_{j=1}^4\widetilde{a}_{ij}.
\]

Pesos completos obtidos pelo script (ordem \(f_1,f_2,f_3,C_4\)):

\[
w=(0{,}6474358974;\ 0{,}0782051282;\ 0{,}0782051282;\ 0{,}1961538462).
\]

Os pesos apresentados arredondados são **64,74% custo; 7,82% SiO₂; 7,82% Al₂O₃; 19,62% heterogeneidade**. Na implementação, manter a precisão total para evitar soma diferente de 1 pelo arredondamento.

**Teste de consistência:** usar o maior autovalor da matriz recíproca original \(\lambda_{\max}\), não a média dos autovalores ponderada pelos pesos aproximados. Para \(n=4\), adotar \(RI=0{,}90\):

\[
CI=\frac{\lambda_{\max}-4}{3},\qquad CR=\frac{CI}{0{,}90}.
\]

Para os julgamentos registrados: \(\lambda_{\max}\approx4{,}073467\); \(CI\approx0{,}024489\); **\(CR\approx0{,}027210<0{,}10\)**. A matriz atende ao limite convencional de consistência, mas isso não certifica que os pesos sejam objetivamente corretos nem substitui sua justificação operacional.

**Procedimentos alternativos considerados:** Swing Weighting (mais explícito quanto ao valor dos ganhos nas escalas reais) e autovetor principal como forma alternativa de extrair pesos AHP. Preferiu-se AHP pela facilidade de registrar comparações e testar a consistência; adotou-se a média das colunas normalizadas para reproduzir exatamente o método usado pelo grupo no SpiceLogic. O autovetor principal é utilizado **somente** para a verificação de consistência.

**Reprodutibilidade:** `data/preferencias_ahp.json`, `src/cassotis_optimization/mcda/ahp.py` e `scripts/calculate_ahp_weights.py`. Saída calculada: `results/mcda/pesos_ahp.json`. Testes: `tests/test_ahp.py` (incluem reconstrução da matriz, reciprocidade, pesos, CR e rejeição de registros incompletos/duplicados). O script verifica também as amplitudes da matriz oficial da D023 antes de exportar os pesos.

**Consequências:** reutilizar esse mesmo vetor-base em ELECTRE e PROMETHEE, cujos limiares e funções de preferência serão decididos posteriormente. Realizar análise de sensibilidade aumentando a importância relativa dos desvios químicos e modificando parâmetros de decisão. Não modificar a matriz original de 91 alternativas nem reexecutar a GVNS para esta etapa.

---

## D025 — ELECTRE I: sobreclassificação, vetos e núcleo de escolha

**Status: PROPOSTA EXPLORATÓRIA — limiares pendentes de aprovação pelo grupo.**

**Base das alternativas:** `results/mcda/matriz_decisao.csv` (91 alternativas, D023),
sem reexecutar a GVNS. Os quatro critérios são minimizados: custo \(f_1\),
desvios quadráticos de SiO₂ \(f_2\), de Al₂O₃ \(f_3\) e heterogeneidade
operacional \(C_4\).

**Pesos fixos de referência (D024):**

\[
w=(0{,}6474358974;\;0{,}0782051282;\;0{,}0782051282;\;0{,}1961538462).
\]

Esses pesos decorrem dos seis julgamentos AHP fornecidos pelo grupo e
reproduzidos por `src/cassotis_optimization/mcda/ahp.py`. Não são
preferências verificadas de uma empresa.

### Variante e significado

Adota-se **ELECTRE I**, para formular um *problema de escolha* (recomendar um
subconjunto, não gerar uma ordenação total). Para as alternativas \(a,b\),
definir concordância ponderada

\[
C(a,b)=\sum_{j\colon f_j(a)\le f_j(b)}w_j.
\]

Um critério apoia a afirmação “\(a\) é pelo menos tão boa quanto \(b\)” quando
seu valor em \(a\) é **menor ou igual** ao de \(b\). Essa comparação é realizada
nos valores originais (não somamos as unidades distintas).

Como teste de discordância, para cada critério calcular a amplitude observada
na matriz D023, \(\Delta_j=\max f_j-\min f_j\). Um veto em \(j\) ocorre quando

\[
f_j(a)-f_j(b)>v_j\Delta_j.
\]

A relação de sobreclassificação é estabelecida quando

\[
aSb\;\Longleftrightarrow\; C(a,b)\ge\lambda
\;\land\; \forall j:\, f_j(a)-f_j(b)\le v_j\Delta_j.
\]

### Limiares **propostos**, não aprovados

- **Concordância:** \(\lambda=0{,}80\).
- **Veto relativo:** \(v_j=0{,}40\) para cada um dos quatro critérios;
  esse número é uma fração da amplitude **observada**, e não uma porcentagem
  física do critério.
- **Indiferença no nível de critério:** adota-se igualdade numérica exata,
  sem limiares \(q\) e \(p\), por se tratar da variante ELECTRE I, e não III/IS.

Limiar de concordância 0,80 foi proposto para impedir que o **custo isolado**
(0,6474 de peso AHP) baste para sobreclassificar qualquer alternativa. Nesse
cenário, custo + homogeneidade somam 0,8436; custo + ambos os desvios químicos
somam 0,8038; custo + apenas um desvio soma 0,7256. Portanto,
o apoio ao custo precisa ser acompanhado por critérios adicionais.

Os vetos de 40% da amplitude observada têm a intenção de bloquear
compensações grandes em um único critério. **Essa fração é uma hipótese de
preferência do grupo e precisa ser discutida**, porque os julgamentos AHP não
determinam veto nem concordância. Não foi inferida de preferências declaradas
pela professora ou pela Cassotis.

**Consequência estrutural importante:** como o peso do custo é maior que 0,5,
nenhuma alternativa de custo mais elevado pode sobreclassificar uma alternativa
mais barata para qualquer limiar maior que 0,5 neste modelo. Mesmo que a
alternativa mais cara seja melhor nos outros três critérios, o máximo de
concordância sem apoio do custo seria 0,3526. Trata-se de uma consequência
das preferências registradas na D024, relevante para a sensibilidade posterior.

### Incomparabilidade e núcleo

Para cada par não ordenado, preservar os dois sentidos \(aSb\) e \(bSa\).
Se nenhum sentido ocorrer, registrar **incomparabilidade**; se ocorrerem
ambos, registrar **sobreclassificação mútua**, sem chamar isso de indiferença
estrita. A relação pode não ser transitiva e pode conter ciclos.

O **núcleo de escolha** requer (i) nenhuma sobreclassificação entre
seus integrantes (independência interna) e (ii) que cada alternativa externa
seja sobreclassificada por pelo menos um integrante (cobertura externa).
A implementação extrai esse núcleo pela seleção recursiva de fontes do grafo
**quando o grafo é acíclico**. Na presença de ciclos residuais, sinaliza a
impossibilidade de usar essa extração simples, em vez de apresentar um falso
núcleo. O núcleo não é um ranking nem afirma ótimo global.

### Diagnóstico preliminar com as 91 alternativas oficiais

Com os parâmetros **ainda exploratórios** descritos acima, o diagnóstico
independente sobre a matriz D023 encontrou:

- 4.095 pares distintos de alternativas;
- 902 pares com sobreclassificação em exatamente um sentido;
- 3.193 pares incomparáveis;
- 6 alternativas sem nenhuma sobreclassificação recebida;
- grafo sem ciclos e **9 alternativas no núcleo de escolha**:
  `A001`, `A002`, `A014`, `A016`, `A020`, `A034`, `A060`, `A062`, `A066`.

Esses números descrevem a resposta do método às preferências **supostas**:
não devem ser usados para ajustar silenciosamente os limiares após observar
quem é selecionado. Os dados de origem continuam intactos.

### Alternativas e validações posteriores

Foram consideradas as variantes ELECTRE III/IS (com limiares de indiferença e
preferência mais numerosos) e métodos de ordenação ELECTRE II. Preferiu-se
inicialmente ELECTRE I por corresponder diretamente à questão de **seleção**
e representar explicitamente discordância e incomparabilidade com poucos
parâmetros auditáveis. A comparação com PROMETHEE será documentada depois,
sem alterar a matriz D023 nem os pesos AHP oficiais.

A consolidação dependerá da aprovação dos limiares pelo grupo e de análise
de sensibilidade. No mínimo, comparar a concordância \(\lambda\) em torno de
0,75/0,80/0,85 e veto relativo em 0,25/0,40/0,50, mostrando como isso altera
o conjunto de escolha. A alteração do limiar de concordância pode ter efeito
*discreto* por causa dos poucos valores possíveis de soma dos pesos.

**Implementação proposta:** `src/cassotis_optimization/mcda/electre.py`,
`scripts/run_electre.py`, `data/parametros_electre.json` e
`tests/test_electre.py`. Saídas geradas no checkout oficial:
`results/mcda/electre_i_resumo.json` e
`results/mcda/electre_i_relacoes.csv`.

**Fontes conceituais:** Bernard Roy, ELECTRE I (método de escolha e núcleo);
revisão *Fifty years of multiple criteria decision analysis*,
European Journal of Operational Research (2025), DOI
`10.1016/j.ejor.2024.07.038`. Os valores específicos de \(\lambda\) e \(v_j\)
são **decisões propostas pelo grupo**, não extraídos dessas fontes.