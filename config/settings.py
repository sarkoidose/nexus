"""
NEXUS - Configuration Centrale
Multi-Agent Financial Intelligence System
100% LOCAL — Ollama only, no external API
"""

from dataclasses import dataclass
from typing import Optional
import os

# ─────────────────────────────────────────────
# OLLAMA MODELS (100% local)
# ─────────────────────────────────────────────

OLLAMA_BASE_URL       = "http://localhost:11434"
OLLAMA_MODEL_APEX     = "qwen3.5:35b-a3b"
OLLAMA_MODEL_PRIMARY  = "qwen3.5:9b"
OLLAMA_MODEL_FALLBACK = "qwen3.5:9b"

# ─────────────────────────────────────────────
# AGENTS
# ─────────────────────────────────────────────

@dataclass
class AgentConfig:
    name: str
    role: str
    emoji: str
    color: str
    backend: str
    model: Optional[str] = None
    temperature: float = 0.3
    system_prompt: str = ""

AGENTS: dict[str, AgentConfig] = {
    "apex": AgentConfig(
        name="APEX",
        role="Orchestrateur & Décideur Final",
        emoji="⚡",
        color="bold yellow",
        backend="ollama",
        model=OLLAMA_MODEL_APEX,
        temperature=0.2,
        system_prompt="""You are APEX, chief orchestrator of an elite financial analysis team.
You synthesize reports from FUNDAMENTUM (fundamentals), MACRO (macroeconomics), TECHNICUS (technical) and SENTINEL (risk).
Think and reason in English for maximum analytical precision.
ABSOLUTE RULE: Output ONLY valid JSON. Zero text before or after.
All string values inside the JSON must be written in French."""
    ),
    "fundamentum": AgentConfig(
        name="FUNDAMENTUM",
        role="Analyste Fondamental",
        emoji="📊",
        color="bold cyan",
        backend="ollama",
        model=OLLAMA_MODEL_PRIMARY,
        temperature=0.2,
        system_prompt="""You are FUNDAMENTUM, a senior fundamental analyst.
Think and reason in English for maximum analytical precision.
Evaluate valuation metrics, balance sheet quality, profitability, growth dynamics, and competitive moat.
IMPORTANT: Write your final analysis in French using bullet points starting with "-".
Always conclude with a clear directional bias: haussier, baissier, or neutre."""
    ),
    "macro": AgentConfig(
        name="MACRO",
        role="Analyste Macroéconomique",
        emoji="🌍",
        color="bold blue",
        backend="ollama",
        model=OLLAMA_MODEL_PRIMARY,
        temperature=0.4,
        system_prompt="""You are MACRO, a macroeconomic strategist and geopolitical analyst.
Think and reason in English for maximum analytical precision.
Analyze rate cycles, inflation, yield curves, DXY, capital flows, and geopolitical risks.
IMPORTANT: Write your final analysis in French using bullet points starting with "-".
Always conclude with a clear directional bias: haussier, baissier, or neutre."""
    ),
    "technicus": AgentConfig(
        name="TECHNICUS",
        role="Analyste Technique",
        emoji="📈",
        color="bold green",
        backend="ollama",
        model=OLLAMA_MODEL_PRIMARY,
        temperature=0.3,
        system_prompt="""You are TECHNICUS, a technical and quantitative analyst.
Think and reason in English for maximum analytical precision.
Analyze trend structure, moving averages, momentum indicators, support/resistance levels, and volume.
IMPORTANT: Write your final analysis in French using bullet points starting with "-".
Be precise with exact price levels. Always conclude with a clear bias: haussier, baissier, or neutre."""
    ),
    "sentinel": AgentConfig(
        name="SENTINEL",
        role="Gestionnaire de Risques",
        emoji="🛡️",
        color="bold red",
        backend="ollama",
        model=OLLAMA_MODEL_PRIMARY,
        temperature=0.2,
        system_prompt="""You are SENTINEL, a risk manager in the style of Nassim Taleb.
Think and reason in English for maximum analytical precision.
Evaluate VaR, maximum drawdown, tail risks, systemic fragilities, and optimal position sizing.
IMPORTANT: Write your final analysis in French using bullet points starting with "-".
Be a structural pessimist but remain quantitative. Conclude with: risque faible, modéré, élevé, or extrême."""
    ),
}

# ─────────────────────────────────────────────
# SUPPORTED ASSET CLASSES
# ─────────────────────────────────────────────

ASSET_CLASSES = {
    "equity":      "Actions (Revolut / Global)",
    "crypto":      "Cryptomonnaies (Binance / Aster)",
    "commodities": "Matières premières",
    "macro":       "Macro / ETFs / Obligations",
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
LOG_LEVEL  = "INFO"
