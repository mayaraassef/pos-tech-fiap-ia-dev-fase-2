"""Cliente LLM — Google Gemini via SDK `google-generativeai`.

A chave da API é lida exclusivamente do ambiente (`.env`), nunca do
código-fonte. O modelo pode ser sobrescrito pela variável GEMINI_MODEL.
"""
from __future__ import annotations

import os
import re
import time
from typing import Protocol

from medroute.config import get_gemini_api_key

DEFAULT_MODEL = "gemini-3.7-flash"

class LLMClient(Protocol):
    """Interface mínima de um cliente de linguagem."""

    def generate(self, prompt: str) -> str:
        """Gera texto a partir de um prompt."""
        ...

class GeminiClient:
    """Wrapper do Gemini implementando `LLMClient`."""

    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        import google.generativeai as genai

        genai.configure(api_key=api_key or get_gemini_api_key())
        self.model_name = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        self._model = genai.GenerativeModel(self.model_name)

    def generate(self, prompt: str, max_retries: int = 4) -> str:
        """Gera texto; tenta de novo com backoff em caso de quota (429)."""
        from google.api_core import exceptions as gexc

        for attempt in range(max_retries + 1):
            try:
                response = self._model.generate_content(prompt)
                break
            except gexc.ResourceExhausted as exc:
                if attempt == max_retries:
                    raise
                delay = self._retry_delay(exc) or 30.0
                time.sleep(delay)
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini não retornou texto para o prompt enviado.")
        return text

    @staticmethod
    def _retry_delay(exc: Exception) -> float | None:
        match = re.search(r"retry in ([\d.]+)s", str(exc))
        return float(match.group(1)) + 1.0 if match else None

def create_default_client() -> GeminiClient:
    """Instancia o cliente padrão; falha se a API key não estiver configurada."""
    return GeminiClient()
