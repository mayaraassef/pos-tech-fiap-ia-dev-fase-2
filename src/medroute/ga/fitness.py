"""Função fitness do VRP: distância + prioridades + restrições.

No TSP base, fitness era apenas a distância do ciclo. Aqui o fitness
penaliza: (1) entregas prioritárias atendidas tarde na rota, (2) entregas
não atendidas por falta de frota, (3) custo fixo por veículo utilizado e
(4) violações residuais de capacidade/autonomia (rede de segurança).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from medroute.domain.constraints import (
    arrival_distance,
    check_autonomy,
    check_capacity,
    route_distance,
)
from medroute.domain.models import DeliveryPoint, Depot, Vehicle
from medroute.ga.chromosome import Chromosome, decode_chromosome

@dataclass(frozen=True)
class FitnessWeights:
    """Pesos dos componentes de custo/penalidade do fitness."""

    distance: float = 1.0
    priority_late: float = 1.0
    unserved_per_priority: float = 10_000.0
    capacity_violation: float = 1e6
    autonomy_violation: float = 1e6

def evaluate(
    chromosome: Chromosome,
    depot: Depot,
    deliveries: Sequence[DeliveryPoint],
    vehicles: Sequence[Vehicle],
    weights: FitnessWeights | None = None,
) -> float:
    """Fitness de um cromossomo (quanto menor, melhor)."""
    w = weights or FitnessWeights()
    plan = decode_chromosome(chromosome, depot, deliveries, vehicles)

    cost = 0.0
    for route in plan.routes:
        cost += w.distance * route_distance(depot, route)
        cost += route.vehicle.fixed_cost
        for idx, point in enumerate(route.stops):
            cost += w.priority_late * point.priority * arrival_distance(
                depot, route, idx
            )
        if not check_capacity(route):
            cost += w.capacity_violation
        if not check_autonomy(depot, route):
            cost += w.autonomy_violation

    for point in plan.unserved:
        cost += w.unserved_per_priority * point.priority

    return cost
