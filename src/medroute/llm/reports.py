"""Geração de instruções, relatórios e respostas via LLM.

Cada método injeta o contexto estruturado do plano de rotas (saída do
algoritmo genético) em um prompt especializado e delega a geração ao
cliente LLM configurado (Gemini por padrão; qualquer `LLMClient` serve).
"""
from __future__ import annotations

from medroute.domain.models import Depot, RoutePlan
from medroute.llm.client import LLMClient
from medroute.llm.prompts import (
    build_driver_instructions_prompt,
    build_efficiency_report_prompt,
    build_qa_prompt,
)

class RouteReportGenerator:
    """Interface de alto nível entre a saída do GA e a LLM."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def driver_instructions(self, depot: Depot, plan: RoutePlan) -> str:
        """Instruções detalhadas por veículo para motoristas/equipes."""
        return self._client.generate(
            build_driver_instructions_prompt(depot, plan)
        )

    def efficiency_report(
        self, depot: Depot, plan: RoutePlan, period: str = "diário"
    ) -> str:
        """Relatório de eficiência: km, carga, prioridades e economia."""
        return self._client.generate(
            build_efficiency_report_prompt(depot, plan, period)
        )

    def improvement_suggestions(self, depot: Depot, plan: RoutePlan) -> str:
        """Extrai só a seção de sugestões do relatório de eficiência."""
        prompt = build_efficiency_report_prompt(depot, plan, "semanal")
        prompt += (
            "\n\nATENÇÃO: retorne APENAS a seção 5 (Sugestões de melhoria), "
            "em lista numerada."
        )
        return self._client.generate(prompt)

    def answer_question(
        self, depot: Depot, plan: RoutePlan, question: str
    ) -> str:
        """Responde perguntas em linguagem natural sobre o plano atual."""
        return self._client.generate(build_qa_prompt(depot, plan, question))
