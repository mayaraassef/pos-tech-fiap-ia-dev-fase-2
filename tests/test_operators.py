"""Fase 2 — testes dos operadores genéticos (OX, mutações, seleções)."""
from __future__ import annotations

import random

from medroute.ga.operators import (
    generate_random_population,
    inversion_mutation,
    mutate,
    order_crossover,
    roulette_selection,
    tournament_selection,
)

def test_population_is_valid_permutations() -> None:
    pop = generate_random_population(8, 20, rng=random.Random(1))
    assert len(pop) == 20
    for ind in pop:
        assert sorted(ind) == list(range(8))

def test_order_crossover_preserves_permutation() -> None:
    rng = random.Random(7)
    p1 = list(range(10))
    p2 = list(reversed(range(10)))
    child = order_crossover(p1, p2, rng)
    assert sorted(child) == list(range(10))
    assert child != p1 or child != p2

def test_ox_same_as_base_code_algorithm() -> None:
    rng = random.Random(0)
    parent1 = [0, 1, 2, 3, 4, 5]
    parent2 = [5, 4, 3, 2, 1, 0]
    child = order_crossover(parent1, parent2, rng)
    assert sorted(child) == parent1

def test_mutate_probability_zero_is_identity() -> None:
    sol = list(range(10))
    assert mutate(sol, 0.0, rng=random.Random(3)) == sol

def test_mutate_probability_one_keeps_permutation() -> None:
    sol = list(range(10))
    out = mutate(sol, 1.0, rng=random.Random(3))
    assert sorted(out) == sol
    assert out != sol

def test_inversion_mutation_keeps_permutation() -> None:
    sol = list(range(10))
    out = inversion_mutation(sol, 1.0, rng=random.Random(5))
    assert sorted(out) == sol
    assert out != sol

def test_roulette_selection_favors_better_fitness() -> None:
    rng = random.Random(42)
    pop = [[0], [1], [2]]
    fitness = [1.0, 10.0, 100.0]
    picks = roulette_selection(pop, fitness, k=1000, rng=rng)
    assert picks.count([0]) > picks.count([1]) > picks.count([2])

def test_tournament_selection_returns_population_members() -> None:
    rng = random.Random(2)
    pop = [[0, 1], [2, 3], [4, 5]]
    fitness = [5.0, 1.0, 9.0]
    chosen = tournament_selection(pop, fitness, k=2, tournament_size=2, rng=rng)
    assert len(chosen) == 2
    assert all(c in pop for c in chosen)
