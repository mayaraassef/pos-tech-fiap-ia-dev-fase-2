"""Fase 4 — testes de integração LLM com cliente mock (sem chamar a API)."""
from __future__ import annotations

import os

import pytest

from medroute.data.sample_scenario import build_sample_scenario
from medroute.ga import GAConfig, GeneticVRPSolver
from medroute.llm import (
    RouteReportGenerator,
    build_driver_instructions_prompt,
    build_efficiency_report_prompt,
    build_qa_prompt,
    plan_context,
)

@pytest.fixture(scope="module")
def plan():
    depot, deliveries, vehicles = build_sample_scenario()
    res = GeneticVRPSolver(
        depot, deliveries, vehicles,
        GAConfig(population_size=80, n_generations=120, seed=42),
    ).solve()
    return depot, res.best_plan

class FakeClient:
    """Mock de LLMClient: registra o prompt e devolve resposta fixa."""

    def __init__(self, response: str = "RESPOSTA_LLm") -> None:
        self.response = response
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response

def test_plan_context_serializes_all_routes(plan) -> None:
    depot, best_plan = plan
    ctx = plan_context(depot, best_plan)
    assert depot.name in ctx
    assert "ROTAS:" in ctx
    for route in best_plan.routes:
        assert f"Veículo {route.vehicle.id}" in ctx
        for p in route.stops:
            assert p.name in ctx
            assert p.priority.name in ctx

def test_driver_instructions_prompt_requests_per_vehicle_format(plan) -> None:
    depot, best_plan = plan
    prompt = build_driver_instructions_prompt(depot, best_plan)
    assert "## Veículo" in prompt
    assert "CRITICAL" in prompt
    assert "capacidade" in prompt and "autonomia" in prompt

def test_efficiency_report_prompt_has_required_sections(plan) -> None:
    depot, best_plan = plan
    prompt = build_efficiency_report_prompt(depot, best_plan)
    for section in [
        "Resumo executivo",
        "Desempenho por veículo",
        "Atendimento a prioridades",
        "Economia de recursos",
        "Sugestões de melhoria",
    ]:
        assert section in prompt

def test_qa_prompt_forces_grounding_in_plan_data(plan) -> None:
    depot, best_plan = plan
    prompt = build_qa_prompt(depot, best_plan, "Qual veículo leva mais carga?")
    assert "Qual veículo leva mais carga?" in prompt
    assert "APENAS com base nos dados do plano" in prompt

def test_report_generator_calls_client_and_returns_text(plan) -> None:
    depot, best_plan = plan
    client = FakeClient("instruções geradas")
    gen = RouteReportGenerator(client)

    assert gen.driver_instructions(depot, best_plan) == "instruções geradas"
    assert gen.efficiency_report(depot, best_plan) == "instruções geradas"
    assert gen.improvement_suggestions(depot, best_plan) == "instruções geradas"
    assert (
        gen.answer_question(depot, best_plan, "quantos veículos?")
        == "instruções geradas"
    )
    for prompt in client.prompts:
        assert "PLANO DE ROTAS OTIMIZADO" in prompt

def test_generator_output_saved_to_file(plan, tmp_path) -> None:
    depot, best_plan = plan
    gen = RouteReportGenerator(FakeClient("# Relatório\n\nok"))
    report = gen.efficiency_report(depot, best_plan)
    out = tmp_path / "relatorio.md"
    out.write_text(report, encoding="utf-8")
    assert "# Relatório" in out.read_text(encoding="utf-8")

@pytest.mark.skipif(
    not os.getenv("GEMINI_RUN_LIVE"),
    reason="teste live com a API real só roda com GEMINI_RUN_LIVE=1",
)
def test_gemini_live_driver_instructions(plan) -> None:
    from medroute.llm import create_default_client

    depot, best_plan = plan
    gen = RouteReportGenerator(create_default_client())
    text = gen.driver_instructions(depot, best_plan)
    assert len(text) > 200
    assert "Veículo" in text or "veículo" in text
