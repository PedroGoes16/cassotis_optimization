# Checklist das entregas

## Entrega 1 — mono-objetivo

### Formulação
- [x] parâmetros
- [x] variáveis
- [x] \(f_1\): custo
- [x] \(f_2\): desvio quadrático de SiO2
- [x] \(f_3\): desvio quadrático de Al2O3
- [x] restrição de massa
- [x] limites de qualidade
- [x] elegibilidade
- [x] disponibilidade global

### Algoritmo
- [x] representação da solução
- [x] heurística construtiva - baseline implementada
- [x] VNS ou GVNS (GVNS, D009)
- [x] N1
- [x] N2
- [x] N3 definida, justificada e implementada
- [x] perturbação P1/P2/P3 (D015)
- [x] busca local (D014)
- [x] tratamento de inviabilidade (D007)
- [x] aceitação (D016)
- [x] parada (D010)
- [x] pseudocódigo completo (`docs/gvns_decisoes.md` e `report/main.tex`)

### Experimentos
- [x] script de experimentos (`scripts/run_mono_experiments.py`)
- [x] calibração dos parâmetros experimentais (orçamento, amostra, P1/P2/P3)
- [x] congelar configuração e registrar as 5 seeds finais (D017)
- [x] 5 execuções de \(f_1\)
- [x] 5 execuções de \(f_2\)
- [x] 5 execuções de \(f_3\)
- [x] min/std/max
- [x] curvas de convergência
- [x] visualização das melhores soluções

### Entregáveis
- [x] conteúdo da Entrega 1 no relatório cumulativo
- [ ] apresentação de até 10 minutos

## Entrega 2 — multiobjetivo

- [x] normalização baseada na Entrega 1
- [x] Soma Ponderada
- [x] epsilon-restrito
- [x] pesos justificados
- [x] valores de epsilon justificados
- [x] 5 execuções por abordagem/configuração definida
- [x] soluções não dominadas
- [x] projeções f1 x f2, f1 x f3 e f2 x f3
- [x] comparação de variabilidade e regiões alcançadas no relatório
- [x] conteúdo cumulativo em `report/main.tex`
- [ ] revisão final do grupo e submissão do relatório e códigos

## Entrega 3 — decisão multicritério

- [ ] escolher 2 entre AHP, ELECTRE e PROMETHEE
- [ ] definir pelo menos 4 critérios
- [ ] incluir f1, f2 e f3
- [ ] definir pelo menos um atributo adicional conflitante
- [ ] justificar pesos e parâmetros
- [ ] tratar incomparabilidade, se ocorrer
- [ ] análise de sensibilidade
- [ ] tabela de alternativas e critérios
- [ ] destacar escolhas nas projeções
- [ ] visualizar solução final
- [ ] Streamlit
- [ ] relatório final cumulativo
- [ ] apresentação final de até 10 minutos
