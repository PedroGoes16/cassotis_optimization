# Estratégias para tratamento de inviabilidade

## Escopo

A representação proposta elimina ou reduz algumas classes de inviabilidade:

- massa: preservada pelo tamanho fixo das pilhas;
- integralidade: preservada porque cada posição é um caminhão;
- elegibilidade: preservada pelos operadores sempre que aplicável.

A decisão de tratamento foi consolidada em D007 e se concentra em:

- limites de SiO2;
- limites de Al2O3;
- disponibilidade mínima global;
- disponibilidade máxima global.

A heurística construtiva sugerida no enunciado pode produzir solução inicialmente inviável quanto à qualidade. Portanto, a política escolhida precisa definir explicitamente o comportamento antes de existir uma solução factível.

## Medida de violação

Independentemente da política final, é útil calcular violações separadamente e de forma normalizada.

Para SiO2 da pilha \(p\):

\[
v_p^{Si}=
\begin{cases}
\dfrac{L_g^{Si}-S_p}{U_g^{Si}-L_g^{Si}}, & S_p<L_g^{Si}\\
0, & L_g^{Si}\le S_p\le U_g^{Si}\\
\dfrac{S_p-U_g^{Si}}{U_g^{Si}-L_g^{Si}}, & S_p>U_g^{Si}.
\end{cases}
\]

Definição análoga vale para Al2O3.

Para disponibilidade, com \(u_i=\sum_p x_{ip}\), uma medida candidata é:

\[
v_i^{disp}=
\frac{
\max(0,d_i^{min}-u_i,u_i-d_i^{max})
}{
\max(1,d_i^{max})
}.
\]

A medida agregada candidata é:

\[
V(X)=
\sum_p v_p^{Si}
+
\sum_p v_p^{Al}
+
\sum_i v_i^{disp}.
\]

Essa fórmula foi consolidada na D007 para comparar soluções inviáveis. A extensão para os limites adicionais de ε está registrada na D020.

## Rejeição

Movimentos inviáveis são descartados.

Vantagens: simplicidade, solução corrente sempre factível e ausência de parâmetros de penalização.

Riscos: requer solução inicial factível ou reparo anterior; pode impedir travessia de regiões inviáveis entre regiões factíveis.

## Penalização

Usa-se, por exemplo:

\[
F(X)=f(X)+\lambda V(X).
\]

Vantagens: permite atravessar regiões inviáveis.

Riscos: \(\lambda\) depende da escala de \(f\); custo e desvios quadráticos têm ordens de grandeza diferentes; a Entrega 2 adicionará normalização e scalarização, aumentando o risco de parâmetros difíceis de interpretar.

## Reparo

Após um movimento inviável, aplica-se um procedimento adicional para tentar retornar à região factível.

Vantagens: permite movimentos mais agressivos sem manter a população/trajetória em estado inviável.

Riscos: o reparador pode dominar o comportamento da metaheurística ou introduzir viés em favor de custo/qualidade.

## Operadores preservadores

Somente movimentos que mantêm todas as restrições são gerados.

Vantagens: nenhuma avaliação é gasta com solução inviável.

Riscos: vizinhança pode ficar pequena ou vazia perto das fronteiras.

## Regra de viabilidade / dominação por restrições

Comparação candidata:

1. solução viável vence solução inviável;
2. entre duas inviáveis, vence a de menor \(V(X)\);
3. entre duas viáveis, vence a de melhor objetivo.

Vantagens: não exige coeficiente \(\lambda\), funciona a partir de solução inicial inviável e é quase independente da escala do objetivo.

Risco: após entrar na região factível, a regra tende a impedir que a busca atravesse novamente regiões inviáveis.

## Estratégia em duas fases

Fase 1:

\[
\min V(X)
\]

até encontrar \(V(X)=0\).

Fase 2: otimizar \(f_j\) mantendo factibilidade.

Essa estratégia separa claramente os problemas de encontrar uma solução possível e encontrar uma solução boa.

## Nota histórica: experimento inicialmente proposto

Antes da consolidação, foi proposta a comparação de pelo menos duas políticas sob o mesmo orçamento e mesmas seeds. Essa comparação não foi realizada; a escolha registrada na D007 se apoia nas razões ali documentadas, não em superioridade experimental demonstrada.

Registrar:

- taxa de execuções que encontram solução factível;
- avaliações até a primeira solução factível;
- proporção de candidatos inviáveis;
- melhor valor do objetivo após orçamento fixo;
- tempo de execução;
- sensibilidade a parâmetros adicionais.

Para o estado e a evidência efetivos da decisão, prevalece a D007 no registro formal.
