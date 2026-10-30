# Relatório cumulativo consolidado — Entrega 2

Relatório acadêmico em português, com oito páginas A4 e conteúdo cumulativo das Entregas 1 e 2 da disciplina Teoria da Decisão (UFMG, 2026/2).

## Fontes utilizadas

- PDF do relatório do Allan, correspondente ao PR #3 (`docs/relatorio-entrega2`), como base para formulação e análise comparativa das frentes.
- PDF do relatório do Pedro Goes, correspondente ao PR #4 (`entrega-2-relatorio-validacao`), para explicação didática da N3, indicadores de dispersão e cuidados de validação/reprodutibilidade.
- Enunciado da disciplina `Case-UFMG-Teoria_da_Decisão.pdf`.
- Resultados oficiais de `results/mono_final/` e `results/multi_final/` do repositório, conferidos nas revisões do projeto.
- Implementação de N3 em `src/cassotis_optimization/algorithms/vizinhancas.py`.

## Consolidações e correções

1. Mantidos os seis integrantes listados no relatório de Pedro, inclusive Pedro Goes. Confirmar apenas a grafia final dos nomes antes da entrega.
2. A N3 recebeu um exemplo comentado, um pequeno esquema, a variação de custo, o caráter atômico, a distinção em relação à N2 e ao SHAKE P2, bem como a demonstração de amostragem uniforme por prefixos. Os 5.034 prefixos e 66.418 movimentos na solução construtiva foram conferidos.
3. Corrigida, com base no CSV oficial, a contagem de vetores na faixa `2,90 < f2 < 5,44`: **32** na frente própria epsilon-restrita, não 24.
4. Esclarecidas as comparações de monotonicidade em epsilon: **3 inversões em 420 pares aninhados comparáveis**, preservando a mesma seed.
5. Evitado o uso de “ótimo global” para soluções-âncora; explicitado que epsilon igual a 1 ainda impõe restrições e que a normalização permite valores fora de [0, 1].
6. Aproveitadas as medianas dos desvios-padrão por configuração do relatório de Pedro; não usadas como prova de superioridade estatística.
7. As seis figuras de Pareto foram dispostas por pares de objetivos e lado a lado para comparação direta. As demais figuras foram aproveitadas dos PDFs de origem.
8. A proposta de auditoria computacional e a assinatura versão 2 do PR #4 são descritas com ressalva: não fizeram parte da execução histórica do commit `d5e0d94`. **Nenhum resultado oficial foi reexecutado ou alterado por este relatório.**

## Compilação

Com LaTeX instalado, execute na pasta deste projeto:

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

Ou `pdflatex main.tex` duas vezes. As 12 figuras referenciadas são distribuídas na pasta `figures/`. O PDF renderizado `main.pdf` também está incluído no pacote.

## Integração ao repositório

Copie `main.tex` para `report/main.tex` e as imagens utilizadas para `report/figures/`, preservando os nomes. Compile novamente no ambiente do repositório e confira o PDF antes de commitar. O pacote não altera pull requests nem o código-fonte da GVNS automaticamente.
