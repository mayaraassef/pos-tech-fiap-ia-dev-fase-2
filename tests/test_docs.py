"""Fase 5 — validação final: todos os artefatos de entrega existem."""
from __future__ import annotations

from medroute.config import PROJECT_ROOT

def _exists_nonempty(rel: str) -> bool:
    p = PROJECT_ROOT / rel
    return p.exists() and p.stat().st_size > 0

def test_required_documentation_files_exist() -> None:
    for rel in [
        "README.md",
        "docs/architecture.md",
        "docs/relatorio_tecnico.md",
        ".env.example",
        "Pipfile",
        "pyproject.toml",
        "pytest.ini",
    ]:
        assert _exists_nonempty(rel), f"artefato ausente: {rel}"

def test_base_tsp_lineage_preserved() -> None:
    operators = (PROJECT_ROOT / "src/medroute/ga/operators.py").read_text(
        encoding="utf-8"
    )
    assert "order_crossover" in operators
    assert "genetic_algorithm_tsp" in operators

def test_report_covers_required_sections() -> None:
    report = (PROJECT_ROOT / "docs" / "relatorio_tecnico.md").read_text(
        encoding="utf-8"
    )
    for topic in [
        "algoritmo genético",
        "restriç",
        "LLM",
        "prompt",
        "Visualiza",
        "Comparativo",
        "capacidade",
        "autonomia",
        "veículo",
        "prioridade",
    ]:
        assert topic.lower() in report.lower(), f"seção '{topic}' ausente"

def test_architecture_doc_has_diagrams() -> None:
    doc = (PROJECT_ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    assert "```mermaid" in doc

def test_demo_and_benchmark_scripts_exist() -> None:
    assert _exists_nonempty("src/medroute/cli.py")
    assert _exists_nonempty("scripts/benchmark.py")
    assert _exists_nonempty("notebooks/demo_medroute.ipynb")

def test_env_not_committable() -> None:
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore
