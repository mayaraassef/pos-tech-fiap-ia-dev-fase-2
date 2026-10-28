"""Motor evolutivo: loop do algoritmo genético para o VRP.

Estrutura preservada do loop de `tsp.py`/`genetic_algorithm.py` base:
população inicial → fitness → ordenação → elitismo → seleção → crossover
→ mutação → próxima geração.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Sequence

from medroute.domain.models import DeliveryPoint, Depot, RoutePlan, Vehicle
from medroute.ga.chromosome import Chromosome, decode_chromosome
from medroute.ga.fitness import FitnessWeights, evaluate
from medroute.ga.operators import (
    generate_random_population,
    inversion_mutation,
    mutate,
    order_crossover,
    roulette_selection,
    tournament_selection,
)

@dataclass(frozen=True)
class GAConfig:
    """Hiperparâmetros do algoritmo genético."""

    population_size: int = 100
    n_generations: int = 200
    mutation_probability: float = 0.3
    elitism_count: int = 1
    selection: str = "roulette"
    tournament_size: int = 3
    mutation: str = "swap"
    seed: int | None = None
    fitness_weights: FitnessWeights = field(default_factory=FitnessWeights)

@dataclass
class GAResult:
    """Resultado da execução do GA."""

    best_plan: RoutePlan
    best_chromosome: Chromosome
    best_fitness: float
    fitness_history: List[float]

class GeneticVRPSolver:
    """Solver de VRP via algoritmo genético."""

    def __init__(
        self,
        depot: Depot,
        deliveries: Sequence[DeliveryPoint],
        vehicles: Sequence[Vehicle],
        config: GAConfig | None = None,
    ) -> None:
        self.depot = depot
        self.deliveries = list(deliveries)
        self.vehicles = list(vehicles)
        self.config = config or GAConfig()

    def _evaluate(self, chromosome: Chromosome) -> float:
        return evaluate(
            chromosome,
            self.depot,
            self.deliveries,
            self.vehicles,
            self.config.fitness_weights,
        )

    def _select(
        self, population: List[Chromosome], fitness: List[float], rng: random.Random
    ) -> List[Chromosome]:
        if self.config.selection == "tournament":
            return tournament_selection(
                population, fitness, k=2,
                tournament_size=self.config.tournament_size, rng=rng,
            )
        return roulette_selection(population, fitness, k=2, rng=rng)

    def _mutate(self, individual: Chromosome, rng: random.Random) -> Chromosome:
        p = self.config.mutation_probability
        if self.config.mutation == "inversion":
            return inversion_mutation(individual, p, rng)
        return mutate(individual, p, rng)

    def solve(self) -> GAResult:
        """Executa o loop evolutivo e retorna o melhor plano de rotas."""
        cfg = self.config
        rng = random.Random(cfg.seed)

        population = generate_random_population(
            len(self.deliveries), cfg.population_size, rng
        )

        best_chromosome: Chromosome = population[0]
        best_fitness = float("inf")
        fitness_history: List[float] = []

        for _generation in range(cfg.n_generations):
            pop_fitness = [self._evaluate(ind) for ind in population]

            order = sorted(range(len(population)), key=lambda i: pop_fitness[i])
            population = [population[i] for i in order]
            pop_fitness = [pop_fitness[i] for i in order]

            if pop_fitness[0] < best_fitness:
                best_fitness = pop_fitness[0]
                best_chromosome = list(population[0])
            fitness_history.append(best_fitness)

            new_population = [list(ind) for ind in population[: cfg.elitism_count]]

            while len(new_population) < cfg.population_size:
                parent1, parent2 = self._select(population, pop_fitness, rng)
                child = order_crossover(parent1, parent2, rng)
                child = self._mutate(child, rng)
                new_population.append(child)

            population = new_population

        best_plan = decode_chromosome(
            best_chromosome, self.depot, self.deliveries, self.vehicles
        )
        return GAResult(
            best_plan=best_plan,
            best_chromosome=best_chromosome,
            best_fitness=best_fitness,
            fitness_history=fitness_history,
        )
