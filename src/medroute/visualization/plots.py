"""Gráficos de análise do algoritmo genético (convergência do fitness)."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot_fitness_history(
    fitness_history: Sequence[float],
    output_path: str | Path,
    title: str = "Convergência do Algoritmo Genético",
) -> Path:
    """Salva gráfico PNG da evolução do melhor fitness por geração."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=120)
    ax.plot(range(len(fitness_history)), fitness_history, color="tab:blue")
    ax.set_xlabel("Geração")
    ax.set_ylabel("Melhor fitness (custo)")
    ax.set_title(title)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path
