"""Fase 2 — testes do decodificador: capacidade, autonomia, cobertura."""
from __future__ import annotations

from medroute.domain import (
    DeliveryPoint,
    Depot,
    Priority,
    Vehicle,
    check_autonomy,
    check_capacity,
    route_distance,
)
from medroute.ga.chromosome import decode_chromosome

DEPOT = Depot("CD", 0, 0)

def _p(i, x, y, demand=1.0, priority=Priority.REGULAR):
    return DeliveryPoint(i, f"P{i}", x, y, demand=demand, priority=priority)

def test_decode_never_loses_or_duplicates_genes() -> None:
    deliveries = [_p(i, i * 10, 0) for i in range(6)]
    vehicles = [Vehicle(0, capacity=3, max_distance=10_000)]
    chromosome = [3, 0, 5, 1, 4, 2]
    plan = decode_chromosome(chromosome, DEPOT, deliveries, vehicles)
    served = [p.id for r in plan.routes for p in r.stops]
    assert sorted(served + [p.id for p in plan.unserved]) == sorted(chromosome)
    assert len(served) == len(set(served))

def test_decode_enforces_capacity_split_across_vehicles() -> None:
    deliveries = [_p(i, i + 1, 0, demand=2.0) for i in range(4)]
    vehicles = [Vehicle(0, capacity=5, max_distance=10_000),
                Vehicle(1, capacity=5, max_distance=10_000)]
    plan = decode_chromosome([0, 1, 2, 3], DEPOT, deliveries, vehicles)
    assert len(plan.routes) == 2
    assert all(check_capacity(r) for r in plan.routes)
    assert all(len(r.stops) <= 2 for r in plan.routes)
    assert plan.unserved == []

def test_decode_enforces_max_distance() -> None:
    deliveries = [_p(0, 50, 0), _p(1, -50, 0)]
    vehicles = [Vehicle(0, capacity=99, max_distance=101.0),
                Vehicle(1, capacity=99, max_distance=101.0)]
    plan = decode_chromosome([0, 1], DEPOT, deliveries, vehicles)
    assert all(check_autonomy(DEPOT, r) for r in plan.routes)
    assert all(len(r.stops) == 1 for r in plan.routes)

def test_decode_marks_unserved_when_fleet_insufficient() -> None:
    deliveries = [_p(i, i + 1, 0, demand=2.0) for i in range(4)]
    one_vehicle = [Vehicle(0, capacity=5, max_distance=10_000)]
    plan = decode_chromosome([0, 1, 2, 3], DEPOT, deliveries, one_vehicle)
    assert len(plan.routes) == 1
    assert len(plan.unserved) == 2
    assert check_capacity(plan.routes[0])

def test_decode_empty_chromosome_yields_no_routes() -> None:
    plan = decode_chromosome([], DEPOT, [], [Vehicle(0, 10, 100)])
    assert plan.routes == []
    assert plan.unserved == []

def test_decode_skips_infeasible_but_keeps_scanning() -> None:
    deliveries = [_p(0, 1, 0, demand=9.0), _p(1, 2, 0, demand=1.0)]
    vehicles = [Vehicle(0, capacity=5, max_distance=10_000)]
    plan = decode_chromosome([0, 1], DEPOT, deliveries, vehicles)
    assert [p.id for p in plan.routes[0].stops] == [1]
    assert [p.id for p in plan.unserved] == [0]

def test_route_distance_used_by_decoder_matches_domain() -> None:
    deliveries = [_p(0, 30, 40)]
    vehicles = [Vehicle(0, capacity=10, max_distance=10_000)]
    plan = decode_chromosome([0], DEPOT, deliveries, vehicles)
    assert route_distance(DEPOT, plan.routes[0]) == 100.0
