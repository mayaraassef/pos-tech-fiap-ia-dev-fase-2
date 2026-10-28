"""Representação genética e decodificação do cromossomo para o VRP.

No TSP base, o cromossomo era a própria rota (lista de coordenadas).
Aqui o cromossomo é uma permutação de índices de entregas, decodificada
em múltiplas rotas (uma por veículo) por um algoritmo guloso que impõe
as restrições de capacidade e autonomia durante a atribuição. Isso
preserva os operadores clássicos de permutação (OX, troca) do código base.
"""
from __future__ import annotations

from typing import List, Sequence

from medroute.domain.constraints import route_distance
from medroute.domain.models import DeliveryPoint, Depot, Route, RoutePlan, Vehicle

Chromosome = List[int]

def decode_chromosome(
    chromosome: Chromosome,
    depot: Depot,
    deliveries: Sequence[DeliveryPoint],
    vehicles: Sequence[Vehicle],
) -> RoutePlan:
    """Decodifica uma permutação de entregas em rotas por veículo.

    Varre o cromossomo em ordem e tenta inserir cada entrega no veículo
    corrente; se a inserção violar capacidade ou autonomia, a entrega é
    pulada para o próximo veículo. Entregas não alocadas em nenhum
    veículo vão para `RoutePlan.unserved` (penalizadas no fitness).
    """
    pending = list(chromosome)
    routes: List[Route] = []

    for vehicle in vehicles:
        if not pending:
            break
        route = Route(vehicle=vehicle)
        i = 0
        while i < len(pending):
            point = deliveries[pending[i]]
            candidate = Route(vehicle=vehicle, stops=[*route.stops, point])
            if (
                candidate.load <= vehicle.capacity
                and route_distance(depot, candidate) <= vehicle.max_distance
            ):
                route.stops.append(point)
                pending.pop(i)
            else:
                i += 1
        if route.stops:
            routes.append(route)

    unserved = [deliveries[i] for i in pending]
    return RoutePlan(routes=routes, unserved=unserved)
