"""
NEXUS - Central Configuration
Multi-Agent Financial Intelligence System
100% LOCAL — Ollama only, no external API
"""

from dataclasses import dataclass
from typing import Optional
import os

# ─────────────────────────────────────────────
# OLLAMA MODELS
# ─────────────────────────────────────────────

OLLAMA_BASE_URL       = "http://localhost:11434"
OLLAMA_MODEL_APEX     = "qwen3.5:35b-a3b"
OLLAMA_MODEL_PRIMARY  = "qwen3.5:9b"
OLLAMA_MODEL_FALLBACK = "qwen3.5:9b"

# ─────────────────────────────────────────────
# AGENT CONFIGS
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
        system_prompt="""You are APEX, chief investment decision-maker of an elite multi-agent financial analysis system.
You receive structured reports from four specialist agents:
- FUNDAMENTUM: fundamental valuation and financial quality
- MACRO: macroeconomic environment and geopolitical risks
- TECHNICUS: technical analysis and price action
- SENTINEL: tail risk management (Taleb-style)

Your role: synthesize their inputs into a single, actionable investment decision.
Think rigorously. Be precise. Output ONLY valid JSON — zero text before or after the JSON block."""
    ),
    "fundamentum": AgentConfig(
        name="FUNDAMENTUM",
        role="Analyste Fondamental",
        emoji="📊",
        color="bold cyan",
        backend="ollama",
        model=OLLAMA_MODEL_PRIMARY,
        temperature=0.2,
        system_prompt="""You are FUNDAMENTUM, a senior fundamental equity analyst at a top-tier investment firm.
Your mandate: evaluate the intrinsic value, financial quality, and competitive positioning of any asset.
Be rigorous, quantitative, and intellectually honest.
Reason internally in English for maximum precision. Write your entire final response in French."""
    ),
    "macro": AgentConfig(
        name="MACRO",
        role="Analyste Macroéconomique",
        emoji="🌍",
        color="bold blue",
        backend="ollama",
        model=OLLAMA_MODEL_PRIMARY,
        temperature=0.4,
        system_prompt="""You are MACRO, a global macro strategist and geopolitical analyst.
Your mandate: assess the macroeconomic environment, rate cycles, capital flows, and geopolitical risks affecting an asset.
Think in terms of regime changes, reflexivity, and second-order effects.
Reason internally in English for maximum precision. Write your entire final response in French."""
    ),
    "technicus": AgentConfig(
        name="TECHNICUS",
        role="Analyste Technique",
        emoji="📈",
        color="bold green",
        backend="ollama",
        model=OLLAMA_MODEL_PRIMARY,
        temperature=0.3,
        system_prompt="""You are TECHNICUS, a quantitative technical analyst with expertise in price action and market structure.
Your mandate: identify trend structure, momentum signals, key levels, and optimal trade setups.
Be precise with exact price levels. Never use vague directional language without a number.
Reason internally in English for maximum precision. Write your entire final response in French."""
    ),
    "sentinel": AgentConfig(
        name="SENTINEL",
        role="Gestionnaire de Risques",
        emoji="🛡️",
        color="bold red",
        backend="ollama",
        model=OLLAMA_MODEL_PRIMARY,
        temperature=0.2,
        system_prompt="""You are SENTINEL, a risk manager in the tradition of Nassim Taleb.
Your mandate: identify tail risks, quantify downside scenarios, and size positions to survive black swan events.
Be a structural pessimist but remain quantitative — every risk claim must be supported by a number or scenario.
Reason internally in English for maximum precision. Write your entire final response in French."""
    ),
}

# ─────────────────────────────────────────────
# MISC
# ─────────────────────────────────────────────

ASSET_CLASSES = {
    "equity":      "Actions (Revolut / Global)",
    "crypto":      "Cryptomonnaies (Binance / Aster)",
    "commodities": "Matières premières",
    "macro":       "Macro / ETFs / Obligations",
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
LOG_LEVEL  = "INFO"
