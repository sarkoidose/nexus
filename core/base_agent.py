"""
NEXUS - Classe de Base des Agents
100% LOCAL — Backend Ollama uniquement
"""
import httpx
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
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
            "prompt": f"Date du jour: {datetime.now().strftime('%d %B %Y')}\n\n{self.config.system_prompt}\n\n{prompt}",
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
            raise RuntimeError(
                f"Ollama inaccessible sur {OLLAMA_BASE_URL}\n"
                "Lance : ollama serve"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404 and model != OLLAMA_MODEL_FALLBACK:
                return self._call_ollama(prompt, OLLAMA_MODEL_FALLBACK)
            raise RuntimeError(f"Erreur Ollama HTTP {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Erreur Ollama: {e}")

    def _llm_call(self, prompt: str) -> str:
        return self._call_ollama(prompt)

    def _parse_score_from_text(self, text: str) -> tuple[int, int]:
        score = 0
        confidence = 50
        text_lower = text.lower()
        bullish = ["haussier", "positif", "favorable", "acheter", "buy", "fort", "solide", "bullish", "hausse"]
        bearish = ["baissier", "négatif", "défavorable", "vendre", "sell", "faible", "fragile", "bearish", "baisse"]
        bull_count = sum(1 for kw in bullish if kw in text_lower)
        bear_count = sum(1 for kw in bearish if kw in text_lower)
        if bull_count > bear_count:
            score = min(80, bull_count * 12)
        elif bear_count > bull_count:
            score = max(-80, -(bear_count * 12))
        return score, confidence

    def _build_report(self, analysis_text: str, raw_data: dict = None) -> AgentReport:
        score, confidence = self._parse_score_from_text(analysis_text)
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
