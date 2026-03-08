"""
NEXUS - APEX : Orchestrateur & Décideur Final
100% LOCAL — qwen3.5:9b via Ollama
"""
import json
import sys
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.base_agent import BaseAgent, AgentReport
from config.settings import AGENTS, OLLAMA_MODEL_APEX, OLLAMA_BASE_URL


@dataclass
class NexusDecision:
    asset: str
    timestamp: str
    recommendation: str
    conviction: int
    time_horizon: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    target_price: Optional[float]
    position_size_pct: float
    synthesis: str
    risks: list[str]
    catalysts: list[str]
    agent_scores: dict
    apex_reasoning: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class ApexAgent(BaseAgent):

    def __init__(self):
        super().__init__(AGENTS["apex"])

    def analyze(self, asset: str, context: dict) -> AgentReport:
        pass

    def synthesize(
        self,
        asset: str,
        snapshot_summary: str,
        reports: dict[str, AgentReport],
        price: float = 0.0,
    ) -> NexusDecision:

        reports_text = ""
        agent_scores = {}

        for agent_name, report in reports.items():
            if report.error:
                reports_text += f"\n### {report.agent_name}\nERREUR: {report.error}\n"
                continue
            kp = "\n".join(f"  - {k}" for k in report.key_points)
            reports_text += (
                f"\n### {report.agent_name} ({report.agent_role})\n"
                f"Score: {report.score:+d}/100 | Confiance: {report.confidence}%\n"
                f"Points clés:\n{kp}\n"
                f"Analyse:\n{report.analysis[:400]}\n"
            )
            agent_scores[agent_name] = {"score": report.score, "confidence": report.confidence}

        prompt = (
            "Tu es APEX, orchestrateur financier.\n\n"
            "DONNEES MARCHE:\n"
            f"{snapshot_summary}\n\n"
            "RAPPORTS AGENTS:\n"
            f"{reports_text}\n\n"
            "REGLE ABSOLUE: Ta reponse doit etre UNIQUEMENT du JSON valide.\n"
            "Pas de texte avant. Pas de texte apres. Pas de markdown.\n"
            "Commence par { et termine par }.\n\n"
            "{\n"
            '  "recommendation": "HOLD",\n'
            '  "conviction": 50,\n'
            '  "time_horizon": "MT",\n'
            f'  "entry_price": {price if price > 0 else "null"},\n'
            '  "stop_loss": null,\n'
            '  "target_price": null,\n'
            '  "position_size_pct": 2.0,\n'
            '  "synthesis": "synthese ici",\n'
            '  "risks": ["risque1", "risque2"],\n'
            '  "catalysts": ["catalyseur1"],\n'
            '  "apex_reasoning": "raisonnement ici"\n'
            "}"
        )

        raw = ""
        try:
            _resp = self._client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL_APEX,
                    "prompt": prompt,
                    "stream": False,
                    "think": False,
                    "options": {
                        "num_predict": 1024,
                        "temperature": 0.1,
                        "num_ctx": 4096,
                    }
                },
                timeout=600.0,
            )
            _d = _resp.json()
            raw = _d.get("response", "") or _d.get("thinking", "")

            json_str = raw.strip()
            for fence in ["```json", "```"]:
                if fence in json_str:
                    json_str = json_str.split(fence)[1].split("```")[0].strip()
                    break

            start = json_str.find("{")
            end   = json_str.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = json_str[start:end]

            data = json.loads(json_str)

            return NexusDecision(
                asset=asset,
                timestamp=datetime.now().isoformat(),
                recommendation=data.get("recommendation", "HOLD"),
                conviction=int(data.get("conviction", 50)),
                time_horizon=data.get("time_horizon", "MT"),
                entry_price=data.get("entry_price"),
                stop_loss=data.get("stop_loss"),
                target_price=data.get("target_price"),
                position_size_pct=float(data.get("position_size_pct", 2.0)),
                synthesis=data.get("synthesis", ""),
                risks=data.get("risks", []),
                catalysts=data.get("catalysts", []),
                agent_scores=agent_scores,
                apex_reasoning=data.get("apex_reasoning", ""),
            )

        except Exception as e:
            return NexusDecision(
                asset=asset,
                timestamp=datetime.now().isoformat(),
                recommendation="HOLD",
                conviction=30,
                time_horizon="MT",
                entry_price=price if price > 0 else None,
                stop_loss=None,
                target_price=None,
                position_size_pct=2.0,
                synthesis=f"Synthèse indisponible: {str(e)[:100]}",
                risks=["Analyse APEX incomplète"],
                catalysts=[],
                agent_scores=agent_scores,
                apex_reasoning=raw[:500] if raw else "",
            )
