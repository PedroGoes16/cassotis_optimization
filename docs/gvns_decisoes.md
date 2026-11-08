# GVNS da Entrega 1 — o que foi decidido e por quê

Este texto explica, em linguagem direta, as escolhas feitas na implementação da
metaheurística:

- `src/cassotis_optimization/algorithms/gvns.py`: GVNS e VND;
- `algorithms/vizinhancas.py`: N1, N2 e N3;
- `algorithms/perturbacoes.py`: P1, P2 e P3.

O registro formal de cada decisão, com status, alternativas e consequências,
está em `docs/decision_log.md` (D007, D009, D010, D013–D017).

Para cada ponto, é indicado o que **o enunciado exige** e o que **é escolha do
grupo**. Os valores numéricos apresentados abaixo são os parâmetros
**consolidados após a calibração** e usados nas execuções finais.

---

## 1. VNS ou GVNS? → GVNS

**Enunciado:** permite VNS ou GVNS.

**Escolha do grupo:** GVNS, seguindo o pseudocódigo da Aula 02 (slides 36–38).

**Por quê:**

- O enunciado exige três vizinhanças (N1, N2, N3). Na GVNS, a busca local é
  uma VND que usa as três de forma sistemática, então todas participam da
  intensificação.
- As três fazem coisas diferentes:
  - N1 muda a composição global;
  - N2 redistribui entre pilhas sem mudar o consumo global;
  - N3 faz as duas coisas ao mesmo tempo.
  
  Um ótimo local em uma delas frequentemente não é ótimo local nas outras, e a
  VND explora exatamente isso.
- A GVNS tem dois níveis separados: as vizinhanças N_ℓ intensificam (VND) e as
  perturbações P_k diversificam (SHAKE). Aqui cada nível tem estruturas
  próprias (seções 5 e 6).

## 2. Pseudocódigo

```text
GVNS(instância, objetivo f, semente, orçamento):
    X ← CONSTRUTIVA()                      # pode ser inviável em qualidade
    X ← VND(X)
    enquanto houver orçamento de avaliações:
        k ← 1
        enquanto k ≤ 3:
            X'  ← SHAKE(X, P_k)            # P1 pequena, P2 cadeia, P3 permutação
            X'' ← VND(X')
            se X'' é melhor que X:         # regra de viabilidade (seção 3)
                X ← X'';  k ← 1
            senão:
                k ← k + 1
    retornar melhor solução avaliada

VND(X):
    ℓ ← 1
    enquanto ℓ ≤ 3:                        # N1 → N2 → N3
        X' ← BUSCA_LOCAL(X, N_ℓ)
        se X' é melhor que X:  X ← X';  ℓ ← 1
        senão:                 ℓ ← ℓ + 1
    retornar X

BUSCA_LOCAL(X, N):                         # primeira melhoria
    repetir
        C ← N1: todos os movimentos, em ordem aleatória
            N2, N3: até 250 movimentos distintos, sorteados sem reposição
        para cada movimento m em C:
            Y ← aplicar m em X;  avaliar Y   # conta 1 avaliação
            se Y é melhor que X:  X ← Y;  recomeçar
    até uma passada inteira não melhorar
    retornar X
```

O orçamento é verificado a cada avaliação; quando ele acaba, a execução para
imediatamente e devolve a melhor solução já avaliada.

## 3. Tratamento de soluções inviáveis → regra de viabilidade

**Enunciado:** cada grupo deve escolher e justificar (rejeição, penalização,
reparo ou operadores que preservem a viabilidade). O enunciado também avisa
que a solução inicial pode ser inviável.

**O que já é garantido pela representação:** massa das pilhas, integralidade
(múltiplos de 2 kt) e elegibilidade. Sobram como possíveis violações: limites
de SiO₂ e Al₂O₃ em cada pilha e disponibilidade mínima/máxima global.

**Escolha do grupo:** regra de viabilidade (Aula 02, slides 46–50):

1. solução viável sempre vence solução inviável;
2. entre duas viáveis, vence a de menor objetivo;
3. entre duas inviáveis, vence a de menor violação normalizada V(X)
   (`feasibility.py`); o objetivo só desempata.

**Por quê:**

- **Funciona partindo de solução inviável.** A construtiva gera as pilhas do
  Sinter 1 com SiO₂ ≈ 7,1% (limite 6,2%). Com a regra, a busca primeiro reduz
  V(X) e, ao chegar em V = 0, passa a otimizar o objetivo.
