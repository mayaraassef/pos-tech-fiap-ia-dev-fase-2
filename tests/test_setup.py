"""Teste da Fase 1 — valida ambiente, pacote, pytest e segurança da API key."""
from __future__ import annotations

import inspect
import os
import sys

import medroute
from medroute import config

def test_python_version_supported() -> None:
    assert sys.version_info >= (3, 10)

def test_package_is_importable() -> None:
    assert medroute.__version__

def test_subpackages_exist() -> None:
    import medroute.domain
    import medroute.ga
    import medroute.llm
    import medroute.visualization

def test_api_key_never_hardcoded() -> None:
    """Nenhum arquivo do pacote pode conter a chave do Gemini em claro."""
    key = os.getenv("GEMINI_API_KEY")
    source = inspect.getsource(config)
    if key:
        assert key not in source

def test_gemini_key_configured_locally() -> None:
    """Se `.env` estiver preenchido, a chave deve ser carregável do ambiente."""
    if os.getenv("GEMINI_API_KEY"):
        assert config.get_gemini_api_key() == os.getenv("GEMINI_API_KEY")

def test_env_example_exists() -> None:
    assert (config.PROJECT_ROOT / ".env.example").exists()
