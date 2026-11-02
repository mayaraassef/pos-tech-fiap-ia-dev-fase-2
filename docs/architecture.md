# Arquitetura — medroute (Projeto 2: Otimização de Rotas Médicas)

## Visão geral

```mermaid
flowchart LR
    subgraph Entrada
        D[Depot - Hospital Central]
        E[DeliveryPoints: demanda + prioridade]
        V[Vehicle: capacidade + autonomia]
    end

    subgraph "Motor Genético (medroute.ga)"
        POP[População: permutações] --> FIT[Fitness: distância + prioridade + penalidades]
        FIT --> SEL[Seleção: roleta / torneio]
        SEL --> OX[Crossover OX]
        OX --> MUT[Mutação: swap / inversão]
        MUT --> DEC[Decoder guloso multi-veículo]
        DEC --> FIT
    end

    subgraph "Saídas"
        PLAN[RoutePlan]
        MAP[Mapa HTML - Folium]
        PLOT[Gráfico convergência PNG]
        JSON[resumo_otimizacao.json]
    end

    subgraph "Camada LLM (medroute.llm)"
        CTX[plan_context: serialização do plano]
        P1[Prompt: instruções motoristas]
        P2[Prompt: relatório eficiência]
        P3[Prompt: Q&A grounded]
        GEM[GeminiClient - google-generativeai]
    end

    D & E & V --> POP
    DEC --> PLAN
    PLAN --> MAP & PLOT & JSON
    PLAN --> CTX --> P1 & P2 & P3 --> GEM
    GEM --> OUT[instrucoes_motoristas.md / relatorio_eficiencia.md / respostas]
```

## Camadas (arquitetura limpa)

| Camada | Módulo | Responsabilidade |
|---|---|---|
| Domínio | `medroute.domain` | Entidades (`DeliveryPoint`, `Vehicle`, `Depot`, `Route`, `RoutePlan`), `Priority` e restrições (`check_capacity`, `check_autonomy`, `route_distance`) |
| GA | `medroute.ga` | Cromossomo + decoder (`chromosome.py`), operadores (`operators.py`), fitness (`fitness.py`), loop evolutivo (`engine.py`) |
| Visualização | `medroute.visualization` | `MapRenderer` (Folium → HTML), `plot_fitness_history` (Matplotlib → PNG) |
| LLM | `medroute.llm` | `GeminiClient` (SDK oficial, retry com backoff), `prompts.py` (engenharia de prompt + serialização do plano), `RouteReportGenerator` |
| App | `medroute.cli` | Orquestração: otimizar → artefatos → (opcional) relatórios LLM |
| Dados | `medroute.data` | `build_sample_scenario`: 12 entregas, 3 veículos heterogêneos |

## Fluxo evolutivo (evoluído do `tsp.py` base)

```mermaid
sequenceDiagram
    participant E as GeneticVRPSolver
    participant O as operators
    participant C as decode_chromosome
    participant F as evaluate

    E->>O: generate_random_population(n_entregas, pop)
    loop n_generations
        E->>C: decode(cromossomo, depot, deliveries, vehicles)
        C->>C: split guloso por veículo (capacidade + autonomia)
        E->>F: fitness = dist + prioridade×chegada + unserved + custo fixo
        E->>E: sort + elitismo
        E->>O: seleção → order_crossover → mutate
    end
    E-->>E: melhor RoutePlan
```

## Decisões-chave

- **Cromossomo = permutação de índices de entrega** — preserva os operadores clássicos do código base (OX e mutação de permutação) sem alteração estrutural; a complexidade do VRP fica no **decoder**.
- **Decoder guloso com hard constraints** — varre o cromossomo e atribui cada entrega ao primeiro veículo onde a inserção não viola capacidade nem autonomia; sobras vão para `unserved` (penalizadas no fitness). Garante que toda solução avaliada é operacionalmente viável.
- **Prioridade como soft constraint** — `prioridade × distância de chegada` penaliza entregas críticas tardias sem inviabilizar soluções; `unserved × prioridade` torna medicamento crítico não entregue 10× pior que regular.
- **LLM desacoplada via protocolo `LLMClient`** — `RouteReportGenerator` não depende do Gemini; testes usam `FakeClient`; a chave fica só no `.env`.
