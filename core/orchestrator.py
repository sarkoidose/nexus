"""
NEXUS - Moteur d'Orchestration Principal
Coordonne les agents, gère le flux et les erreurs.
Inclut le mode portefeuille multi-actifs.
"""

import sys
import os
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.base_agent import AgentReport
from agents.specialists import FundamentumAgent, MacroAgent, TechnicusAgent, SentinelAgent
from agents.apex import ApexAgent, NexusDecision
from data.fetcher import DataFetcher, MarketSnapshot
from rich.console import Console

console = Console()


@dataclass
class PortfolioResult:
    """Résultat d'analyse d'un actif dans le mode portefeuille."""
    ticker: str
    name: str
    price: float
    change_24h: float
    apex_action: str
    conviction: int
    score_fundamentum: int
    score_macro: int
    score_technicus: int
    score_sentinel: int
    conf_fundamentum: int
    conf_macro: int
    conf_technicus: int
    conf_sentinel: int
    stop_loss: Optional[float]
    target: Optional[float]
    position_size: Optional[float]
    error: Optional[str] = None


class NexusOrchestrator:
    """Orchestrateur central de NEXUS."""

    def __init__(self):
        self.fetcher     = DataFetcher()
        self.fundamentum = FundamentumAgent()
        self.macro       = MacroAgent()
        self.technicus   = TechnicusAgent()
        self.sentinel    = SentinelAgent()
        self.apex        = ApexAgent()

    # ─────────────────────────────────────────────
    # ANALYSE UNIQUE
    # ─────────────────────────────────────────────
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
        snapshot_summary = f"Asset: {asset}"
        if snapshot:
            snapshot_summary = snapshot.summary()
            context = snapshot.to_context_dict()
            context["snapshot_summary"] = snapshot_summary
        else:
            context = {"asset": asset, "asset_class": asset_class, "snapshot_summary": snapshot_summary}

        # 2. Agents séquentiels
        reports: dict[str, AgentReport] = {}
        agent_tasks = [
            ("fundamentum", self.fundamentum, "📊 FUNDAMENTUM — Fondamentaux",   20),
            ("macro",       self.macro,       "🌍 MACRO — Macroéconomie",         38),
            ("technicus",   self.technicus,   "📈 TECHNICUS — Analyse technique", 56),
            ("sentinel",    self.sentinel,    "🛡️ SENTINEL — Gestion des risques", 74),
        ]

        for name, agent, label, pct in agent_tasks:
            if progress_callback:
                progress_callback(label, pct)
            try:
                reports[name] = agent.analyze(asset, context)
            except Exception as e:
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

    # ─────────────────────────────────────────────
    # MODE PORTEFEUILLE MULTI-ACTIFS
    # ─────────────────────────────────────────────
    def run_portfolio(
        self,
        tickers: list[str],
        progress_callback=None,
    ) -> list[PortfolioResult]:
        """
        Analyse une liste d'actifs séquentiellement.
        Retourne un tableau récapitulatif (sans TUI complète par actif).
        """
        results: list[PortfolioResult] = []
        total = len(tickers)

        for i, ticker in enumerate(tickers):
            if progress_callback:
                pct = int((i / total) * 100)
                progress_callback(f"📊 Analyse {ticker} ({i+1}/{total})...", pct)

            try:
                snapshot, reports, decision = self.run_analysis(
                    asset=ticker,
                    asset_class="auto",
                    progress_callback=None,  # Pas de progress par actif en mode portefeuille
                )

                name       = snapshot.name if snapshot else ticker
                price      = snapshot.price if snapshot else 0.0
                change_24h = snapshot.price_24h_change_pct if snapshot else 0.0

                apex_action  = decision.action if decision else "N/A"
                conviction   = decision.conviction if decision else 0
                stop_loss    = decision.stop_loss if decision else None
                target       = decision.target_price if decision else None
                position_sz  = decision.position_size if decision else None

                results.append(PortfolioResult(
                    ticker=ticker, name=name,
                    price=price, change_24h=change_24h,
                    apex_action=apex_action, conviction=conviction,
                    score_fundamentum=reports.get("fundamentum", AgentReport("","","","",[], 0,0)).score,
                    score_macro=reports.get("macro",       AgentReport("","","","",[], 0,0)).score,
                    score_technicus=reports.get("technicus",  AgentReport("","","","",[], 0,0)).score,
                    score_sentinel=reports.get("sentinel",   AgentReport("","","","",[], 0,0)).score,
                    conf_fundamentum=reports.get("fundamentum", AgentReport("","","","",[], 0,0)).confidence,
                    conf_macro=reports.get("macro",       AgentReport("","","","",[], 0,0)).confidence,
                    conf_technicus=reports.get("technicus",  AgentReport("","","","",[], 0,0)).confidence,
                    conf_sentinel=reports.get("sentinel",   AgentReport("","","","",[], 0,0)).confidence,
                    stop_loss=stop_loss, target=target, position_size=position_sz,
                ))

            except Exception as e:
                results.append(PortfolioResult(
                    ticker=ticker, name=ticker, price=0.0, change_24h=0.0,
                    apex_action="ERREUR", conviction=0,
                    score_fundamentum=0, score_macro=0, score_technicus=0, score_sentinel=0,
                    conf_fundamentum=0, conf_macro=0, conf_technicus=0, conf_sentinel=0,
                    stop_loss=None, target=None, position_size=None, error=str(e),
                ))

        if progress_callback:
            progress_callback("✅ Portefeuille analysé", 100)

        return results

    # ─────────────────────────────────────────────
    # UTILITAIRES
    # ─────────────────────────────────────────────
    def check_ollama(self) -> tuple[bool, list[str]]:
        import httpx
        from config.settings import OLLAMA_BASE_URL
        try:
            client = httpx.Client(timeout=5.0)
            resp   = client.get(f"{OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            client.close()
            return True, models
        except Exception:
            return False, []
