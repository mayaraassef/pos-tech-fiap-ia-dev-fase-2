# Relatório Técnico — Projeto 2: Otimização de Rotas para Distribuição de Medicamentos e Insumos

**Tech Challenge — Fase 2 · Pós-Graduação FIAP/IADT**

---

## 1. Visão geral

O sistema `medroute` resolve o problema do **"caixeiro viajante médico"** — na prática, um **Problema de Roteamento de Veículos com Capacidade (CVRP)** ampliado com autonomia limitada e prioridades clínicas — usando **Algoritmos Genéticos**, evoluído do código base de TSP em Python fornecido (`genetic_algorithm_tsp/`, mantido fora do repositório como referência).

Uma **LLM (Google Gemini)** transforma a saída matemática do GA em:

- instruções operacionais detalhadas para motoristas e equipes de entrega;
- relatórios diários/semanais de eficiência logística;
- sugestões automáticas de melhoria do processo;
- respostas a perguntas em linguagem natural sobre as rotas.

**Stack:** Python 3.14 · Pipenv · Folium + Matplotlib · `google-generativeai` · pytest (56 testes)

---

## 2. Arquitetura da solução

Camadas desacopladas em `src/medroute/` (detalhes e diagramas em `docs/architecture.md`):

```
domain/          Entidades (DeliveryPoint, Vehicle, Depot, Route, RoutePlan,
                 Priority) + restrições (capacidade, autonomia, distância)
ga/              Cromossomo + decoder multi-veículo, operadores genéticos,
                 função fitness, motor evolutivo (GeneticVRPSolver)
visualization/   MapRenderer (Folium → HTML) + gráfico de convergência (PNG)
llm/             GeminiClient (protocolo LLMClient), prompts.py,
                 RouteReportGenerator
data/            Cenário hospitalar de exemplo (12 entregas, 3 veículos)
cli.py           Ponto de entrada: otimização → artefatos → relatórios LLM
```

Fluxo de dados:

```
depot + deliveries + vehicles → GA (evolução de permutações)
  → decode_chromosome (split guloso por veículo)
  → RoutePlan → {mapa HTML, PNG convergência, resumo JSON}
              → {plan_context → prompts → Gemini → instruções/relatório/Q&A}
```

---

## 3. Implementação do algoritmo genético a partir do código base

### 3.1 Linhagem do código base

| Componente do TSP base | Destino no `medroute` |
|---|---|
| `calculate_distance` (euclidiana) | `domain.models.distance` — mesma fórmula |
| `calculate_fitness` (distância do ciclo) | `domain.constraints.route_distance` — rota fechada depósito→paradas→depósito |
| `generate_random_population` | `ga.operators.generate_random_population` — permutações de índices |
| `order_crossover` (OX) | `ga.operators.order_crossover` — **algoritmo idêntico**, generalizado para índices inteiros |
| `mutate` (troca de adjacentes) | `ga.operators.mutate` — troca de 2 posições quaisquer + `inversion_mutation` (atende o TODO do próprio código base) |
| Seleção roleta `weights=1/f` (`tsp.py`) | `ga.operators.roulette_selection` (+ `tournament_selection` alternativo) |
| `sort_population` | Ordenação interna no loop de `ga.engine` |
| Loop elite `[population[0]]` + filhos | `ga.engine.GeneticVRPSolver.solve` — mesma estrutura, com `GAConfig` (hiperparâmetros, seed, pesos) |

### 3.2 Representação genética

No TSP base, o cromossomo era a própria rota (lista de coordenadas). Para suportar **múltiplos veículos**, adotamos a representação clássica de **permutação de entregas + separador implícito**:

- **Cromossomo** `[3, 0, 5, 1, 4, 2]` = apenas uma ordem de visita;
- **Decodificador guloso** (`ga/chromosome.py`) varre a permutação e atribui cada entrega ao veículo corrente **somente se a inserção não violar capacidade nem autonomia**; o que não couber segue para o próximo veículo; sobras finais → `unserved` (penalizadas).

**Por que essa escolha:** mantém os operadores de permutação do código base (OX, swap, inversão) válidos sem reparo pós-cruzamento — toda permutação é um cromossomo legal e a viabilidade operacional é garantida na decodificação.

### 3.3 Operadores genéticos

- **Seleção**: roleta proporcional a `1/fitness` (como no `tsp.py` base) e torneio (k=3) configurável.
- **Crossover**: OX — segmento contíguo do pai 1 + preenchimento na ordem do pai 2, sem duplicar genes.
- **Mutação**: swap de duas posições (padrão) ou inversão de segmento — ambas preservam a permutação.
- **Elitismo**: os melhores indivíduos passam inteiros → histórico de melhor fitness estritamente não-crescente (verificado em teste).

### 3.4 Função fitness

