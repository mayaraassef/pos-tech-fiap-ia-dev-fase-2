"""Benchmark: GA-VRP vs. heurística gulosa (nearest neighbor) vs. TSP ingênuo.

Gera os números usados no comparativo do relatório técnico.
Uso: pipenv run python scripts/benchmark.py
"""
from __future__ import annotations

import random
import time

from medroute.data.sample_scenario import build_sample_scenario
from medroute.domain.constraints import plan_metrics, route_distance
from medroute.domain.models import Depot, DeliveryPoint, Route, RoutePlan, Vehicle
from medroute.ga import GAConfig, GeneticVRPSolver
from medroute.ga.fitness import evaluate

def naive_tsp(depot: Depot, deliveries: list[DeliveryPoint]) -> float:
    """TSP clássico: 1 veículo infinito, sequência na ordem dada."""
    route = Route(vehicle=Vehicle(99, 1e9, 1e9), stops=deliveries)
    return route_distance(depot, route)

def greedy_vrp(
    depot: Depot, deliveries: list[DeliveryPoint], vehicles: list[Vehicle]
) -> RoutePlan:
    """Baseline guloso: nearest-neighbor respeitando capacidade/autonomia."""
    pending = list(deliveries)
    routes = []
    for vehicle in vehicles:
        if not pending:
            break
        route = Route(vehicle=vehicle)
        current = depot.coord
        for _ in range(len(pending)):
            best, best_d, best_i = None, float("inf"), None
            for i, p in enumerate(pending):
                cand = Route(vehicle=vehicle, stops=[*route.stops, p])
                if cand.load > vehicle.capacity:
                    continue
                if route_distance(depot, cand) > vehicle.max_distance:
                    continue
                d = ((p.x - current[0]) ** 2 + (p.y - current[1]) ** 2) ** 0.5
                if d < best_d:
                    best, best_d, best_i = p, d, i
            if best is None:
                break
            route.stops.append(best)
            current = best.coord
            pending.pop(best_i)
        if route.stops:
            routes.append(route)
    return RoutePlan(routes=routes, unserved=pending)

def random_search(
    depot, deliveries, vehicles, n_samples=5000, seed=0
) -> float:
    """Baseline: melhor de N permutações aleatórias (sem evolução)."""
    rng = random.Random(seed)
    base = list(range(len(deliveries)))
    best = float("inf")
    for _ in range(n_samples):
        rng.shuffle(base)
        best = min(best, evaluate(base, depot, deliveries, vehicles))
    return best

def main() -> None:
    depot, deliveries, vehicles = build_sample_scenario()

    print("=== BASELINE: TSP ingênuo (1 veículo, sem restrições) ===")
    d = naive_tsp(depot, deliveries)
    naive = Route(vehicle=vehicles[0], stops=deliveries)
    print(f"  distância: {d:.1f} km | carga {naive.load} > cap {vehicles[0].capacity}"
          f" | INVIÁVEL (viola capacidade e autonomia)")

    print("\n=== BASELINE: guloso nearest-neighbor ===")
    plan_g = greedy_vrp(depot, deliveries, vehicles)
    m = plan_metrics(depot, plan_g)
    fit_g = evaluate(
        [deliveries.index(p) for r in plan_g.routes for p in r.stops]
        + [deliveries.index(p) for p in plan_g.unserved],
        depot, deliveries, vehicles,
    )
    print(f"  fitness: {fit_g:.1f} | dist: {m['total_distance']:.1f} km | "
          f"veículos: {m['vehicles_used']} | não atendidas: {m['deliveries_unserved']}")

    print("\n=== BASELINE: amostragem aleatória (5000 permutações) ===")
    t0 = time.time()
    fit_r = random_search(depot, deliveries, vehicles)
    print(f"  melhor fitness: {fit_r:.1f} | tempo: {time.time()-t0:.1f}s")

    print("\n=== GA-VRP (nossa solução) ===")
    for seed in (42, 7, 123):
        t0 = time.time()
        res = GeneticVRPSolver(
            depot, deliveries, vehicles,
            GAConfig(population_size=150, n_generations=400, seed=seed),
        ).solve()
        m = plan_metrics(depot, res.best_plan)
        print(f"  seed {seed}: fitness {res.best_fitness:.1f} | "
              f"dist {m['total_distance']:.1f} km | "
              f"veículos {m['vehicles_used']} | "
              f"não atendidas {m['deliveries_unserved']} | "
              f"{time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