- **Não tem parâmetro de penalidade.** Uma penalização F = f + λV exigiria
  calibrar λ para cada objetivo, porque o custo está na casa de 10⁷ R$ e os
  desvios quadráticos na casa de 1. A Aula 04 (slide 33) mostra que um λ mal
  escolhido bloqueia a busca ou a deixa presa na região inviável.
- **É reaproveitável na Entrega 2.** Ela não depende da escala do objetivo,
  então continua valendo com soma ponderada normalizada ou restrições ε.
- **Rejeição pura não serve** porque a solução inicial já é inviável.
- **Reparo** exigiria um procedimento específico de correção de qualidade, com
  risco de dominar o comportamento da busca.

**Limitação conhecida:** depois de viável, a busca não atravessa mais regiões
inviáveis (Aula 04, slide 14). O SHAKE compensa em parte: P1 e P2 podem gerar
uma solução inviável, e a VND a partir dela pode reencontrar outra região
viável. Isso deve ser discutido no relatório.

## 4. Critério de aceitação → só melhoria estrita

**Enunciado:** não especifica.

**Escolha do grupo:** X'' substitui X somente se for estritamente melhor pela
regra acima, como no pseudocódigo da Aula 02. Uma tolerância relativa de 10⁻¹²
evita "melhorias" causadas só por arredondamento.

**Por quê:** é a aceitação padrão da VNS/GVNS vista em aula, é simples de
explicar e não tem parâmetros. A diversificação fica a cargo do SHAKE.

## 5. Busca local → primeira melhoria; N1 completa, N2 e N3 amostradas

**Enunciado:** exige a busca local, mas não diz como.

**Escolha do grupo:**

- **Primeira melhoria**, com a ordem dos movimentos definida pela semente, o
  que mantém a execução reprodutível.
- **VND na ordem N1 → N2 → N3**, da vizinhança menor para a maior.
- **N1 é explorada por completo** (cerca de 1.100 movimentos distintos na
  instância). Quando a busca em N1 termina, a solução é um ótimo local de N1.
- **N2 (cerca de 3.000 movimentos) e N3 (cerca de 100.000) são amostradas.**
  A cada passada, sorteiam-se até 250 movimentos distintos, com probabilidade
  igual para cada movimento distinto e sem repetição dentro da passada.
  Quando nenhum deles melhora, a busca naquela vizinhança termina. Isso
  **não garante** que a solução seja ótimo local de N2 ou N3: só quer dizer
  que a amostra não encontrou melhoria.

**Por quê:**

- Melhor melhoria gastaria a vizinhança inteira a cada passo; com N3 na casa
  de 10⁵ movimentos, poucos passos consumiriam o orçamento.
- **Amostragem uniforme sobre movimentos distintos.** Posições que contêm o
  mesmo minério numa pilha geram a mesma solução quando trocadas, então os
  movimentos são definidos sobre os minérios distintos de cada pilha. O
  conjunto de soluções alcançáveis é o mesmo do enunciado, só sem vizinhos
  repetidos. A primeira versão sorteava por posição e tinha dois problemas:
  - um minério que ocupa várias posições de uma pilha tinha mais chance de ser
    escolhido;
  - o mesmo movimento podia ser avaliado várias vezes na mesma passada.
  
  A versão atual corrige os dois:
  - N2 é enumerada e sorteada sem reposição;
  - em N3, os movimentos são agrupados por (pilha a, pilha b, m_x, m_y); cada
    grupo é sorteado com peso igual ao número de m_z possíveis e depois m_z é
    sorteado. Assim, cada movimento distinto tem a mesma probabilidade, sem
    precisar enumerar os 10⁵ movimentos.
- O valor **250** foi consolidado após a comparação experimental com amostras
  de 500 e 1000 movimentos (D014).

## 6. Perturbação (SHAKE) → estruturas próprias P1, P2, P3

**Enunciado:** exige perturbação, mas não diz qual.

**Escolha do grupo:** separar claramente os dois níveis da GVNS.
N1/N2/N3 são usadas só na VND. O SHAKE tem estruturas próprias, de intensidade
crescente:

| k | Estrutura | O que faz | Tamanho |
|---|---|---|---|
| 1 | **P1 — pequena** | troca o minério de 3 posições sorteadas por outro minério elegível | até 3 caminhões |
| 2 | **P2 — cadeia** | alteração encadeada em 4 pilhas: a 1ª recebe um minério novo, cada pilha seguinte recebe o que saiu da anterior, e o minério da 4ª sai da solução | até 4 caminhões em 4 pilhas |
| 3 | **P3 — forte** | permutação cíclica de uma posição de cada uma de 5 pilhas do mesmo grupo de sinter | até 5 caminhões em 5 pilhas |

**Por quê:**