```
fitness = Σ_veículos [ distância(rota) + custo_fixo_veículo
                     + Σ_paradas prioridade(p) × distância_chegada(p) ]
        + Σ_não_atendidos  10_000 × prioridade(p)
        + penalidades de violação residuais (rede de segurança, 1e6)
```

- **`prioridade × distância de chegada`**: entrega CRITICAL (peso 10) atendida tarde custa 10× mais que REGULAR (peso 1) no mesmo ponto → o GA antecipa entregas críticas quando o desvio compensa.
- **`unserved × prioridade`**: deixar um medicamento crítico de fora (100 000) é proibitivamente pior que um insumo regular (10 000).

---

## 4. Tratamento das restrições adicionais

| Restrição exigida | Estratégia |
|---|---|
| **Prioridades** (medicamentos críticos × insumos regulares) | `Priority{REGULAR=1, HIGH=3, CRITICAL=10}`; soft constraint no fitness (tardança × peso) e penalidade escalonada em `unserved` |
| **Capacidade limitada de carga** | Hard constraint no decoder: inserção rejeitada se `carga + demanda > capacidade` → split automático para o próximo veículo |
| **Autonomia limitada (distância máxima)** | Hard constraint no decoder: inserção rejeitada se a rota resultante exceder `max_distance` |
| **Múltiplos veículos (VRP)** | Decoder atribui entregas à frota em sequência; frota **heterogênea** (capacidade/autonomia/custo diferentes por veículo) |
| **Extra: custo fixo por veículo** | `fixed_cost` no fitness → o GA evita acionar veículo desnecessário |
| **Extra: cobertura** | `unserved` documenta e penaliza frota insuficiente |

Cada restrição possui **teste unitário dedicado** (`test_chromosome.py`, `test_fitness.py`, `test_engine.py`): split por capacidade, limite de autonomia, crítico-cedo < crítico-tarde, zero violações na solução final, determinismo por seed.

---

## 5. Integração com LLMs

### 5.1 Abordagem

SDK oficial `google-generativeai`, com arquitetura desacoplada:

- `LLMClient` (protocolo `generate(prompt) -> str`) — permite mock nos testes e troca de provedor sem reescrever a camada;
- `GeminiClient` — modelo via `GEMINI_MODEL` (default `gemini-3.7-flash`), **retry com backoff** lendo o `retry_delay` das respostas 429;
- Chave lida **exclusivamente** do `.env` (gitignored) — `tests/test_setup.py::test_api_key_never_hardcoded` trava se a chave aparecer no código.

> O pacote `google-generativeai` foi descontinuado pelo Google em favor de `google-genai`; foi mantido por ser o SDK indicado para o projeto. A migração futura é trivial (import em `client.py`).

### 5.2 Engenharia de prompts (`llm/prompts.py`)

Todos os prompts seguem a mesma estrutura:

1. **Papel de sistema embutido** — "assistente de logística do sistema de distribuição de medicamentos do hospital universitário" + legenda das prioridades;
2. **Contexto estruturado** — `plan_context()` serializa o `RoutePlan`: métricas globais, rotas por veículo (capacidade, autonomia, km, carga) e cada parada em ordem com prioridade e demanda;
3. **Tarefa com formato de saída especificado**:

| Saída | Exigências no prompt |
|---|---|
| Instruções dos motoristas | Seção `## Veículo <id>` com itinerário numerado, alertas para CRITICAL, status carga/autonomia, checklist final comum |
| Relatório de eficiência | 5 seções fixas: resumo executivo, desempenho por veículo, atendimento a prioridades, economia vs. baseline ingênuo, sugestões de melhoria |
| Sugestões de melhoria | Mesmo contexto do relatório, retornando apenas a seção de sugestões numerada |
| Q&A | *Grounding* explícito: "responda APENAS com base nos dados do plano; se não constar, diga isso" |

### 5.3 Qualidade observada (execução real, artefatos em `output/`)

- **Instruções**: itinerários corretos por veículo, alertas clínicos plausíveis (lacre térmico, conferência lote a lote), análise de margem de autonomia;
- **Relatório**: tabela por veículo com ocupação %, seções completas, comparativo quantitativo com baseline;
- **Sugestões**: insight operacional real — detectou o Veículo 2 subutilizado (27,8%) e sugeriu rebalanceamento e ajuste de pesos da função fitness;
- **Q&A**: respondeu corretamente "Qual veículo faz mais entregas críticas?" (V0, 2 entregas) e respeitou o grounding ao admitir o que não consta nos dados.

---

## 6. Visualizações geradas

