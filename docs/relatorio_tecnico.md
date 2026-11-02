# Relatório Técnico — Projeto 2: Otimização de Rotas para Distribuição de Medicamentos e Insumos

**Tech Challenge — Fase 2 · Pós-Graduação FIAP/IADT**

## 1. Visão geral da solução

O sistema `medroute` resolve o problema do "caixeiro viajante médico" — na prática, um **Problema de Roteamento de Veículos com capacidade (CVRP)** ampliado com autonomia limitada e prioridades clínicas — usando **Algoritmos Genéticos**, evoluído do código base de TSP em Python fornecido (`genetic_algorithm_tsp/`, mantido fora do repositório). Uma LLM (Google Gemini) transforma a saída matemática do GA em instruções operacionais para motoristas, relatórios de eficiência, sugestões de melhoria e respostas a perguntas em linguagem natural.

## 2. Implementação do algoritmo genético a partir do código base

### 2.1 O que foi preservado do código base

| Componente do base (`genetic_algorithm.py` / `tsp.py`) | Destino no `medroute` |
|---|---|
| `calculate_distance` (euclidiana) | `domain.models.distance` — mesma fórmula |
| `calculate_fitness` (distância do ciclo) | `domain.constraints.route_distance` — rota fechada depósito→paradas→depósito |
| `generate_random_population` | `ga.operators.generate_random_population` — permutações de índices |
| `order_crossover` (OX) | `ga.operators.order_crossover` — **algoritmo idêntico**, generalizado para índices inteiros |
| `mutate` (troca adjacentes) | `ga.operators.mutate` — troca de 2 posições quaisquer + `inversion_mutation` (operador clássico de TSP sugerido no TODO do próprio base) |
| Seleção roleta `weights=1/fitness` | `ga.operators.roulette_selection` (+ `tournament_selection` alternativo) |
| `sort_population` | Ordenação interna no loop do `engine.py` |
| Loop: elite `population[0]` + filhos por crossover+mutação | `ga.engine.GeneticVRPSolver.solve` — mesma estrutura |

### 2.2 Representação genética

No TSP base, o cromossomo era a própria rota (lista de coordenadas). Para múltiplos veículos, adotamos a representação clássica de **permutação de entregas + separador implícito**: o cromossomo `[3, 0, 5, 1, 4, 2]` é apenas uma **ordem de visita**; a divisão em rotas por veículo é feita por um **decodificador guloso** (`ga/chromosome.py`):

```
para cada veículo da frota (em ordem):
    varre o cromossomo na ordem
    insere a entrega se NÃO violar: carga + demanda ≤ capacidade
                                  E distância da rota ≤ autonomia
    entregas que não couberem ficam para o próximo veículo
sobras → unserved (penalizadas)
```

**Vantagem:** os operadores de permutação do código base (OX, swap) permanecem válidos sem adaptação — qualquer permutação continua sendo um cromossomo legal, e a viabilidade operacional é garantida pelo decoder, não por reparo pós-cruzamento.

### 2.3 Operadores genéticos

- **Seleção**: roleta proporcional a `1/fitness` (como o `tsp.py` base) e torneio (k=3) como alternativa configurável.
- **Crossover**: OX (Order Crossover) — mantém um segmento contíguo do pai 1 e completa na ordem do pai 2, sem duplicar genes.
- **Mutação**: swap de duas posições (padrão) ou inversão de segmento.
- **Elitismo**: os `elitism_count` melhores indivíduos passam inteiros para a próxima geração → histórico de melhor fitness é monotonicamente não-crescente.

### 2.4 Função fitness

```
fitness = Σ_veículos [ distância(rota) + custo_fixo_veículo
                     + Σ_paradas prioridade(p) × distância_chegada(p) ]
        + Σ_não_atendidos  10_000 × prioridade(p)
        + penalidades de violação (rede de segurança, 1e6)
```

