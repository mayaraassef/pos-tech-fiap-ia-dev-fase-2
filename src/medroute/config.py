"""Configuração da aplicação.

Carrega variáveis de ambiente a partir do arquivo `.env` na raiz do
projeto. A chave da API do Gemini é lida exclusivamente do ambiente —
nunca deve constar no código-fonte.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
OUTPUT_DIR = PROJECT_ROOT / "output"

load_dotenv(ENV_PATH)

def get_gemini_api_key() -> str:
    """Retorna a chave da API do Gemini configurada no ambiente.

    Raises:
        RuntimeError: se a variável GEMINI_API_KEY não estiver definida.
    """
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY não configurada. Copie `.env.example` para `.env` "
            "na raiz do projeto e preencha com sua chave."
        )
    return key

def ensure_output_dir() -> Path:
    """Garante a existência do diretório de artefatos gerados."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR
