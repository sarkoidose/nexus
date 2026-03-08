"""
NEXUS - Interface TUI (Terminal User Interface)
Dashboard financier multi-agents avec Rich
"""

import sys
import os
import json
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from rich.rule import Rule
from rich.prompt import Prompt
from rich.columns import Columns
from rich import box
from rich.align import Align

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

console = Console()

# ─────────────────────────────────────────────
# PALETTE NEXUS
# ─────────────────────────────────────────────
NEXUS_GOLD  = "bold yellow"
NEXUS_CYAN  = "bold cyan"
NEXUS_GREEN = "bold green"
NEXUS_RED   = "bold red"
NEXUS_DIM   = "dim white"


def render_header() -> Panel:
    agents_line = Text()
    agents_line.append("  ⚡ APEX",        style="yellow")
    agents_line.append("  ·  ",            style="dim")
    agents_line.append("📊 FUNDAMENTUM",   style="cyan")
    agents_line.append("  ·  ",            style="dim")
    agents_line.append("🌍 MACRO",         style="blue")
    agents_line.append("  ·  ",            style="dim")
    agents_line.append("📈 TECHNICUS",     style="green")
    agents_line.append("  ·  ",            style="dim")
    agents_line.append("🛡️ SENTINEL",      style="red")

    return Panel(
        Align.center(agents_line),
        title="[bold yellow]⚡ N E X U S[/bold yellow]",
        subtitle=f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        border_style="yellow",
        padding=(0, 2),
    )


def render_market_snapshot(snapshot) -> Panel:
    if snapshot is None:
        return Panel("[dim]Aucune donnée[/dim]", title="📡 Marché", border_style="bright_black")

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)

    change_24h_style = "bold green" if snapshot.price_24h_change_pct >= 0 else "bold red"
    change_sign = "▲" if snapshot.price_24h_change_pct >= 0 else "▼"

    left_lines = Text()
    left_lines.append(f"{snapshot.name} ({snapshot.ticker})\n", style="bold white")
    left_lines.append(f"Classe : {snapshot.asset_class.upper()}\n", style="dim")
    left_lines.append(f"Prix   : ", style="bold")
    left_lines.append(f"{snapshot.price:,.4f} {snapshot.currency}\n", style="bold white")
    left_lines.append(f"24h    : {change_sign} {abs(snapshot.price_24h_change_pct):.2f}%\n", style=change_24h_style)
    left_lines.append(f"7j     : {snapshot.price_7d_change_pct:+.2f}%\n",
                      style="green" if snapshot.price_7d_change_pct >= 0 else "red")
    left_lines.append(f"30j    : {snapshot.price_30d_change_pct:+.2f}%",
                      style="green" if snapshot.price_30d_change_pct >= 0 else "red")

    right_lines = Text()
    if snapshot.market_cap:
        right_lines.append(f"Mkt Cap : ${snapshot.market_cap/1e9:.2f}B\n", style="dim")
    if snapshot.volume_24h:
        right_lines.append(f"Vol 24h : ${snapshot.volume_24h/1e6:.1f}M\n", style="dim")
    if snapshot.pe_ratio:
        right_lines.append(f"P/E     : {snapshot.pe_ratio:.1f}\n")
    if snapshot.rsi_14:
        rsi_style = "red" if snapshot.rsi_14 > 70 else ("green" if snapshot.rsi_14 < 30 else "white")
        right_lines.append(f"RSI(14) : {snapshot.rsi_14:.1f}\n", style=rsi_style)
    if snapshot.sma_50:
        above = snapshot.price > snapshot.sma_50
        right_lines.append(f"SMA50   : {snapshot.sma_50:.2f} {'↑' if above else '↓'}\n",
                           style="green" if above else "red")
    if snapshot.week_52_high:
        pct_from_high = (snapshot.price / snapshot.week_52_high - 1) * 100
        right_lines.append(f"52s Max : {snapshot.week_52_high:.2f} ({pct_from_high:+.1f}%)")

    grid.add_row(left_lines, right_lines)

    return Panel(
        grid,
        title=f"[bold cyan]📡 {snapshot.name} — Données Marché[/bold cyan]",
        border_style="cyan",
        padding=(0, 1),
    )


def render_agent_report(report, expanded: bool = False) -> Panel:
    """Panel rapport d'un agent spécialisé."""
    from config.settings import AGENTS
    cfg = AGENTS.get(report.agent_name.lower(), None)
    emoji = cfg.emoji if cfg else "🤖"
    color = cfg.color if cfg else "white"
    bare_color = color.replace("bold ", "")

    if report.error:
        return Panel(
            Text(f"⚠️ Erreur: {report.error}", style="red"),
            title=f"[{bare_color}]{emoji} {report.agent_name}[/{bare_color}]",
            border_style="red",
        )

    score = report.score
    score_bar_width = 20
    filled = int(abs(score) / 100 * score_bar_width)
    empty  = score_bar_width - filled
    bar_color = "green" if score >= 0 else "red"

    content = Text()
    # Score
    content.append("Score: ", style="dim")
    content.append(f"{score:+d}", style=f"bold {bar_color}")
    content.append(f" / Confiance: {report.confidence}%\n", style="dim")
    # Barre
    content.append("[", style="dim")
    content.append("█" * filled, style=f"bold {bar_color}")
    content.append("░" * empty, style="dim")
    content.append("]\n\n", style="dim")

    if report.key_points:
        content.append("Points clés :\n", style="bold")
        for kp in report.key_points[:3]:
            # Nettoyer le markdown résiduel (**)
            clean = kp.replace("**", "").replace("*", "").strip()
            if clean:
                content.append(f"  → {clean[:120]}\n", style="dim white")

    if expanded and report.analysis:
        content.append("\nAnalyse complète :\n", style="bold dim")
        analysis_short = report.analysis[:800]
        if len(report.analysis) > 800:
            analysis_short += "..."
        # Nettoyer markdown
        clean_analysis = analysis_short.replace("**", "").replace("*", "")
        content.append(clean_analysis, style="dim")

    return Panel(
        content,
        title=f"[{bare_color}]{emoji} {report.agent_name} — {report.agent_role}[/{bare_color}]",
        border_style=bare_color,
        padding=(0, 1),
    )


