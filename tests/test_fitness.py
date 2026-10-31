"""Fase 2 — testes da função fitness: distância, prioridade, penalidades."""
from __future__ import annotations

from medroute.domain import DeliveryPoint, Depot, Priority, Vehicle, route_distance
from medroute.domain.models import Route
from medroute.ga.chromosome import decode_chromosome
from medroute.ga.fitness import FitnessWeights, evaluate

DEPOT = Depot("CD", 0, 0)

def _scenario():
    deliveries = [
        DeliveryPoint(0, "crit", 10, 0, demand=1, priority=Priority.CRITICAL),
        DeliveryPoint(1, "reg1", 50, 0, demand=1, priority=Priority.REGULAR),
        DeliveryPoint(2, "reg2", 100, 0, demand=1, priority=Priority.REGULAR),
    ]
    vehicles = [Vehicle(0, capacity=10, max_distance=10_000)]
    return deliveries, vehicles

def test_fitness_equals_distance_when_no_priority_weight() -> None:
    deliveries, vehicles = _scenario()
    w = FitnessWeights(priority_late=0.0)
    chromosome = [0, 1, 2]
    expected = route_distance(
        DEPOT,
        Route(vehicle=vehicles[0], stops=[deliveries[0], deliveries[1], deliveries[2]]),
    )
    assert evaluate(chromosome, DEPOT, deliveries, vehicles, w) == expected

def test_critical_first_beats_critical_last() -> None:
    deliveries, vehicles = _scenario()
    w = FitnessWeights(priority_late=1.0)
    f_early = evaluate([0, 2, 1], DEPOT, deliveries, vehicles, w)
    f_late = evaluate([1, 2, 0], DEPOT, deliveries, vehicles, w)
    assert f_early < f_late

def test_unserved_deliveries_are_heavily_penalized() -> None:
    deliveries, _ = _scenario()
    w = FitnessWeights()
    fleet_ok = [Vehicle(0, capacity=10, max_distance=10_000)]
    fleet_weak = [Vehicle(0, capacity=1, max_distance=10_000)]
    f_ok = evaluate([0, 1, 2], DEPOT, deliveries, fleet_ok, w)
    f_weak = evaluate([0, 1, 2], DEPOT, deliveries, fleet_weak, w)
    assert f_weak > f_ok

def test_unserved_critical_costs_more_than_regular() -> None:
    deliveries = [
        DeliveryPoint(0, "crit", 10, 0, demand=9, priority=Priority.CRITICAL),
        DeliveryPoint(1, "reg", 20, 0, demand=9, priority=Priority.REGULAR),
        DeliveryPoint(2, "ok", 30, 0, demand=1, priority=Priority.REGULAR),
    ]
    vehicles = [Vehicle(0, capacity=1, max_distance=10_000)]
    w = FitnessWeights()
    f_crit_out = evaluate([0, 2], DEPOT, deliveries, vehicles, w)
    f_reg_out = evaluate([1, 2], DEPOT, deliveries, vehicles, w)
    assert f_crit_out > f_reg_out

def test_fixed_cost_discourages_extra_vehicles() -> None:
    deliveries, _ = _scenario()
    cheap = [Vehicle(0, capacity=10, max_distance=10_000)]
    expensive = [Vehicle(0, capacity=10, max_distance=10_000, fixed_cost=1000)]
    w = FitnessWeights(priority_late=0.0)
    f_cheap = evaluate([0, 1, 2], DEPOT, deliveries, cheap, w)
    f_exp = evaluate([0, 1, 2], DEPOT, deliveries, expensive, w)
    assert f_exp == f_cheap + 1000

def test_evaluate_never_returns_infeasible_plan_cost() -> None:
    deliveries = [DeliveryPoint(i, f"P{i}", i, 0, demand=1) for i in range(3)]
    vehicles = [Vehicle(0, capacity=10, max_distance=10_000)]
    f = evaluate([0, 1, 2], DEPOT, deliveries, vehicles, FitnessWeights())
    assert f < 1e6
