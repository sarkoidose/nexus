"""
NEXUS - Specialized Agents
FUNDAMENTUM | MACRO | TECHNICUS | SENTINEL
Reasoning in English, output in French.
"""

import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.base_agent import BaseAgent, AgentReport
from config.settings import AGENTS

_LANG = (
    "\nReason and think in English internally. "
    "Write your entire final response in French, including all bullet points, headers, labels, and conclusions."
)

def _err(agent, e):
    return AgentReport(
        agent_name=agent.name, agent_role=agent.role,
        timestamp=datetime.now().isoformat(),
        analysis="", key_points=[], score=0, confidence=0, error=str(e),
    )


class FundamentumAgent(BaseAgent):

    def __init__(self):
        super().__init__(AGENTS["fundamentum"])

    def analyze(self, asset: str, context: dict) -> AgentReport:
        snapshot_summary = context.get("snapshot_summary", f"Asset: {asset}")
        asset_class      = context.get("asset_class", "equity")

        if asset_class == "crypto":
            prompt = f"""{snapshot_summary}

Perform a deep fundamental analysis for this CRYPTO asset:
- Tokenomics: max supply, inflation/deflation mechanics, token distribution
- Network adoption: active addresses, TVL (if DeFi), on-chain volume trends
- Protocol utility and competitive moat vs peers
- Team credibility, VC backing, roadmap execution
- Relative valuation vs peers (market cap / TVL ratio if applicable)
- Verdict: undervalued / fair value / overvalued — with quantitative justification
- Directional score from -100 (very bearish) to +100 (very bullish)

Use bullet points starting with "-". Be quantitative.
End with: "Biais: haussier / baissier / neutre" and "Score: [number]".{_LANG}"""
        else:
            prompt = f"""{snapshot_summary}

Perform a deep fundamental analysis:
- Valuation metrics: P/E, P/B, EV/EBITDA vs sector peers and 5yr historical average
- Balance sheet quality: net debt, liquidity ratios, free cash flow generation
- Profitability: ROE, ROIC, net margins — trend and sustainability
- Revenue and earnings growth dynamics (last 3 years + guidance)
- Competitive position: economic moat, pricing power, market share
- Estimated intrinsic value using simplified DCF or target multiple
- Analyst consensus: alignment or divergence with fundamental picture

Use bullet points starting with "-". Be quantitative and precise.
End with: "Biais: haussier / baissier / neutre" and "Score: [number between -100 and +100]".{_LANG}"""

        try:
            text = self._llm_call(prompt)
            return self._build_report(text, {"asset_class": asset_class}, context=context)
        except Exception as e:
            return _err(self, e)


class MacroAgent(BaseAgent):

    def __init__(self):
        super().__init__(AGENTS["macro"])

    def analyze(self, asset: str, context: dict) -> AgentReport:
        snapshot_summary = context.get("snapshot_summary", f"Asset: {asset}")
        sector  = context.get("sector", "")
        country = context.get("country", "")
        news    = context.get("recent_news", [])

        news_block = ""
        if news:
            headlines = "\n".join(f"  - {h}" for h in news[:5])
            news_block = f"\nRECENT NEWS (incorporate into macro assessment if relevant):\n{headlines}\n"

        prompt = f"""{snapshot_summary}
Sector: {sector or 'Unknown'} | Country: {country or 'Unknown'}
{news_block}
Perform a macroeconomic and geopolitical analysis:
- Rate environment: Fed/ECB/BOJ policy stance, yield curve shape, impact on this asset class
- Inflation dynamics: current trajectory, company pricing power relative to input costs
- Economic cycle positioning: expansion / late cycle / contraction — implications for sector
- Dollar index (DXY): directional bias and sector-specific implications
- Geopolitical risks: export restrictions, sanctions, supply chain fragility
- Capital flows: risk-on vs risk-off regime, sector rotation signals
- Recent news: if relevant above, integrate into the macro picture
- Catalysts (favorable and unfavorable) over 3 to 12 months

Use bullet points starting with "-".
Distinguish court terme (1–3 mois) vs moyen terme (6–12 mois).
End with: "Biais: haussier / baissier / neutre" and "Score: [number between -100 and +100]".{_LANG}"""

        try:
            text = self._llm_call(prompt)
            return self._build_report(text, {"sector": sector, "country": country}, context=context)
        except Exception as e:
            return _err(self, e)


