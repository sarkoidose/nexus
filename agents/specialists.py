"""
NEXUS - Agents Spécialisés
FUNDAMENTUM | MACRO | TECHNICUS | SENTINEL
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.base_agent import BaseAgent, AgentReport
from config.settings import AGENTS


class FundamentumAgent(BaseAgent):

    def __init__(self):
        super().__init__(AGENTS["fundamentum"])

    def analyze(self, asset: str, context: dict) -> AgentReport:
        snapshot_summary = context.get("snapshot_summary", f"Actif: {asset}")
        asset_class = context.get("asset_class", "equity")

        if asset_class == "crypto":
            prompt = f"""
{snapshot_summary}

Analyse fondamentale CRYPTO :
- Tokenomique (offre max, inflation/deflation, distribution)
- Adoption réseau : adresses actives, TVL si DeFi, volume on-chain
- Utilité du protocole et avantage compétitif
- Équipe, VC backing, roadmap
- Valorisation relative vs pairs (market cap / TVL si applicable)
- Verdict : sous-évalué / juste / surévalué
- Score directionnel : -100 à +100
"""
        else:
            prompt = f"""
{snapshot_summary}

Analyse fondamentale :
- Valorisation : P/E, P/B, EV/EBITDA vs secteur et historique
- Bilan : endettement, liquidité, FCF
- Profitabilité : ROE, ROIC, marges
- Croissance du CA et des bénéfices
- Position compétitive (moat)
- Valorisation intrinsèque estimée
- Verdict : sous-évalué / juste / surévalué
- Score directionnel : -100 à +100
"""
        try:
            text = self._llm_call(prompt)
            return self._build_report(text, {"asset_class": asset_class})
        except Exception as e:
            from datetime import datetime
            return AgentReport(
                agent_name=self.name, agent_role=self.role,
                timestamp=datetime.now().isoformat(),
                analysis="", key_points=[], score=0, confidence=0, error=str(e),
            )


class MacroAgent(BaseAgent):

    def __init__(self):
        super().__init__(AGENTS["macro"])

    def analyze(self, asset: str, context: dict) -> AgentReport:
        snapshot_summary = context.get("snapshot_summary", f"Actif: {asset}")
        sector  = context.get("sector", "")
        country = context.get("country", "")

        prompt = f"""
{snapshot_summary}
Secteur: {sector or 'Non précisé'} | Pays: {country or 'Non précisé'}

Analyse macroéconomique :
- Environnement de taux : Fed/BCE, courbe des taux, impact sur l'actif
- Inflation et pouvoir de fixation des prix
- Cycle économique actuel et position dans le cycle
- Dollar index (DXY) et implications
- Risques géopolitiques spécifiques
- Flux de capitaux : risk-on vs risk-off
- Catalyseurs macro favorables et défavorables (3-12 mois)
- Score directionnel : -100 à +100
"""
        try:
            text = self._llm_call(prompt)
            return self._build_report(text, {"sector": sector, "country": country})
        except Exception as e:
            from datetime import datetime
            return AgentReport(
                agent_name=self.name, agent_role=self.role,
                timestamp=datetime.now().isoformat(),
                analysis="", key_points=[], score=0, confidence=0, error=str(e),
            )


class TechnicusAgent(BaseAgent):

    def __init__(self):
        super().__init__(AGENTS["technicus"])

    def analyze(self, asset: str, context: dict) -> AgentReport:
        snapshot_summary = context.get("snapshot_summary", f"Actif: {asset}")

        prompt = f"""
{snapshot_summary}

Analyse technique :
- Structure de tendance : HH/HL (uptrend) ou LL/LH (downtrend) ?
- Position vs moyennes mobiles SMA 20/50/200 : golden/death cross ?
- Momentum : RSI (suracheté >70 / survendu <30), MACD
- Supports clés et résistances majeures (niveaux chiffrés)
- Configuration chartiste identifiée
- Volume : confirme-t-il la tendance ?
- Setup :
  * Entrée optimale
  * Stop-loss (niveau et % de risque)
  * Objectif 1 et Objectif 2
  * Ratio risque/rendement
- Score directionnel : -100 à +100
"""
        try:
            text = self._llm_call(prompt)
            return self._build_report(text, {})
        except Exception as e:
            from datetime import datetime
            return AgentReport(
                agent_name=self.name, agent_role=self.role,
                timestamp=datetime.now().isoformat(),
                analysis="", key_points=[], score=0, confidence=0, error=str(e),
            )


class SentinelAgent(BaseAgent):

    def __init__(self):
        super().__init__(AGENTS["sentinel"])

    def analyze(self, asset: str, context: dict) -> AgentReport:
        snapshot_summary = context.get("snapshot_summary", f"Actif: {asset}")
        vol_30d = context.get("volatility_30d")
        price   = context.get("price", 0)
        vol_info = f"Volatilité annualisée 30j: {vol_30d:.1%}" if vol_30d else "Volatilité: non disponible"

        prompt = f"""
{snapshot_summary}
{vol_info} | Prix: {price}

Analyse de risques (style Taleb) :

1. RISQUES QUANTIFIABLES
- VaR journalière 95% et 99%
- Drawdown maximum probable
- Beta estimé vs marché global

2. RISQUES DE QUEUE
- Événements à faible probabilité / fort impact négatif
- Fragilités systémiques cachées
- Asymétries défavorables non pricées

3. SIZING
- % du portefeuille recommandé (Kelly partiel 25%)
- Pour 10 000€ : montant maximum
- Stop-loss psychologique vs technique

4. CONDITIONS D'INVALIDATION
- Événements qui invalideraient la thèse haussière
- Niveaux de prix critiques

Score de risque : 0 à 100. Score directionnel : -100 à +100.
"""
        try:
            text = self._llm_call(prompt)
            return self._build_report(text, {"volatility_30d": vol_30d})
        except Exception as e:
            from datetime import datetime
            return AgentReport(
                agent_name=self.name, agent_role=self.role,
                timestamp=datetime.now().isoformat(),
                analysis="", key_points=[], score=0, confidence=0, error=str(e),
            )
