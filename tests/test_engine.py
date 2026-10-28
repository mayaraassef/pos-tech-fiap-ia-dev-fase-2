"""Fase 2 — testes de integração do motor evolutivo sobre o cenário exemplo."""
from __future__ import annotations

import pytest

from medroute.data.sample_scenario import build_sample_scenario
from medroute.domain import check_autonomy, check_capacity, plan_metrics
from medroute.ga import GAConfig, GeneticVRPSolver

@pytest.fixture(scope="module")
def result():
    depot, deliveries, vehicles = build_sample_scenario()
    solver = GeneticVRPSolver(
        depot, deliveries, vehicles,
        GAConfig(
            population_size=120,
            n_generations=300,
            mutation_probability=0.3,
            seed=42,
        ),
    )
    return depot, deliveries, vehicles, solver.solve()

def test_solver_serves_all_deliveries(result) -> None:
    depot, deliveries, _, res = result
    served = {p.id for r in res.best_plan.routes for p in r.stops}
    assert served == {p.id for p in deliveries}
    assert res.best_plan.unserved == []

def test_solver_uses_multiple_vehicles(result) -> None:
    _, _, _, res = result
    assert len(res.best_plan.routes) >= 2

def test_routes_respect_all_constraints(result) -> None:
    depot, _, _, res = result
    for route in res.best_plan.routes:
        assert check_capacity(route)
        assert check_autonomy(depot, route)

def test_metrics_show_no_violations(result) -> None:
    depot, _, _, res = result
    metrics = plan_metrics(depot, res.best_plan)
    assert metrics["violations"]["capacity"] == []
    assert metrics["violations"]["autonomy"] == []
    assert metrics["deliveries_unserved"] == 0

def test_fitness_history_is_non_increasing(result) -> None:
    _, _, _, res = result
    hist = res.fitness_history
    assert all(a >= b for a, b in zip(hist, hist[1:]))

def test_solver_is_deterministic_with_seed() -> None:
    depot, deliveries, vehicles = build_sample_scenario()
    cfg = GAConfig(population_size=60, n_generations=60, seed=7)
    r1 = GeneticVRPSolver(depot, deliveries, vehicles, cfg).solve()
    r2 = GeneticVRPSolver(depot, deliveries, vehicles, cfg).solve()
    assert r1.best_fitness == r2.best_fitness
    assert r1.best_chromosome == r2.best_chromosome

def test_ga_fleet_solves_what_single_vehicle_cannot() -> None:
    """O TSP puro (1 veículo) é INVIÁVEL com as restrições reais; o GA da
    frota produz plano viável — essa é a vantagem da evolução para VRP."""
    from medroute.domain.models import Route, Vehicle
    from medroute.domain.constraints import route_distance

    depot, deliveries, vehicles = build_sample_scenario()

    naive = Route(vehicle=vehicles[0], stops=deliveries)
    assert naive.load > vehicles[0].capacity
    assert route_distance(depot, naive) > vehicles[0].max_distance

    solver = GeneticVRPSolver(
        depot, deliveries, vehicles,
        GAConfig(population_size=120, n_generations=300, seed=42),
    )
    res = solver.solve()
    assert res.best_plan.unserved == []
    assert res.fitness_history[-1] <= res.fitness_history[0]
