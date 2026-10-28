"""Entidades de domínio do problema de roteamento médico (VRP).

No código base TSP, os "genes" eram tuplas de coordenadas de cidades.
Aqui, cada gene é o índice de um ponto de entrega, que carrega demanda
(carga) e prioridade — a evolução necessária para o contexto hospitalar.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Tuple

Coordinate = Tuple[float, float]

def distance(a: Coordinate, b: Coordinate) -> float:
    """Distância euclidiana entre dois pontos.

    Evoluída de `calculate_distance` em genetic_algorithm_tsp/genetic_algorithm.py.
    """
    return math.hypot(a[0] - b[0], a[1] - b[1])

class Priority(IntEnum):
    """Prioridade clínica da entrega (peso usado na função fitness)."""

    REGULAR = 1
    HIGH = 3
    CRITICAL = 10

@dataclass(frozen=True)
class DeliveryPoint:
    """Ponto de entrega: unidade hospitalar, clínica ou paciente domiciliar."""

    id: int
    name: str
    x: float
    y: float
    demand: float = 1.0
    priority: Priority = Priority.REGULAR

    @property
    def coord(self) -> Coordinate:
        return (self.x, self.y)

@dataclass(frozen=True)
class Vehicle:
    """Veículo da frota com capacidade de carga e autonomia limitadas."""

    id: int
    capacity: float
    max_distance: float
    fixed_cost: float = 0.0

@dataclass(frozen=True)
class Depot:
    """Centro de distribuição (hospital central) de onde as rotas partem."""

    name: str
    x: float
    y: float

    @property
    def coord(self) -> Coordinate:
        return (self.x, self.y)

@dataclass
class Route:
    """Rota de um único veículo: depósito → paradas → depósito."""

    vehicle: Vehicle
    stops: List[DeliveryPoint] = field(default_factory=list)

    @property
    def load(self) -> float:
        return sum(p.demand for p in self.stops)

@dataclass
class RoutePlan:
    """Solução decodificada do VRP: um conjunto de rotas + não atendidos."""

    routes: List[Route]
    unserved: List[DeliveryPoint] = field(default_factory=list)
