"""Operadores genéticos especializados para o problema de roteamento.

Evoluídos de genetic_algorithm_tsp/genetic_algorithm.py, que operava
sobre permutações de coordenadas. Aqui operam sobre permutações de
índices de entregas — os algoritmos são preservados (OX, swap) e
generalizados com um gerador `rng` injetável para reprodutibilidade.
"""
from __future__ import annotations

import random
from typing import List, Sequence

from medroute.ga.chromosome import Chromosome

_Rng = random.Random

def _rng(rng: _Rng | None) -> _Rng | random.Random:
    return rng if rng is not None else random

def generate_random_population(
    n_deliveries: int, population_size: int, rng: _Rng | None = None
) -> List[Chromosome]:
    """População inicial: permutações aleatórias dos índices de entrega.

    Evoluída de `generate_random_population` do código base (que recebia
    a lista de cidades; aqui recebe apenas a quantidade de entregas).
    """
    r = _rng(rng)
    base = list(range(n_deliveries))
    population = []
    for _ in range(population_size):
        individual = base[:]
        r.shuffle(individual)
        population.append(individual)
    return population

def order_crossover(
    parent1: Chromosome, parent2: Chromosome, rng: _Rng | None = None
) -> Chromosome:
    """Order Crossover (OX) — mesmo algoritmo do código base.

    Mantém um segmento contíguo de parent1 e preenche o restante na
    ordem em que aparecem em parent2, produzindo permutação válida.
    """
    r = _rng(rng)
    length = len(parent1)
    start_index = r.randint(0, length - 1)
    end_index = r.randint(start_index + 1, length)

    child = parent1[start_index:end_index]

    remaining_positions = [i for i in range(length) if i < start_index or i >= end_index]
    remaining_genes = [gene for gene in parent2 if gene not in child]

    for position, gene in zip(remaining_positions, remaining_genes):
        child.insert(position, gene)

    return child

def mutate(
    solution: Chromosome,
    mutation_probability: float,
    rng: _Rng | None = None,
) -> Chromosome:
    """Mutação por troca de posições — generalização da do código base.

    O base trocava apenas pares adjacentes; aqui dois índices quaisquer
    podem ser trocados, aumentando a exploração sem perder a validade
    da permutação.
    """
    r = _rng(rng)
    mutated = list(solution)
    if r.random() < mutation_probability and len(mutated) >= 2:
        i, j = r.sample(range(len(mutated)), 2)
        mutated[i], mutated[j] = mutated[j], mutated[i]
    return mutated

def inversion_mutation(
    solution: Chromosome,
    mutation_probability: float,
    rng: _Rng | None = None,
) -> Chromosome:
    """Mutação por inversão de segmento (operador alternativo, clássico em TSP)."""
    r = _rng(rng)
    mutated = list(solution)
    if r.random() < mutation_probability and len(mutated) >= 2:
        i, j = sorted(r.sample(range(len(mutated)), 2))
        mutated[i : j + 1] = reversed(mutated[i : j + 1])
    return mutated

def roulette_selection(
    population: Sequence[Chromosome],
    fitness: Sequence[float],
    k: int = 2,
    rng: _Rng | None = None,
) -> List[Chromosome]:
    """Seleção por roleta com peso 1/fitness — como no loop de `tsp.py` base."""
    r = _rng(rng)
    weights = [1.0 / f if f > 0 else 1.0 for f in fitness]
    return r.choices(population, weights=weights, k=k)

def tournament_selection(
    population: Sequence[Chromosome],
    fitness: Sequence[float],
    k: int = 2,
    tournament_size: int = 3,
    rng: _Rng | None = None,
) -> List[Chromosome]:
    """Seleção por torneio: sorteia `tournament_size` e fica com o melhor."""
    r = _rng(rng)
    selected = []
    for _ in range(k):
        aspirants = r.sample(range(len(population)), min(tournament_size, len(population)))
        winner = min(aspirants, key=lambda i: fitness[i])
        selected.append(population[winner])
    return selected
