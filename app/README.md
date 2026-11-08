# Aplicação Streamlit — Entrega 3

A aplicação explora as soluções não dominadas, os rankings PROMETHEE II e ELECTRE III, a análise de sensibilidade e a composição recomendada. Ela lê os resultados oficiais e reutiliza `evaluate()` e `plot_solution()`; fórmulas de custo, qualidade e restrições não são reimplementadas na interface.

## Execução

Na raiz do repositório:

```powershell
pip install -e ".[app]"
python scripts/run_decision_analysis.py
streamlit run app/app.py
```

O aplicativo contém:

- visão geral da recomendação;
- projeções interativas dos quatro critérios;
- comparação normalizada entre alternativas;
- rankings e conjunto máximo dos dois métodos;
- 15 cenários de sensibilidade;
- qualidade e composição das pilhas da solução final.