class TechnicusAgent(BaseAgent):

    def __init__(self):
        super().__init__(AGENTS["technicus"])

    def analyze(self, asset: str, context: dict) -> AgentReport:
        snapshot_summary = context.get("snapshot_summary", f"Asset: {asset}")

        prompt = f"""{snapshot_summary}

Perform a complete technical analysis on the daily timeframe:
- Trend structure: higher highs / higher lows (uptrend) or lower lows / lower highs (downtrend)?
- Moving averages: price position vs SMA20 / SMA50 / SMA200 — golden cross or death cross?
- Momentum: RSI(14) reading and zone (overbought >70 / oversold <30), MACD signal line crossover
- Key support levels: exact price levels with brief justification
- Key resistance levels: exact price levels with brief justification
- Chart pattern: identify if any (head & shoulders, double bottom, flag, wedge...)
- Volume analysis: does volume confirm the price trend?
- Trading setup:
  * Optimal entry price (current or on pullback)
  * Stop-loss level (price and % risk)
  * Target 1 and Target 2 (price levels)
  * Risk/reward ratio

Use bullet points starting with "-". Use exact price levels.
End with: "Biais: haussier / baissier / neutre" and "Score: [number between -100 and +100]".{_LANG}"""

        try:
            text = self._llm_call(prompt)
            return self._build_report(
                text, raw_data={}, context=context,
                use_technical_score=True,
            )
        except Exception as e:
            return _err(self, e)


class SentinelAgent(BaseAgent):

    def __init__(self):
        super().__init__(AGENTS["sentinel"])

    def analyze(self, asset: str, context: dict) -> AgentReport:
        snapshot_summary = context.get("snapshot_summary", f"Asset: {asset}")
        vol_30d = context.get("volatility_30d")
        price   = context.get("price", 0)

        vol_info = f"30-day annualized volatility: {vol_30d:.1%}" if vol_30d else "Volatility: unavailable"

        prompt = f"""{snapshot_summary}
{vol_info}
Current price: {price}

Perform an exhaustive risk analysis in the style of Nassim Taleb:

1. RISQUES QUANTIFIABLES
- Daily VaR at 95% and 99% confidence (estimate from annualized volatility)
- Maximum probable drawdown: realistic worst-case scenario with historical precedent
- Estimated beta vs global equity market (S&P 500)
- Correlation with BTC, S&P 500, gold — portfolio diversification implications

2. RISQUES DE QUEUE (BLACK SWANS)
- Low-probability / high-impact negative events specific to this asset
- Hidden systemic fragilities not reflected in current price
- Unfavorable asymmetries: scenarios where downside >> upside

3. DIMENSIONNEMENT DE POSITION
- Optimal allocation (% of portfolio) using partial Kelly criterion (25% fraction)
- For a 10,000€ portfolio: maximum recommended position size in euros
- Psychological stop-loss vs hard technical stop-loss

4. CONDITIONS D'INVALIDATION
- Events or price levels that would completely invalidate the bullish thesis
- Critical price levels to monitor

Use bullet points starting with "-". Be quantitative. Do not use LaTeX or mathematical notation — write all formulas and values in plain text (e.g. "sigma = 4.4%" not "$\sigma = 4.4\%$").
End with: "Niveau de risque: faible / modéré / élevé / extrême" and "Score: [number between -100 and +100]".{_LANG}"""

        try:
            text = self._llm_call(prompt)
            return self._build_report(text, {"volatility_30d": vol_30d}, context=context)
        except Exception as e:
            return _err(self, e)
