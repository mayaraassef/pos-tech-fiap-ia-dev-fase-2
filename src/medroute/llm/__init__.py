"""Pacote llm do medroute — integração com Google Gemini."""
from medroute.llm.client import GeminiClient, LLMClient, create_default_client
from medroute.llm.prompts import (
    build_driver_instructions_prompt,
    build_efficiency_report_prompt,
    build_qa_prompt,
    plan_context,
)
from medroute.llm.reports import RouteReportGenerator

__all__ = [
    "LLMClient",
    "GeminiClient",
    "create_default_client",
    "RouteReportGenerator",
    "plan_context",
    "build_driver_instructions_prompt",
    "build_efficiency_report_prompt",
    "build_qa_prompt",
]
