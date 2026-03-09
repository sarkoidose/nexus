"""
NEXUS - Classe de Base des Agents
100% LOCAL — Backend Ollama uniquement
"""
import httpx
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import AgentConfig, OLLAMA_BASE_URL, OLLAMA_MODEL_PRIMARY, OLLAMA_MODEL_FALLBACK


@dataclass
class AgentReport:
    agent_name: str
    agent_role: str
    timestamp: str
    analysis: str
    key_points: list[str]
    score: int          # -100 à +100
    confidence: int     # 0-100
    raw_data: dict = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "agent":      self.agent_name,
            "role":       self.agent_role,
            "timestamp":  self.timestamp,
            "analysis":   self.analysis,
            "key_points": self.key_points,
            "score":      self.score,
            "confidence": self.confidence,
            "error":      self.error,
        }


class BaseAgent(ABC):

    def __init__(self, config: AgentConfig):
        self.config  = config
        self.name    = config.name
        self.role    = config.role
        self.emoji   = config.emoji
        self._client = httpx.Client(timeout=600.0)

    def _call_ollama(self, prompt: str, model: str = None) -> str:
        model = model or self.config.model or OLLAMA_MODEL_PRIMARY
        payload = {
            "model": model,
            "prompt": f"Today's date: {datetime.now().strftime('%d %B %Y')}\n\n{self.config.system_prompt}\n\n{prompt}",
            "stream": False,
            "think": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": 2048,
                "num_ctx": 4096,
            }
        }
        try:
            resp = self._client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=600.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "") or data.get("thinking", "")
        except httpx.ConnectError:
            raise RuntimeError(f"Ollama inaccessible sur {OLLAMA_BASE_URL}\nLance : ollama serve")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404 and model != OLLAMA_MODEL_FALLBACK:
                return self._call_ollama(prompt, OLLAMA_MODEL_FALLBACK)
            raise RuntimeError(f"Erreur Ollama HTTP {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Erreur Ollama: {e}")

    def _llm_call(self, prompt: str) -> str:
        return self._call_ollama(prompt)

    # ─────────────────────────────────────────────
    # SCORE TECHNIQUE DÉTERMINISTE (basé sur prix)
    # ─────────────────────────────────────────────
    def _compute_technical_score(self, context: dict) -> Optional[int]:
        """
        Score TECHNICUS calculé directement depuis les données de marché.
        Retourne None si données insuffisantes.
        """
        price   = context.get("price", 0)
        sma50   = context.get("sma_50")
        sma200  = context.get("sma_200")
        rsi     = context.get("rsi_14")
        vol     = context.get("volatility_30d")

        if not price or not sma50:
            return None

        score = 0

        # Prix vs SMA50 (+/- 20 pts)
        if price > sma50:
            score += 20
        else:
            score -= 20

        # Prix vs SMA200 (+/- 15 pts)
        if sma200:
            if price > sma200:
                score += 15
            else:
                score -= 15

        # Golden/Death cross SMA50 vs SMA200 (+/- 10 pts)
        if sma50 and sma200:
            if sma50 > sma200:
                score += 10   # Golden cross structure
            else:
                score -= 10   # Death cross structure

        # RSI (+/- 20 pts)
        if rsi:
            if rsi < 30:
                score += 20   # Survendu = opportunité rebond
            elif rsi > 70:
                score -= 20   # Suracheté = risque retournement
            elif rsi < 40:
                score += 5    # Zone survente relative = léger positif
            elif rsi > 60:
                score -= 5    # Zone surachat relative = léger négatif

        # Distance au 52s high (momentum)
        week52h = context.get("week_52_high")
        if week52h and price:
            pct_from_high = (price / week52h - 1) * 100
            if pct_from_high > -10:
                score += 10   # Proche des plus hauts
            elif pct_from_high < -30:
                score -= 10   # Loin des plus hauts

        # Volatilité élevée = pénalité légère
        if vol and vol > 0.50:
            score -= 5

        return max(-80, min(80, score))

    # ─────────────────────────────────────────────
    # CONFIANCE DYNAMIQUE
    # ─────────────────────────────────────────────
    def _compute_confidence(self, analysis_text: str, context: dict) -> int:
        """
        Confiance calculée selon :
        - Quantité de données disponibles
        - Longueur et richesse de l'analyse
        """
        conf = 40  # base

        # Données disponibles
        data_fields = ["pe_ratio", "roe", "sma_50", "sma_200", "rsi_14",
                       "volatility_30d", "revenue_growth", "profit_margin",
                       "analyst_target_mean"]
        available = sum(1 for f in data_fields if context.get(f))
        conf += min(25, available * 3)  # +3 par champ, max +25

        # Richesse de l'analyse (longueur)
        words = len(analysis_text.split())
        if words > 400:
            conf += 15
        elif words > 200:
            conf += 10
        elif words > 100:
            conf += 5

        # Consensus analystes disponible = +10
        if context.get("analyst_target_mean"):
            conf += 10

        return min(90, conf)

    # ─────────────────────────────────────────────
    # PARSER SCORE TEXTUEL (pour FUNDAMENTUM/MACRO/SENTINEL)
    # ─────────────────────────────────────────────
    def _parse_score_from_text(self, text: str) -> tuple[int, int]:
        score = 0
        confidence = 50
        text_lower = text.lower()
        bullish = [
            "haussier", "bullish", "achat fort", "signal d'achat", "acheter", "buy",
            "accumulate", "accumuler", "surperformance", "golden cross",
            "sous-évalué", "sous-valorisé", "opportunité", "solide", "exceptionnel",
            "dominance", "monopole", "moat", "avantage compétitif", "leader",
            "marges élevées", "marge exceptionnelle", "rentabilité",
            "croissance", "croissance des revenus", "hausse des bénéfices",
            "fcf", "cash flow", "bilan solide",
            "assouplissement", "pivot", "baisse des taux", "taux en baisse",
            "rotation favorable", "risk-on", "soft landing", "atterrissage en douceur",
            "reprise économique", "expansion",
            "rebond", "reprise", "soutien", "support solide", "au-dessus",
            "momentum positif", "hausse", "upside", "potentiel haussier",
            "strong buy", "consensus haussier", "potentiel de hausse",
        ]
        bearish = [
            "baissier", "bearish", "vendre", "sell", "éviter", "avoid",
            "signal baissier", "death cross", "pression vendeuse",
            "surévalué", "surévaluation", "prime excessive",
            "détérioration", "dégradation", "fragile", "endettement élevé",
            "perte", "contraction des marges", "ralentissement de la croissance",
            "resserrement", "hausse des taux", "taux élevés", "risk-off",
            "récession", "stagflation", "inflation persistante", "dollar fort",
            "risque géopolitique", "restriction", "embargo", "sanctions",
            "correction", "rupture", "cassure", "en-dessous", "drawdown",
            "volatilité élevée", "résistance forte", "momentum négatif",
            "survendu", "oversold", "breakdown",
            "risque élevé", "risque extrême", "black swan", "fragilité",
            "concentration", "dépendance", "fuite des capitaux",
        ]
        bull_count = sum(1 for kw in bullish if kw in text_lower)
        bear_count = sum(1 for kw in bearish if kw in text_lower)
        if bull_count > bear_count:
            score = min(80, bull_count * 6)
        elif bear_count > bull_count:
            score = max(-80, -(bear_count * 6))
        return score, confidence

    def _build_report(
        self,
        analysis_text: str,
        raw_data: dict = None,
        context: dict = None,
        use_technical_score: bool = False,
    ) -> AgentReport:
        # Score
        if use_technical_score and context:
            tech_score = self._compute_technical_score(context)
            score = tech_score if tech_score is not None else self._parse_score_from_text(analysis_text)[0]
        else:
            score, _ = self._parse_score_from_text(analysis_text)

        # Confiance dynamique
        confidence = self._compute_confidence(analysis_text, context or {})

        # Points clés
        key_points = []
        for line in analysis_text.split("\n"):
            line = line.strip()
            if line.startswith(("-", "•", "*", "→")) and len(line) > 5:
                key_points.append(line.lstrip("-•*→ "))
        if not key_points:
            sentences = [s.strip() for s in analysis_text.split(".") if len(s.strip()) > 20]
            key_points = sentences[:3]

        return AgentReport(
            agent_name=self.name,
            agent_role=self.role,
            timestamp=datetime.now().isoformat(),
            analysis=analysis_text,
            key_points=key_points[:5],
            score=score,
            confidence=confidence,
            raw_data=raw_data or {},
        )

    @abstractmethod
    def analyze(self, asset: str, context: dict) -> AgentReport:
        pass

    def __del__(self):
        try:
            self._client.close()
        except:
            pass