| Artefato (`output/`) | Conteúdo |
|---|---|
| `rotas_otimizadas.html` | Mapa Folium interativo: depósito com ícone, marcadores por prioridade (vermelho=CRITICAL, laranja=HIGH, verde=REGULAR, cinza=não atendido), polyline por veículo em camadas ativáveis, popups com ordem/demanda/prioridade. Tiles **Esri World Street Map** (OSM bloqueia `file://` sem referer; OSM segue como camada alternativa) |
| `convergencia_fitness.png` | Curva do melhor fitness por geração — queda monotônica (evidência do elitismo) |
| `resumo_otimizacao.json` | Plano serializado: rotas, distâncias, cargas, métricas |
| `instrucoes_motoristas.md` | Instruções geradas pela LLM |
| `relatorio_eficiencia.md` | Relatório de eficiência gerado pela LLM |
| `sugestoes_melhoria.md` | Sugestões de melhoria geradas pela LLM |

A projeção das coordenadas cartesianas do problema para o mapa usa transformação afim ancorada em São Paulo (`meters_per_unit` configurável no `MapRenderer`).

---

## 7. Comparativo de desempenho com outras abordagens

Cenário: 12 entregas, frota 3 veículos (cap. 15/15/18, autonomia 1200/1200/1500). Fitness menor = melhor. Reproduzível via `scripts/benchmark.py` e pela seção 5 do notebook.

| Abordagem | Fitness | Distância | Viável? | Observação |
|---|---|---|---|---|
| TSP ingênuo (1 veículo) | — | 2 284,2 km | **Não** | Viola capacidade (32 > 15) e autonomia — motiva o VRP |
| Amostragem aleatória (5 000 permutações) | 13 920,1 | — | Sim | Sem direção evolutiva |
| Guloso nearest-neighbor | 11 949,8 | 1 660,7 km | Sim | Menor km, **mas ignora prioridade** → penalidade alta |
| **GA-VRP (seeds 42/7/123)** | **10 285 / 10 850 / 10 507** | 1 845 / 1 899 / 1 545 km | Sim | Melhor compromisso distância × prioridade × restrições |

**Leitura:** o guloso minimiza km localmente, mas o fitness composto do GA fica **~14% melhor** porque o GA equilibra quilometragem com antecipação de entregas críticas — o objetivo real do contexto hospitalar. Contra amostragem aleatória, a melhoria é **~26%** com orçamento computacional da mesma ordem (15s vs. população 150 × 400 gerações ≈ 15s).

---

## 8. Código, organização e testes

- **Ambiente**: Pipenv + virtualenv; pacote `src/` instalável (`pipenv run pip install -e .`); dependências travadas em `Pipfile.lock`.
- **Testes**: **56 testes passando + 1 skip** (teste live da API, opt-in `GEMINI_RUN_LIVE=1`), organizados por fase:
  - `test_setup.py` — ambiente, pacote, chave fora do código;
  - `test_domain.py`, `test_operators.py` — fórmulas, permutações válidas, viés da seleção;
  - `test_chromosome.py`, `test_fitness.py`, `test_engine.py` — cada restrição matemática;
  - `test_visualization.py` — HTML com marcadores/polylines, PNG válido, CLI gera artefatos;
  - `test_llm.py` — prompts injetam o plano e exigem formato, gerador com `FakeClient`;
  - `test_docs.py` — existência de todos os artefatos de documentação.
- **Demo**: `notebooks/demo_medroute.ipynb` (executado, com outputs gravados) + `scripts/benchmark.py` + CLI (`python -m medroute.cli [--llm] [--ask]`).

---

## 9. Desafios e soluções implementadas

| Desafio | Solução |
|---|---|
| Restrições duras sem quebrar operadores de permutação | Representação permutação + decoder guloso (hard constraints no split, soft no fitness) |
| Prioridade clínica sem inviabilizar soluções | Pesos moderados (1/3/10) permitem trade-off real |
| Quota free-tier do Gemini (20 req/dia por modelo) | Retry com backoff a partir do `retry_delay` + modelo parametrizável (`GEMINI_MODEL`) para trocar de pool |
| Modelo `gemini-2.5-flash` descontinuado | Descoberta via `list_models()`; default atualizado para `gemini-3.7-flash` |
| Tiles OSM bloqueados em `file://` (403, política de tiles) | Camada base Esri World Street Map; OSM como alternativa `show=False` |
| Console Windows (cp1252) sem suporte a Unicode | Saídas CLI restritas a ASCII |

---

## 10. Como executar (resumo)

```bash
pipenv install --dev
pipenv run pip install -e .
# copiar .env.example → .env e preencher GEMINI_API_KEY
pipenv run pytest                                  # 56 testes
pipenv run python -m medroute.cli                  # otimização + mapa
pipenv run python -m medroute.cli --llm --ask "?"  # + LLM
pipenv run python scripts/benchmark.py             # comparativo
pipenv run jupyter notebook notebooks/demo_medroute.ipynb
```

Instruções detalhadas no `README.md`.
