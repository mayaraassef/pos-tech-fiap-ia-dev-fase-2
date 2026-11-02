# medroute — Otimização de Rotas para Distribuição de Medicamentos e Insumos

**Projeto 2 · Tech Challenge Fase 2 · Pós-Graduação FIAP/IADT**

Sistema de otimização do "caixeiro viajante médico" (TSP → VRP) via **Algoritmos
Genéticos**, evoluído do código base TSP fornecido (fora deste repositório), com relatórios,
instruções para motoristas e Q&A em linguagem natural via **Google Gemini**.

## Funcionalidades

- VRP com **múltiplos veículos**, **capacidade limitada**, **autonomia limitada**
  e **prioridades de entrega** (CRITICAL / HIGH / REGULAR)
- Mapa interativo das rotas (`folium` → HTML) + gráfico de convergência do GA
- Instruções por motorista, relatório de eficiência, sugestões de melhoria e
  perguntas em linguagem natural — gerados por LLM
- 50 testes automatizados (`pytest`)

## Estrutura

```
├── src/medroute/
│   ├── domain/                # entidades + restrições (capacidade, autonomia)
│   ├── ga/                    # cromossomo/decoder, operadores, fitness, engine
│   ├── visualization/         # mapa Folium + gráfico Matplotlib
│   ├── llm/                   # cliente Gemini, prompts, gerador de relatórios
│   ├── data/sample_scenario.py
│   └── cli.py                 # ponto de entrada
├── scripts/benchmark.py       # GA vs. guloso vs. aleatório vs. TSP ingênuo
├── notebooks/demo_medroute.ipynb  # notebook de demonstração end-to-end
├── tests/                     # suíte pytest (50 testes)
├── docs/architecture.md       # diagramas da solução
├── docs/relatorio_tecnico.md  # relatório técnico completo
├── Pipfile / pyproject.toml / pytest.ini
└── .env.example               # template da chave do Gemini
```

## Setup

Requisitos: **Python ≥ 3.10** e **Pipenv** (`pip install pipenv`).

```bash
# 1. instalar dependências (cria o virtualenv automaticamente)
pipenv install --dev

# 2. registrar o pacote src/ no ambiente
pipenv run pip install -e .

# 3. configurar a chave do Gemini
#    copie .env.example para .env e preencha GEMINI_API_KEY
#    (o .env está no .gitignore — nunca commitar a chave)
```

## Execução

```bash
# otimização + mapa HTML + gráfico PNG + resumo JSON  →  pasta output/
pipenv run python -m medroute.cli

# idem + instruções dos motoristas + relatório de eficiência via Gemini
pipenv run python -m medroute.cli --llm

# pergunta em linguagem natural sobre o plano otimizado
pipenv run python -m medroute.cli --ask "Qual veiculo faz mais entregas criticas?"

# comparativo de desempenho (GA vs. baselines)
pipenv run python scripts/benchmark.py

# notebook de demonstração end-to-end
pipenv run jupyter notebook notebooks/demo_medroute.ipynb
```

Artefatos gerados em `output/`:
`rotas_otimizadas.html` · `convergencia_fitness.png` · `resumo_otimizacao.json` ·
`instrucoes_motoristas.md` · `relatorio_eficiencia.md` · `sugestoes_melhoria.md`

## Testes

```bash
pipenv run pytest            # suíte completa (50 testes)
pipenv run pytest -v         # detalhado
GEMINI_RUN_LIVE=1 pipenv run pytest tests/test_llm.py   # inclui teste live da API
```

## Configurações úteis

| Variável de ambiente | Efeito |
|---|---|
| `GEMINI_API_KEY` | **obrigatória** para as funcionalidades LLM |
| `GEMINI_MODEL` | modelo Gemini (default `gemini-3.7-flash`; útil para contornar quota diária por modelo) |
| `GEMINI_RUN_LIVE` | `1` habilita o teste que chama a API real |

Hiperparâmetros do GA em `medroute.ga.GAConfig` (população, gerações, taxa de
mutação, seleção roleta/torneio, mutação swap/inversão, seed, pesos do fitness).

## Documentação

- [docs/architecture.md](docs/architecture.md) — diagramas e decisões
- [docs/relatorio_tecnico.md](docs/relatorio_tecnico.md) — estratégia do GA,
  restrições, integração LLM + prompts, comparativo de desempenho
