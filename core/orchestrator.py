"""
NEXUS - Moteur d'Orchestration Principal
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.base_agent import AgentReport
from agents.specialists import FundamentumAgent, MacroAgent, TechnicusAgent, SentinelAgent
from agents.apex import ApexAgent, NexusDecision
from data.fetcher import DataFetcher, MarketSnapshot
from typing import Optional
from rich.console import Console

console = Console()


class NexusOrchestrator:

    def __init__(self):
        self.fetcher      = DataFetcher()
        self.fundamentum  = FundamentumAgent()
        self.macro        = MacroAgent()
        self.technicus    = TechnicusAgent()
        self.sentinel     = SentinelAgent()
        self.apex         = ApexAgent()

    def run_analysis(
        self,
        asset: str,
        asset_class: str = "auto",
        progress_callback=None,
    ) -> tuple[Optional[MarketSnapshot], dict[str, AgentReport], Optional[NexusDecision]]:

        # 1. Collecte données
        snapshot = None
        try:
            if progress_callback:
                progress_callback("📡 Collecte données marché...", 0)
            snapshot = self.fetcher.fetch(asset, asset_class)
        except Exception as e:
            console.print(f"[yellow]⚠️ Données marché limitées: {e}[/yellow]")

        context = {}
        snapshot_summary = f"Actif: {asset}"

        if snapshot:
            snapshot_summary = snapshot.summary()
            context = snapshot.to_context_dict()
            context["snapshot_summary"] = snapshot_summary
        else:
            context = {
                "asset": asset,
                "asset_class": asset_class,
                "snapshot_summary": snapshot_summary,
            }

        # 2. Analyses séquentielles
        reports: dict[str, AgentReport] = {}

        agent_tasks = [
            ("fundamentum", self.fundamentum, "📊 FUNDAMENTUM — Fondamentaux", 20),
            ("macro",        self.macro,       "🌍 MACRO — Macroéconomie",      38),
            ("technicus",    self.technicus,   "📈 TECHNICUS — Technique",       56),
            ("sentinel",     self.sentinel,    "🛡️ SENTINEL — Risques",          74),
        ]

        for name, agent, label, pct in agent_tasks:
            if progress_callback:
                progress_callback(label, pct)
            try:
                reports[name] = agent.analyze(asset, context)
            except Exception as e:
                from datetime import datetime
                reports[name] = AgentReport(
                    agent_name=agent.name, agent_role=agent.role,
                    timestamp=datetime.now().isoformat(),
                    analysis="", key_points=[], score=0, confidence=0, error=str(e),
                )

        # 3. Synthèse APEX
        if progress_callback:
            progress_callback("⚡ APEX — Synthèse finale...", 90)

        decision = None
        try:
            decision = self.apex.synthesize(
                asset=asset,
                snapshot_summary=snapshot_summary,
                reports=reports,
                price=snapshot.price if snapshot else 0.0,
            )
        except Exception as e:
            console.print(f"[red]❌ Erreur APEX: {e}[/red]")

        if progress_callback:
            progress_callback("✅ Analyse complète", 100)

        return snapshot, reports, decision

    def check_ollama(self) -> tuple[bool, list[str]]:
        import httpx
        from config.settings import OLLAMA_BASE_URL
        try:
            client = httpx.Client(timeout=5.0)
            resp = client.get(f"{OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            client.close()
            return True, models
        except Exception:
            return False, []
