"""Renderização das rotas otimizadas em mapa interativo (Folium/HTML).

As coordenadas do problema são cartesianas abstratas (x, y); o renderer
projeta-as sobre coordenadas geográficas reais via transformação afim
ancorada em uma origem configurável (default: centro de São Paulo),
permitindo visualizar as rotas sobre tiles OpenStreetMap.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence, Tuple

import folium

from medroute.domain.constraints import route_distance
from medroute.domain.models import Depot, Priority, RoutePlan

_PRIORITY_COLOR = {
    Priority.CRITICAL: "red",
    Priority.HIGH: "orange",
    Priority.REGULAR: "green",
}

_ROUTE_COLORS = ["blue", "purple", "cadetblue", "darkgreen", "darkred", "black"]

class MapRenderer:
    """Gera mapa HTML com depósito, entregas (por prioridade) e rotas."""

    def __init__(
        self,
        origin: Tuple[float, float] = (-23.5505, -46.6333),
        meters_per_unit: float = 10.0,
    ) -> None:
        self.origin_lat, self.origin_lon = origin
        self._deg_per_unit = meters_per_unit / 111_320.0

    def to_geo(self, x: float, y: float) -> Tuple[float, float]:
        return (
            self.origin_lat + y * self._deg_per_unit,
            self.origin_lon + x * self._deg_per_unit,
        )

    def render(
        self,
        depot: Depot,
        plan: RoutePlan,
        output_path: str | Path,
        title: str = "Rotas Otimizadas — Distribuição de Medicamentos",
    ) -> Path:
        """Renderiza o plano de rotas e salva como arquivo HTML."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        center = self.to_geo(depot.x, depot.y)
        fmap = folium.Map(location=center, zoom_start=11, tiles=None)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            attr="Esri — Sources: Esri, HERE, Garmin, USGS",
            name="Esri World Street Map",
        ).add_to(fmap)
        folium.TileLayer(
            "OpenStreetMap", name="OpenStreetMap", show=False
        ).add_to(fmap)

        folium.Marker(
            location=self.to_geo(depot.x, depot.y),
            popup=f"<b>{depot.name}</b><br>Centro de distribuição",
            tooltip=depot.name,
            icon=folium.Icon(color="darkred", icon="plus-sign", prefix="glyphicon"),
        ).add_to(fmap)

        for v_idx, route in enumerate(plan.routes):
            color = _ROUTE_COLORS[v_idx % len(_ROUTE_COLORS)]
            dist = route_distance(depot, route)
            group = folium.FeatureGroup(
                name=f"Veículo {route.vehicle.id} — {dist:.1f} km, "
                f"carga {route.load:.0f}/{route.vehicle.capacity:.0f}"
            )
            group.add_to(fmap)

            coords = [self.to_geo(depot.x, depot.y)]
            for order, point in enumerate(route.stops, start=1):
                geo = self.to_geo(point.x, point.y)
                coords.append(geo)
                folium.Marker(
                    location=geo,
                    popup=(
                        f"<b>{point.name}</b><br>"
                        f"Veículo {route.vehicle.id} · Parada #{order}<br>"
                        f"Prioridade: {point.priority.name}<br>"
                        f"Demanda: {point.demand}"
                    ),
                    tooltip=f"{point.name} (v{route.vehicle.id} #{order})",
                    icon=folium.Icon(
                        color=_PRIORITY_COLOR[point.priority],
                        icon="flag" if point.priority == Priority.CRITICAL else "info-sign",
                    ),
                ).add_to(group)
            coords.append(self.to_geo(depot.x, depot.y))
            folium.PolyLine(coords, color=color, weight=4, opacity=0.8).add_to(group)

        for point in plan.unserved:
            folium.Marker(
                location=self.to_geo(point.x, point.y),
                popup=f"<b>{point.name}</b><br>NÃO ATENDIDO",
                tooltip=f"{point.name} — NÃO ATENDIDO",
                icon=folium.Icon(color="gray", icon="exclamation-sign"),
            ).add_to(fmap)

        folium.LayerControl().add_to(fmap)
        fmap.get_root().html.add_child(
            folium.Element(f"<h3 style='text-align:center'>{title}</h3>")
        )
        fmap.save(str(output_path))
        return output_path