def render_decision(decision) -> Panel:
    """Panel décision finale APEX."""
    rec = decision.recommendation
    rec_colors = {
        "BUY":        "bold green",
        "ACCUMULATE": "green",
        "HOLD":       "bold yellow",
        "AVOID":      "bold red",
        "SELL":       "red",
    }
    rec_icons = {
        "BUY":        "🟢 BUY",
        "ACCUMULATE": "🟩 ACCUMULATE",
        "HOLD":       "🟡 HOLD",
        "AVOID":      "🔴 AVOID",
        "SELL":       "🔴 SELL",
    }
    rec_color = rec_colors.get(rec, "white")
    bare_rec_color = rec_color.replace("bold ", "")

    conv = decision.conviction
    conv_filled = int(conv / 100 * 30)
    conv_bar_filled = "█" * conv_filled
    conv_bar_empty  = "░" * (30 - conv_filled)

    content = Text()
    content.append(f"  {rec_icons.get(rec, rec)}\n", style=rec_color)
    content.append("  Conviction : ", style="dim")
    content.append(f"{conv}% ", style="bold white")
    content.append("[", style="dim")
    content.append(conv_bar_filled, style=f"bold {bare_rec_color}")
    content.append(conv_bar_empty, style="dim")
    content.append("]\n\n", style="dim")

    content.append(f"  Horizon    : {decision.time_horizon}\n")

    if decision.entry_price:
        content.append(f"  Entrée     : {decision.entry_price:,.4f}\n", style="cyan")
    if decision.stop_loss:
        content.append(f"  Stop-Loss  : {decision.stop_loss:,.4f}\n", style="red")
    if decision.target_price:
        ep = decision.entry_price or 0
        sl = decision.stop_loss or 0
        risk = abs(ep - sl)
        rr = (decision.target_price - ep) / max(risk, 0.001)
        content.append(f"  Objectif   : {decision.target_price:,.4f} (R/R ≈ {rr:.1f}x)\n", style="green")

    content.append(f"  Taille pos.: {decision.position_size_pct:.1f}% du portefeuille\n\n")

    content.append("  Synthèse :\n", style="bold")
    synthesis = decision.synthesis.replace("**", "").replace("*", "")
    content.append(f"  {synthesis}\n\n", style="italic dim white")

    if decision.catalysts:
        content.append("  Catalyseurs :\n", style="bold green")
        for c in decision.catalysts:
            content.append(f"    + {c}\n", style="green")

    if decision.risks:
        content.append("\n  Risques :\n", style="bold red")
        for r in decision.risks:
            content.append(f"    - {r}\n", style="red")

    content.append("\n  Scores agents :\n", style="bold dim")
    for agent, scores in decision.agent_scores.items():
        s = scores.get("score", 0)
        style = "green" if s > 0 else ("red" if s < 0 else "yellow")
        content.append(f"    {agent.upper():12s} : ", style="dim")
        content.append(f"{s:+4d}", style=f"bold {style}")
        content.append(f" / conf {scores.get('confidence', 0)}%\n", style="dim")

    return Panel(
        content,
        title="[bold yellow]⚡ APEX — DÉCISION FINALE[/bold yellow]",
        border_style="yellow",
        padding=(0, 1),
    )


def render_menu() -> Panel:
    items = [
        ("1", "Analyser un actif",         "cyan"),
        ("2", "Historique des analyses",   "blue"),
        ("3", "Tester la connexion Ollama","yellow"),
        ("Q", "Quitter",                   "red"),
    ]
    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_column(style="bold white", width=6)
    table.add_column()
    for key, label, color in items:
        table.add_row(f"[{color}][{key}][/{color}]", f"[{color}]{label}[/{color}]")
    return Panel(table, title="[bold]Menu Principal[/bold]", border_style="bright_black")


def display_progress_analysis(asset: str) -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=30),
        console=console,
        transient=False,
    )


def save_analysis(asset: str, decision, reports: dict, snapshot):
    """Sauvegarde une analyse en JSON."""
    output_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"nexus_{asset}_{timestamp}.json"
    filepath  = os.path.join(output_dir, filename)

    data = {
        "asset":        asset,
        "timestamp":    decision.timestamp,
        "decision":     decision.to_dict(),
        "snapshot":     snapshot.to_context_dict() if snapshot else {},
        "agent_reports": {
            name: report.to_dict()
            for name, report in reports.items()
            if not report.error
        },
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    return filepath
