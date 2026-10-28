"""Fase 2 — testes das entidades de domínio e métricas de rota."""
from __future__ import annotations

import math

from medroute.domain import (
    DeliveryPoint,
    Depot,
    Priority,
    Route,
    Vehicle,
    arrival_distance,
    check_autonomy,
    check_capacity,
    distance,
    route_distance,
)

def _vehicle(capacity=10.0, max_distance=1000.0) -> Vehicle:
    return Vehicle(id=0, capacity=capacity, max_distance=max_distance)

def test_distance_matches_base_tsp_formula() -> None:
    assert distance((0, 0), (3, 4)) == 5.0
    assert math.isclose(distance((1.5, -2), (1.5, 3)), 5.0)

def test_route_distance_is_closed_tour() -> None:
    depot = Depot("CD", 0, 0)
    p = DeliveryPoint(0, "A", 3, 4)
    route = Route(vehicle=_vehicle(), stops=[p])
    assert route_distance(depot, route) == 10.0

def test_route_load_sums_demands() -> None:
    pts = [DeliveryPoint(i, f"P{i}", i, i, demand=2.5) for i in range(4)]
    route = Route(vehicle=_vehicle(), stops=pts)
    assert route.load == 10.0

def test_check_capacity_boundary() -> None:
    pts = [DeliveryPoint(0, "A", 0, 0, demand=10.0)]
    route = Route(vehicle=_vehicle(capacity=10.0), stops=pts)
    assert check_capacity(route)
    route.stops.append(DeliveryPoint(1, "B", 0, 0, demand=0.1))
    assert not check_capacity(route)

def test_check_autonomy_boundary() -> None:
    depot = Depot("CD", 0, 0)
    pts = [DeliveryPoint(0, "A", 0, 500)]
    route = Route(vehicle=_vehicle(max_distance=1000.0), stops=pts)
    assert check_autonomy(depot, route)
    route.stops.append(DeliveryPoint(1, "B", 1, 500))
    assert not check_autonomy(depot, route)

def test_arrival_distance_counts_legs_until_stop() -> None:
    depot = Depot("CD", 0, 0)
    pts = [
        DeliveryPoint(0, "A", 10, 0, priority=Priority.REGULAR),
        DeliveryPoint(1, "B", 10, 10, priority=Priority.CRITICAL),
    ]
    route = Route(vehicle=_vehicle(), stops=pts)
    assert arrival_distance(depot, route, 0) == 10.0
    assert arrival_distance(depot, route, 1) == 20.0
