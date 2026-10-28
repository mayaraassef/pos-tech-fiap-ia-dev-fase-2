"""Cenário de exemplo: distribuição de medicamentos/insumos de um hospital
central para unidades de saúde e pacientes domiciliares."""
from __future__ import annotations

from medroute.domain.models import DeliveryPoint, Depot, Priority, Vehicle

def build_sample_scenario() -> tuple[Depot, list[DeliveryPoint], list[Vehicle]]:
    """Cenário determinístico com 12 entregas e 3 veículos heterogêneos."""
    depot = Depot(name="Hospital Central (CD)", x=500.0, y=200.0)

    deliveries = [
        DeliveryPoint(0, "UPA Norte", 470, 169, demand=3, priority=Priority.CRITICAL),
        DeliveryPoint(1, "Clínica Leste", 602, 202, demand=2, priority=Priority.HIGH),
        DeliveryPoint(2, "UBS Jardins", 754, 239, demand=4, priority=Priority.REGULAR),
        DeliveryPoint(3, "Paciente domiciliar A", 476, 233, demand=1, priority=Priority.CRITICAL),
        DeliveryPoint(4, "Paciente domiciliar B", 468, 301, demand=2, priority=Priority.HIGH),
        DeliveryPoint(5, "Hospital Municipal", 522, 29, demand=5, priority=Priority.CRITICAL),
        DeliveryPoint(6, "UBS Vila Nova", 597, 171, demand=3, priority=Priority.REGULAR),
        DeliveryPoint(7, "Clínica Sul", 487, 325, demand=2, priority=Priority.REGULAR),
        DeliveryPoint(8, "Farmácia Popular", 746, 232, demand=4, priority=Priority.HIGH),
        DeliveryPoint(9, "Paciente domiciliar C", 558, 136, demand=1, priority=Priority.CRITICAL),
        DeliveryPoint(10, "UPA Oeste", 512, 317, demand=3, priority=Priority.REGULAR),
        DeliveryPoint(11, "Laboratório Central", 589, 381, demand=2, priority=Priority.HIGH),
    ]

    vehicles = [
        Vehicle(id=0, capacity=15.0, max_distance=1200.0, fixed_cost=50.0),
        Vehicle(id=1, capacity=15.0, max_distance=1200.0, fixed_cost=50.0),
        Vehicle(id=2, capacity=18.0, max_distance=1500.0, fixed_cost=80.0),
    ]
    return depot, deliveries, vehicles