- `prioridade × distância de chegada`: entrega CRITICAL (peso 10) atendida no km 800 custa 10× mais que uma REGULAR (peso 1) no mesmo ponto → o GA ordena críticas primeiro quando o desvio é aceitável.
- `unserved`: não atender uma entrega CRITICAL custa 100_000 — o GA prefere qualquer alocação viável.

## 3. Estratégias para as restrições adicionais

| Restrição do enunciado | Como foi tratada |
|---|---|
| **Prioridades** (medicamentos críticos × insumos regulares) | Enum `Priority{REGULAR=1, HIGH=3, CRITICAL=10}`; soft constraint no fitness (tardança × peso) e hard-ish no `unserved` (penalidade × peso) |
| **Capacidade limitada de carga** | Hard constraint no decoder: inserção rejeitada se `carga + demanda > capacidade` → o veículo fecha a rota e o próximo assume |
| **Autonomia limitada (distância máx.)** | Hard constraint no decoder: inserção rejeitada se a rota resultante exceder `max_distance` |
| **Múltiplos veículos (VRP)** | Decoder atribui entregas a cada veículo em sequência; frota heterogênea (capacidades/autonomias diferentes por veículo) |
| **Extra: custo fixo por veículo** | `fixed_cost` entra no fitness → o GA evita acionar veículo desnecessário |
| **Extra: cobertura completa** | `unserved` com penalidade escalonada por prioridade documenta (e penaliza) frota insuficiente |

## 4. Integração com LLMs

### 4.1 Abordagem

SDK oficial `google-generativeai` (modelo configurável via `GEMINI_MODEL`, padrão `gemini-3.7-flash`), chave lida exclusivamente do `.env` (nunca no código — há um teste que verifica isso). O cliente implementa retry com backoff extraído do `retry_delay` da resposta 429. Arquitetura desacoplada: `RouteReportGenerator` depende do protocolo `LLMClient` (`generate(prompt) -> str`), permitindo mock nos testes e troca de provedor sem reescrever a camada.

> Nota: o pacote `google-generativeai` foi descontinuado pelo Google em favor de `google-genai` (mesma API de alto nível: `GenerativeModel.generate_content`). Foi mantido por ser o SDK indicado para o projeto; a migração futura é trivial (trocar o import em `client.py`).

### 4.2 Engenharia de prompt (`llm/prompts.py`)

Todos os prompts compartilham um **papel de sistema embutido** ("assistente de logística do sistema de distribuição de medicamentos"), **contexto estruturado** serializado do `RoutePlan` (métricas, rotas por veículo, ordem e prioridade de cada parada) e uma **tarefa com formato de saída especificado**:

1. **Instruções dos motoristas** — exige seção `## Veículo <id>` com itinerário numerado, alertas para entregas CRITICAL e status carga/autonomia; termina com checklist comum.
2. **Relatório de eficiência** — exige 5 seções fixas: resumo executivo, desempenho por veículo, atendimento a prioridades, economia de recursos (vs. baseline ingênuo informado no prompt) e sugestões de melhoria.
3. **Sugestões de melhoria** — mesmo contexto do relatório, com instrução de retornar apenas a seção de sugestões numerada.
4. **Q&A** — prompt com *grounding* explícito: "responda APENAS com base nos dados do plano; se a informação não constar, diga isso" — observado na prática: o modelo recusou extrapolar a justificativa interna do GA.

### 4.3 Qualidade observada (execução real)

- Instruções: itinerários corretos por veículo, alertas clínicos plausíveis (lacre térmico, conferência lote a lote), análise correta de margem de autonomia.
- Relatório: tabela por veículo com ocupação %, seções completas, comparação quantitativa com baseline.
- Sugestões: insights operacionais reais — detectou Veículo 2 subutilizado (27,8%) e sugeriu rebalanceamento e ajuste de pesos da função fitness.
- Q&A: respondeu corretamente "Qual veículo faz mais entregas críticas?" (V0, com 2) e respeitou o grounding.

