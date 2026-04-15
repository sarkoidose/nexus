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
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.base_agent import AgentReport
from agents.specialists import FundamentumAgent, MacroAgent, TechnicusAgent, SentinelAgent
from agents.apex import ApexAgent, NexusDecision
from data.fetcher import DataFetcher, MarketSnapshot
from rich.console import Console

console = Console()

# Rapport vide réutilisable pour le fallback du mode portefeuille.
_EMPTY_REPORT = AgentReport(
    agent_name="", agent_role="", timestamp="",
    analysis="", key_points=[], score=0, confidence=0,
)


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
        # Deux pools HTTP partagés :
        # - data_client : Yahoo / CoinGecko / RSS (timeout court, 30 s)
        # - llm_client  : Ollama local (timeout long, réponses LLM)
        self._data_client = httpx.Client(timeout=30.0, follow_redirects=True)
        self._llm_client  = httpx.Client(timeout=300.0)

        self.fetcher     = DataFetcher(client=self._data_client)
        self.fundamentum = FundamentumAgent(client=self._llm_client)
        self.macro       = MacroAgent(client=self._llm_client)
        self.technicus   = TechnicusAgent(client=self._llm_client)
        self.sentinel    = SentinelAgent(client=self._llm_client)
        self.apex        = ApexAgent(client=self._llm_client)

    def close(self):
        """Ferme proprement les pools HTTP partagés."""
        for client in (self._data_client, self._llm_client):
            try:
                client.close()
            except Exception:
                pass

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

        # 2. Agents en parallèle (4 threads, Ollama doit accepter la concurrence)
        reports: dict[str, AgentReport] = {}
        agent_tasks = [
            ("fundamentum", self.fundamentum),
            ("macro",       self.macro),
            ("technicus",   self.technicus),
            ("sentinel",    self.sentinel),
        ]

        if progress_callback:
            progress_callback("⚙️ Agents spécialisés en parallèle...", 20)

        def _run(name, agent):
            try:
                return name, agent.analyze(asset, context), None
            except Exception as e:
                return name, None, e

        with ThreadPoolExecutor(max_workers=len(agent_tasks)) as executor:
            futures = [executor.submit(_run, name, agent) for name, agent in agent_tasks]
            done = 0
            for fut in as_completed(futures):
                name, report, err = fut.result()
                done += 1
                pct = 20 + int((done / len(agent_tasks)) * 60)  # 20→80
                if err is not None:
                    agent = dict(agent_tasks)[name]
                    reports[name] = AgentReport(
                        agent_name=agent.name, agent_role=agent.role,
                        timestamp=datetime.now().isoformat(),
                        analysis="", key_points=[], score=0, confidence=0, error=str(err),
                    )
                else:
                    reports[name] = report
                if progress_callback:
                    progress_callback(f"✓ {name.upper()} terminé ({done}/{len(agent_tasks)})", pct)

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

                f = reports.get("fundamentum", _EMPTY_REPORT)
                m = reports.get("macro",       _EMPTY_REPORT)
                t = reports.get("technicus",   _EMPTY_REPORT)
                s = reports.get("sentinel",    _EMPTY_REPORT)
                results.append(PortfolioResult(
                    ticker=ticker, name=name,
                    price=price, change_24h=change_24h,
                    apex_action=apex_action, conviction=conviction,
                    score_fundamentum=f.score, score_macro=m.score,
                    score_technicus=t.score,   score_sentinel=s.score,
                    conf_fundamentum=f.confidence, conf_macro=m.confidence,
                    conf_technicus=t.confidence,   conf_sentinel=s.confidence,
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
        from config.settings import OLLAMA_BASE_URL
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{OLLAMA_BASE_URL}/api/tags")
                resp.raise_for_status()
                models = [m["name"] for m in resp.json().get("models", [])]
            return True, models
        except Exception:
            return False, []
