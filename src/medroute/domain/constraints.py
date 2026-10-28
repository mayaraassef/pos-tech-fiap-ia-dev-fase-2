"""Restrições operacionais do VRP e métricas de avaliação das rotas."""
from __future__ import annotations

from medroute.domain.models import Depot, Route, RoutePlan, distance

_EPS = 1e-9

def route_distance(depot: Depot, route: Route) -> float:
    """Distância total da rota fechada: depósito → paradas → depósito.

    Equivalente ao `calculate_fitness` do código base, mas a rota é uma
    lista de DeliveryPoint em vez de coordenadas de cidades.
    """
    points = [depot.coord] + [p.coord for p in route.stops] + [depot.coord]
    return sum(distance(a, b) for a, b in zip(points, points[1:]))

def check_capacity(route: Route) -> bool:
    """Carga total transportada não pode exceder a capacidade do veículo."""
    return route.load <= route.vehicle.capacity + _EPS

def check_autonomy(depot: Depot, route: Route) -> bool:
    """Distância total percorrida não pode exceder a autonomia do veículo."""
    return route_distance(depot, route) <= route.vehicle.max_distance + _EPS

def arrival_distance(depot: Depot, route: Route, stop_index: int) -> float:
    """Distância percorrida desde o depósito até a parada `stop_index`.

    Usada pelo fitness para penalizar entregas prioritárias atendidas tarde.
    """
    points = [depot.coord] + [p.coord for p in route.stops[: stop_index + 1]]
    return sum(distance(a, b) for a, b in zip(points, points[1:]))

def plan_metrics(depot: Depot, plan: RoutePlan) -> dict:
    """Consolida métricas e violações do plano de rotas."""
    total_distance = sum(route_distance(depot, r) for r in plan.routes)
    violations = {
        "capacity": [r.vehicle.id for r in plan.routes if not check_capacity(r)],
        "autonomy": [r.vehicle.id for r in plan.routes if not check_autonomy(depot, r)],
    }
    critical_late = [
        p
        for r in plan.routes
        for i, p in enumerate(r.stops)
        if p.priority.name == "CRITICAL" and i > len(r.stops) // 2
    ]
    return {
        "total_distance": total_distance,
        "vehicles_used": len(plan.routes),
        "deliveries_served": sum(len(r.stops) for r in plan.routes),
        "deliveries_unserved": len(plan.unserved),
        "violations": violations,
        "critical_in_second_half": len(critical_late),
    }