## 5. Visualizações

- **`output/rotas_otimizadas.html`** — mapa Folium/OpenStreetMap: depósito com ícone hospitalar, marcadores coloridos por prioridade (vermelho=CRITICAL, laranja=HIGH, verde=REGULAR, cinza=não atendido), uma polyline por veículo (camadas ativáveis), popups com ordem da parada/demanda/prioridade. As coordenadas cartesianas do problema são projetadas por transformação afim sobre São Paulo (`meters_per_unit` configurável).
- **`output/convergencia_fitness.png`** — curva do melhor fitness por geração (queda monotônica, evidência do elitismo).
- **`output/resumo_otimizacao.json`** — plano serializado (rotas, distâncias, métricas).
- **`output/instrucoes_motoristas.md`, `relatorio_eficiencia.md`, `sugestoes_melhoria.md`** — saídas da LLM.

## 6. Comparativo de desempenho com outras abordagens

Cenário: 12 entregas, frota 3 veículos (cap. 15/15/18, autonomia 1200/1200/1500). Fitness menor = melhor. `scripts/benchmark.py` reproduz os números.

| Abordagem | Fitness | Distância | Viável? | Observação |
|---|---|---|---|---|
| TSP ingênuo (1 veículo) | — | 2 284,2 km | **Não** | Viola capacidade (32 > 15) e autonomia — motiva o VRP |
| Amostragem aleatória (5 000 permutações) | 13 920,1 | — | Sim | Sem direção evolutiva, explode combinatorialmente |
| Guloso nearest-neighbor | 11 949,8 | 1 660,7 km | Sim | Menor km total, **mas ignora prioridade** → penalidade alta |
| **GA-VRP (seeds 42/7/123)** | **10 285 / 10 850 / 10 507** | 1 845 / 1 899 / 1 545 km | Sim | Melhor compromisso distância×prioridade×restrições |

Leitura: o guloso minimiza km localmente, mas o fitness composto do GA é ~14% melhor porque o GA equilibra quilometragem com **antecipação de entregas críticas** — exatamente o objetivo do contexto hospitalar. O GA também supera a amostragem aleatória em ~26% com orçamento computacional da mesma ordem.

## 7. Testes automatizados

50 testes (`pytest`), um arquivo por fase/requisito:

- `test_setup.py` (Fase 1): ambiente, pacote, `.env` sem chave hardcoded.
- `test_domain.py`, `test_operators.py` (Fase 2): fórmulas, validade das permutações, bias da seleção.
- `test_chromosome.py` (Fase 2): cada restrição matemática — capacidade, autonomia, sem perda/duplicação de genes, `unserved`.
- `test_fitness.py` (Fase 2): crítico-cedo < crítico-tarde, penalidades, custo fixo.
- `test_engine.py` (Fase 2): integração — todas as 12 entregas atendidas, zero violações, determinismo por seed, histórico não-crescente.
- `test_visualization.py` (Fase 3): HTML contém marcadores/polylines, PNG com assinatura válida, CLI gera artefatos.
- `test_llm.py` (Fase 4): prompts injetam o plano e exigem formato, gerador funciona com `FakeClient`, teste live opcional (`GEMINI_RUN_LIVE=1`).
- `test_docs.py` (Fase 5): existência dos artefatos de documentação.

## 8. Desafios e soluções

- **Restrições sem quebrar operadores**: resolvido com representação permutação+decoder (hard constraints no split, soft no fitness).
- **Prioridade sem inviabilizar**: pesos moderados no fitness permitem trade-off (crítico antecipado quando o desvio compensa).
- **Quota da API Gemini (free tier, 20 req/dia/modelo)**: cliente com retry/backoff + modelo parametrizável (`GEMINI_MODEL`) para trocar entre pools de quota.
- **Console Windows (cp1252)**: saída CLI limitada a ASCII.
