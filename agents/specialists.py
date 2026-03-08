"""
NEXUS - Agents Spécialisés
FUNDAMENTUM | MACRO | TECHNICUS | SENTINEL
Prompts in English for maximum analytical precision.
Output in French for TUI display.
"""

import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.base_agent import BaseAgent, AgentReport
from config.settings import AGENTS


def _err(agent, e):
    return AgentReport(
        agent_name=agent.name,
        agent_role=agent.role,
        timestamp=datetime.now().isoformat(),
        analysis="", key_points=[],
        score=0, confidence=0, error=str(e),
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
- Tokenomics: max supply, inflation/deflation mechanics, distribution
- Network adoption: active addresses, TVL (if DeFi), on-chain volume
- Protocol utility and competitive moat
- Team, VC backing, roadmap milestones
- Relative valuation vs peers (market cap / TVL ratio if applicable)
- Verdict: undervalued / fair value / overvalued with justification
- Directional score from -100 (very bearish) to +100 (very bullish)

Be quantitative. Write your response in French using bullet points starting with "-".
Conclude with a clear bias: haussier, baissier, or neutre."""
        else:
            prompt = f"""{snapshot_summary}

Perform a deep fundamental analysis:
- Valuation metrics: P/E, P/B, EV/EBITDA vs sector peers and historical average
- Balance sheet quality: debt levels, liquidity, FCF generation
- Profitability: ROE, ROIC, net margins
- Revenue and earnings growth dynamics
- Competitive position and economic moat
- Estimated intrinsic value (simplified DCF or target multiple)
- Analyst consensus: if available, how does it align with fundamentals?
- Verdict: undervalued / fair / overvalued

Write your response in French using bullet points starting with "-".
Conclude with a clear directional bias: haussier, baissier, or neutre.
Directional score: -100 (very bearish) to +100 (very bullish)."""

        try:
            text   = self._llm_call(prompt)
            report = self._build_report(text, {"asset_class": asset_class})
            return report
        except Exception as e:
            return _err(self, e)


class MacroAgent(BaseAgent):

    def __init__(self):
        super().__init__(AGENTS["macro"])

    def analyze(self, asset: str, context: dict) -> AgentReport:
        snapshot_summary = context.get("snapshot_summary", f"Asset: {asset}")
        sector  = context.get("sector", "")
        country = context.get("country", "")

        prompt = f"""{snapshot_summary}
Sector: {sector or 'Unknown'} | Country: {country or 'Unknown'}

Perform a macroeconomic and geopolitical analysis:
- Rate environment: Fed/ECB/BOJ policy, yield curve shape, impact on this asset
- Inflation dynamics and pricing power of the company
- Current economic cycle (expansion/contraction/late cycle) and its implications
- Dollar index (DXY) and implications (especially for commodities and EM assets)
- Geopolitical risks specific to the sector or country
- Capital flows: risk-on vs risk-off, sector rotation trends
- Favorable and unfavorable macro catalysts over 3-12 months
- If analyst consensus is available in the data, factor it into the macro outlook

Write your response in French using bullet points starting with "-".
Distinguish short term (1-3 months) and medium term (6-12 months).
Conclude with a clear directional bias: haussier, baissier, or neutre.
Macro directional score: -100 to +100."""

        try:
            text = self._llm_call(prompt)
            return self._build_report(text, {"sector": sector, "country": country})
        except Exception as e:
            return _err(self, e)


class TechnicusAgent(BaseAgent):

    def __init__(self):
        super().__init__(AGENTS["technicus"])

    def analyze(self, asset: str, context: dict) -> AgentReport:
        snapshot_summary = context.get("snapshot_summary", f"Asset: {asset}")

        prompt = f"""{snapshot_summary}

Perform a complete technical analysis:
- Trend structure: HH/HL (uptrend) or LL/LH (downtrend)? Daily timeframe.
- Position vs moving averages (SMA 20/50/200): golden cross / death cross?
- Momentum: RSI (overbought >70 / oversold <30), MACD signal
- Key support and resistance levels (exact price levels)
- Chart pattern identified (if any)
- Volume: does it confirm the trend?
- Trading setup:
  * Optimal entry price
  * Stop-loss level and risk percentage
  * Target 1 and Target 2
  * Risk/reward ratio
- Directional bias: -100 (very bearish) to +100 (very bullish)

Write your response in French using bullet points starting with "-".
Be precise with exact price levels.
Conclude with a clear bias: haussier, baissier, or neutre."""

        try:
            text = self._llm_call(prompt)
            return self._build_report(text, {})
        except Exception as e:
            return _err(self, e)


class SentinelAgent(BaseAgent):

    def __init__(self):
        super().__init__(AGENTS["sentinel"])

    def analyze(self, asset: str, context: dict) -> AgentReport:
        snapshot_summary = context.get("snapshot_summary", f"Asset: {asset}")
        vol_30d = context.get("volatility_30d")
        price   = context.get("price", 0)

        vol_info = f"30d annualized volatility: {vol_30d:.1%}" if vol_30d else "Volatility: unavailable"

        prompt = f"""{snapshot_summary}
{vol_info}
Current price: {price}

Perform an exhaustive risk analysis (Nassim Taleb style):

1. QUANTIFIABLE RISKS
- Daily VaR 95% and 99% (estimate based on volatility)
- Maximum probable drawdown (realistic worst case)
- Estimated beta vs global market
- Correlation with other major assets (BTC, S&P500, gold)

2. TAIL RISKS (BLACK SWANS)
- Low-probability / high-impact negative events specific to this asset
- Hidden systemic fragilities
- Unfavorable asymmetries not yet priced in

3. POSITION SIZING
- Optimal sizing (% of portfolio) using partial Kelly (25%)
- For a 10,000€ portfolio: maximum recommended amount
- Psychological stop-loss vs technical stop-loss

4. INVALIDATION CONDITIONS
- What events would completely invalidate the bullish thesis?
- Critical price levels to monitor

Write your response in French using bullet points starting with "-".
Risk score: 0 (minimal risk) to 100 (extreme risk).
Directional score: -100 to +100.
Conclude with: risque faible, modéré, élevé, or extrême."""

        try:
            text = self._llm_call(prompt)
            return self._build_report(text, {"volatility_30d": vol_30d})
        except Exception as e:
            return _err(self, e)
