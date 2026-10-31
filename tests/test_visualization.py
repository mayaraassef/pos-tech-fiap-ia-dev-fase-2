"""Fase 3 — teste do renderizador: mapa HTML e gráfico de convergência."""
from __future__ import annotations

from medroute.data.sample_scenario import build_sample_scenario
from medroute.ga import GAConfig, GeneticVRPSolver
from medroute.visualization import MapRenderer, plot_fitness_history

def _plan():
    depot, deliveries, vehicles = build_sample_scenario()
    res = GeneticVRPSolver(
        depot, deliveries, vehicles,
        GAConfig(population_size=60, n_generations=80, seed=42),
    ).solve()
    return depot, res

def test_map_renderer_generates_html(tmp_path) -> None:
    depot, res = _plan()
    out = MapRenderer().render(depot, res.best_plan, tmp_path / "mapa.html")
    assert out.exists()
    html = out.read_text(encoding="utf-8")
    assert "Hospital Central" in html
    assert "L.polyline" in html or "polyline" in html
    assert "UPA Norte" in html

def test_map_renderer_marks_unserved(tmp_path) -> None:
    from medroute.domain.models import RoutePlan

    depot, deliveries, _vehicles = build_sample_scenario()
    plan = RoutePlan(routes=[], unserved=[deliveries[0]])
    out = MapRenderer().render(depot, plan, tmp_path / "m2.html")
    assert "NÃO ATENDIDO" in out.read_text(encoding="utf-8")

def test_fitness_plot_generates_png(tmp_path) -> None:
    _, res = _plan()
    out = plot_fitness_history(res.fitness_history, tmp_path / "conv.png")
    assert out.exists()
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

def test_cli_run_optimization_generates_artifacts(tmp_path) -> None:
    from medroute.cli import run_optimization

    summary = run_optimization(output_dir=tmp_path)
    assert (tmp_path / "rotas_otimizadas.html").exists()
    assert (tmp_path / "convergencia_fitness.png").exists()
    assert (tmp_path / "resumo_otimizacao.json").exists()
    assert summary["metrics"]["deliveries_unserved"] == 0
    assert len(summary["routes"]) >= 2
