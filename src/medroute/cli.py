"""Ponto de entrada: executa a otimização e gera os artefatos de saída.

Uso:
    pipenv run python -m medroute.cli                 # otimiza + mapa + gráfico
    pipenv run python -m medroute.cli --llm           # idem + instruções e relatório via Gemini
    pipenv run python -m medroute.cli --ask "pergunta"  # Q&A sobre o plano otimizado
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from medroute.config import ensure_output_dir
from medroute.data.sample_scenario import build_sample_scenario
from medroute.domain.constraints import plan_metrics, route_distance
from medroute.ga import GAConfig, GeneticVRPSolver
from medroute.visualization import MapRenderer, plot_fitness_history

def run_optimization(output_dir: Path | None = None) -> dict:
    """Resolve o cenário exemplo e grava mapa, gráfico e resumo JSON."""
    out = output_dir or ensure_output_dir()

    depot, deliveries, vehicles = build_sample_scenario()
    solver = GeneticVRPSolver(
        depot,
        deliveries,
        vehicles,
        GAConfig(population_size=150, n_generations=400, seed=42),
    )
    result = solver.solve()
    metrics = plan_metrics(depot, result.best_plan)

    map_path = MapRenderer().render(
        depot, result.best_plan, out / "rotas_otimizadas.html"
    )
    plot_path = plot_fitness_history(
        result.fitness_history, out / "convergencia_fitness.png"
    )

    summary = {
        "best_fitness": result.best_fitness,
        "metrics": metrics,
        "routes": [
            {
                "vehicle_id": r.vehicle.id,
                "distance": route_distance(depot, r),
                "load": r.load,
                "stops": [p.name for p in r.stops],
            }
            for r in result.best_plan.routes
        ],
        "artifacts": {"map": str(map_path), "plot": str(plot_path)},
        "_objects": {"depot": depot, "plan": result.best_plan},
    }
    (out / "resumo_otimizacao.json").write_text(
        json.dumps({k: v for k, v in summary.items() if k != "_objects"},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return summary

def _llm_outputs(summary: dict, out: Path, question: str | None) -> None:
    from medroute.llm import RouteReportGenerator, create_default_client

    depot = summary["_objects"]["depot"]
    plan = summary["_objects"]["plan"]
    gen = RouteReportGenerator(create_default_client())

    instructions = gen.driver_instructions(depot, plan)
    (out / "instrucoes_motoristas.md").write_text(instructions, encoding="utf-8")
    print(f"Instruções dos motoristas: {out / 'instrucoes_motoristas.md'}")

    report = gen.efficiency_report(depot, plan)
    (out / "relatorio_eficiencia.md").write_text(report, encoding="utf-8")
    print(f"Relatório de eficiência: {out / 'relatorio_eficiencia.md'}")

    if question:
        print("\nPergunta:", question)
        print("Resposta:", gen.answer_question(depot, plan, question))

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llm", action="store_true",
                        help="gera instruções e relatório via Gemini")
    parser.add_argument("--ask", metavar="PERGUNTA",
                        help="pergunta em linguagem natural sobre o plano")
    args = parser.parse_args()

    out = ensure_output_dir()
    summary = run_optimization(out)
    print(f"Melhor fitness: {summary['best_fitness']:.2f}")
    print(f"Veículos usados: {summary['metrics']['vehicles_used']}")
    print(f"Distância total: {summary['metrics']['total_distance']:.2f}")
    for r in summary["routes"]:
        print(f"  V{r['vehicle_id']}: {r['distance']:.1f} km - {' -> '.join(r['stops'])}")
    print(f"Mapa: {summary['artifacts']['map']}")
    print(f"Gráfico: {summary['artifacts']['plot']}")

    if args.llm or args.ask:
        _llm_outputs(summary, out, args.ask)

if __name__ == "__main__":
    main()