- A Aula 02 separa as perturbações P_k das vizinhanças de refinamento N_ℓ.
  Misturar as duas (como na primeira versão, que aplicava k × 3 movimentos
  de N1/N2/N3) confundia a definição das vizinhanças locais com a intensidade
  da perturbação.
- Quando a VND não consegue melhorar, o SHAKE passa progressivamente para
  regiões mais distantes: P1 mexe em 3 caminhões, P2 em 4 pilhas encadeadas e
  P3 em 5 pilhas ao mesmo tempo.
- **P3 fica dentro de um grupo** porque as pilhas de um mesmo sinter têm a
  mesma elegibilidade, então qualquer minério pode circular entre elas sem
  violar a elegibilidade. Na instância, cada grupo tem exatamente 5 pilhas.
- **P3 não altera o consumo global** e, portanto, nunca cria violação de
  disponibilidade. Ela redistribui minérios para mudar a qualidade de várias
  pilhas de uma vez. P1 e P2 alteram o consumo e podem violar a
  disponibilidade, o que é tratado pela regra de viabilidade.
- As perturbações **sorteiam posições (caminhões)**, seguindo o texto do
  enunciado. Diferente da busca local, aqui não se trata de explorar uma
  vizinhança, e sim de sortear caminhões ao acaso.

Os tamanhos 3, 4 e 5 foram consolidados após a calibração (`p1_positions`,
`p2_chain_length`, `p3_piles` em `GVNSConfig`; D015).

## 7. Critério de parada → número de avaliações

**Enunciado:** não especifica; pede curvas de convergência em função de
avaliações ou iterações.

**Escolha do grupo:** parar após um número fixo de avaliações de soluções
candidatas, igual para f1, f2 e f3.

**Por quê:**

- Contar avaliações não depende da máquina (tempo depende), então resultados
  e curvas são comparáveis entre objetivos e entre computadores do grupo.
- O eixo x das curvas de convergência fica igual ao critério de parada.

O valor consolidado é **200.000 avaliações** (`GVNSConfig.max_evaluations`,
configurável com `--budget`). O tempo de execução é registrado como informação
complementar.

## 8. Protocolo experimental

**Enunciado:** 5 execuções por objetivo, com mínimo, desvio-padrão e máximo,
as 5 curvas sobrepostas e uma figura da melhor solução.

**Escolha do grupo:**

1. **Calibração** dos parâmetros experimentais (orçamento, tamanho da amostra,
   P1/P2/P3) com um conjunto próprio de seeds.
2. **Congelar** o algoritmo e os parâmetros.
3. **Registrar as 5 seeds finais** em D017 antes da rodada oficial. Foram
   escolhidas 2016, 2017, 2018, 2019 e 2020, diferentes das seeds usadas no
   desenvolvimento, na calibração e nos testes.
4. **Executar** os três objetivos e gerar mínimo, desvio-padrão e máximo, as
   curvas e as figuras.
5. **Adicionar os resultados num commit ou PR separado** da implementação.

Detalhes:

- A heurística construtiva é determinística, então as 5 execuções partem da
  mesma solução inicial e diferem pela seed.
- O desvio-padrão é o amostral (n − 1).
- A curva mostra a **melhor solução viável encontrada até aquela avaliação**;
  o ponto inicial de cada curva marca quando a execução ficou viável.

O script exige as seeds explicitamente:

```bash
python scripts/run_mono_experiments.py --seeds S1 S2 S3 S4 S5
```

Cada execução salva, em `results/mono/runs/*.json`:

- versão do código, instância, objetivo e seed;
- parâmetros e orçamento;
- valores finais de f1, f2, f3 e viabilidade;
- tempo de execução;
- composição da melhor solução;
- curva de convergência.

## 9. Parâmetros atuais

| Parâmetro | Valor padrão | Status | Registro |
|---|---|---|---|
| Critério de parada | nº de avaliações | consolidado | D010 |
| Orçamento | 200.000 | consolidado | D010 |
| Ordem da VND | N1 → N2 → N3 | consolidado | D014 |
| Busca local | primeira melhoria | consolidado | D014 |
| Vizinhanças completas | N1 | consolidado | D014 |
| Tamanho da amostra (N2, N3) | 250 | consolidado | D014 |
| SHAKE | P1 → P2 → P3 (k_max = 3) | consolidado | D015 |
| Posições em P1 | 3 | consolidado | D015 |
| Pilhas na cadeia P2 | 4 | consolidado | D015 |
| Pilhas na permutação P3 | 5 | consolidado | D015 |
| Aceitação | melhoria estrita | consolidado | D016 |
| Seeds finais | 2016--2020 | consolidado | D017 |
