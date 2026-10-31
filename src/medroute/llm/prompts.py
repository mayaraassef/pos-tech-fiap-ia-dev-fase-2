"""Engenharia de prompts: serializa o plano de rotas do GA em contexto
estruturado e monta prompts especializados para cada saída exigida."""
from __future__ import annotations

from medroute.domain.constraints import plan_metrics, route_distance
from medroute.domain.models import Depot, RoutePlan

_SYSTEM_ROLE = (
    "Você é o assistente de logística do sistema de distribuição de "
    "medicamentos e insumos de um hospital universitário. As rotas foram "
    "otimizadas por um algoritmo genético (VRP) que respeita capacidade "
    "dos veículos, autonomia máxima e prioridade clínica das entregas "
    "(CRITICAL = medicamentos críticos, HIGH = importantes, REGULAR = "
    "insumos regulares). Responda sempre em português brasileiro, de "
    "forma objetiva e operacional."
)

def plan_context(depot: Depot, plan: RoutePlan) -> str:
    """Serializa o plano de rotas em texto compacto para injetar no prompt."""
    metrics = plan_metrics(depot, plan)
    lines = [
        f"DEPÓSITO: {depot.name} (todas as rotas partem e retornam aqui)",
        f"MÉTRICAS: distância total {metrics['total_distance']:.1f} km | "
        f"veículos usados {metrics['vehicles_used']} | "
        f"entregas atendidas {metrics['deliveries_served']} | "
        f"não atendidas {metrics['deliveries_unserved']}",
        "ROTAS:",
    ]
    for route in plan.routes:
        dist = route_distance(depot, route)
        lines.append(
            f"  Veículo {route.vehicle.id} "
            f"(capacidade {route.vehicle.capacity:.0f}, autonomia "
            f"{route.vehicle.max_distance:.0f} km): "
            f"{dist:.1f} km, carga {route.load:.0f}"
        )
        for order, p in enumerate(route.stops, start=1):
            lines.append(
                f"    {order}. {p.name} — prioridade {p.priority.name}, "
                f"demanda {p.demand}"
            )
    if plan.unserved:
        lines.append("NÃO ATENDIDOS: " + ", ".join(p.name for p in plan.unserved))
    return "\n".join(lines)

def build_driver_instructions_prompt(depot: Depot, plan: RoutePlan) -> str:
    return (
        f"{_SYSTEM_ROLE}\n\n"
        f"=== PLANO DE ROTAS OTIMIZADO ===\n{plan_context(depot, plan)}\n\n"
        "TAREFA: gere instruções operacionais detalhadas para o motorista "
        "de CADA veículo, no formato abaixo:\n"
        "## Veículo <id>\n"
        "- Itinerário numerado com o nome de cada parada na ordem exata\n"
        "- Alertas para entregas CRITICAL (manuseio e prazo reforçados)\n"
        "- Observação de carga total vs. capacidade e km vs. autonomia\n"
        "Finalize com um checklist de saída comum a todos os motoristas."
    )

def build_efficiency_report_prompt(
    depot: Depot, plan: RoutePlan, period: str = "diário"
) -> str:
    metrics = plan_metrics(depot, plan)
    return (
        f"{_SYSTEM_ROLE}\n\n"
        f"=== PLANO DE ROTAS OTIMIZADO ===\n{plan_context(depot, plan)}\n\n"
        f"TAREFA: escreva o relatório {period} de eficiência logística em "
        "Markdown, contendo obrigatoriamente as seções:\n"
        "1. **Resumo executivo** — números-chave do dia\n"
        "2. **Desempenho por veículo** — km, carga, nº de entregas\n"
        "3. **Atendimento a prioridades** — cobertura das entregas "
        "CRITICAL/HIGH e impacto clínico\n"
        f"4. **Economia de recursos** — estime ganhos vs. rota ingênua "
        f"(todas as entregas com 1 único veículo = ~{metrics['total_distance']*1.3:.0f} km)\n"
        "5. **Sugestões de melhoria** — ao menos 2 recomendações "
        "operacionais baseadas nos padrões das rotas"
    )

def build_qa_prompt(depot: Depot, plan: RoutePlan, question: str) -> str:
    return (
        f"{_SYSTEM_ROLE}\n\n"
        f"=== PLANO DE ROTAS OTIMIZADO ===\n{plan_context(depot, plan)}\n\n"
        f"PERGUNTA DO USUÁRIO: {question}\n\n"
        "Responda APENAS com base nos dados do plano acima. Se a resposta "
        "não estiver nos dados, diga explicitamente que a informação não "
        "consta no plano de rotas atual."
    )
