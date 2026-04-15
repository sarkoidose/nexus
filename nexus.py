#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║         ⚡ NEXUS — Multi-Agent Financial Intelligence ⚡      ║
║      FUNDAMENTUM · MACRO · TECHNICUS · SENTINEL · APEX      ║
╚══════════════════════════════════════════════════════════════╝

Lancement : python nexus.py
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.columns import Columns
from rich.align import Align
from rich import box

from core.orchestrator import NexusOrchestrator
from tui.display import (
    render_header, render_market_snapshot, render_agent_report,
    render_decision, render_menu, save_analysis, console,
    render_portfolio_table, prompt_portfolio_tickers,
)
from config.settings import ASSET_CLASSES

orchestrator     = NexusOrchestrator()
analysis_history: list[dict] = []


# ─────────────────────────────────────────────────────────────
# SPLASH
# ─────────────────────────────────────────────────────────────

def splash_screen():
    console.clear()
    console.print()
    logo = """
  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
"""
    console.print(Align.center(f"[bold yellow]{logo}[/bold yellow]"))
    console.print(Align.center("[dim]Multi-Agent Financial Intelligence System[/dim]"))
    console.print(Align.center("[dim]FUNDAMENTUM · MACRO · TECHNICUS · SENTINEL · APEX[/dim]"))
    console.print()

    with Progress(SpinnerColumn(), TextColumn("[bold cyan]{task.description}"),
                  console=console, transient=True) as progress:
        task = progress.add_task("Vérification du système...", total=None)
        progress.update(task, description="🔍 Vérification Ollama...")
        time.sleep(0.3)
        ollama_ok, models = orchestrator.check_ollama()
        progress.update(task, description="✅ Système prêt")
        time.sleep(0.3)

    status_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    status_table.add_column(width=20)
    status_table.add_column()

    ollama_status = (f"[green]✓ OK[/green] ({', '.join(models[:3]) if models else 'connecté'})"
                     if ollama_ok else "[red]✗ Hors ligne[/red] (lancer: ollama serve)")
    status_table.add_row("[dim]Ollama (local)[/dim]",  ollama_status)
    status_table.add_row("[dim]Agents[/dim]",           "[green]✓ 5 agents initialisés[/green]")
    status_table.add_row("[dim]News RSS[/dim]",         "[green]✓ Yahoo Finance RSS[/green]")
    status_table.add_row("[dim]Mode Portefeuille[/dim]","[green]✓ Disponible[/green]")

    console.print(Panel(
        Align.center(status_table),
        title="[bold]Statut Système[/bold]",
        border_style="bright_black",
        width=70,
    ))
    console.print()


# ─────────────────────────────────────────────────────────────
# MENU PRINCIPAL (mise à jour avec option portefeuille)
# ─────────────────────────────────────────────────────────────

def render_main_menu() -> Panel:
    items = [
        ("1", "Analyser un actif",           "cyan"),
        ("2", "Portefeuille multi-actifs",   "green"),
        ("3", "Historique des analyses",     "blue"),
        ("4", "Tester la connexion Ollama",  "yellow"),
        ("Q", "Quitter",                     "red"),
    ]
    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_column(style="bold white", width=6)
    table.add_column()
    for key, label, color in items:
        table.add_row(f"[{color}][{key}][/{color}]", f"[{color}]{label}[/{color}]")
    return Panel(table, title="[bold]⚡ Menu Principal NEXUS[/bold]", border_style="bright_black")


# ─────────────────────────────────────────────────────────────
# FLUX ANALYSE UNIQUE
# ─────────────────────────────────────────────────────────────

def select_asset_class() -> str:
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column(style="bold yellow", width=4)
    table.add_column()
    table.add_column(style="dim")

    rows = [
        ("1", "Actions & Marchés globaux",   "TSMC, AAPL, NVDA, ASML..."),
        ("2", "Cryptomonnaies",              "BTC, ETH, SOL, ARB..."),
        ("3", "Matières premières (ETFs)",   "GLD, SLV, USO..."),
        ("4", "Macro / ETFs / Obligations",  "TLT, SPY, QQQ..."),
        ("A", "Détection automatique",       ""),
    ]
    for key, label, ex in rows:
        table.add_row(f"[{key}]", label, ex)

    console.print(Panel(table, title="[bold]Classe d'actif[/bold]", border_style="bright_black"))
    choice = Prompt.ask("Choix", choices=["1","2","3","4","A","a"], default="A")
    mapping = {"1":"equity","2":"crypto","3":"commodities","4":"macro","A":"auto","a":"auto"}
    return mapping.get(choice.upper(), "auto")


def run_analysis_flow():
    console.print()
    console.print(render_header())
    console.print()

    ticker = Prompt.ask(
        "[bold cyan]Ticker / Symbole[/bold cyan] [dim](ex: TSMC, BTC, NVDA)[/dim]"
    ).upper().strip()
    if not ticker:
        return

    console.print()
    asset_class = select_asset_class()
    console.print()

    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold cyan]{task.description:<45}"),
        BarColumn(bar_width=25, complete_style="yellow", finished_style="green"),
        TextColumn("[dim]{task.percentage:>3.0f}%[/dim]"),
        console=console, transient=False,
    ) as progress:
        task = progress.add_task(f"⚡ Analyse NEXUS — {ticker}", total=100)
        def cb(msg, pct):
            progress.update(task, description=msg, completed=pct)
        snapshot, reports, decision = orchestrator.run_analysis(
            asset=ticker, asset_class=asset_class, progress_callback=cb,
        )

    console.print()
    console.print(Rule("[bold yellow]⚡ RÉSULTATS NEXUS[/bold yellow]", style="yellow"))
    console.print()

    if snapshot:
        console.print(render_market_snapshot(snapshot))
        console.print()

    # News récentes si disponibles
    if snapshot and snapshot.recent_news:
        news_text = Text()
        news_text.append("  Actualités récentes :\n", style="bold dim")
        for h in snapshot.recent_news[:5]:
            news_text.append(f"  • {h}\n", style="dim")
        console.print(Panel(news_text, title="📰 News Yahoo Finance", border_style="bright_black"))
        console.print()

    console.print("[bold dim]── Rapports des Agents Spécialisés ──[/bold dim]")
    console.print()

    panels = [render_agent_report(reports[n], expanded=False)
              for n in ["fundamentum","macro","technicus","sentinel"] if n in reports]
    if len(panels) >= 2:
        console.print(Columns([panels[0], panels[1]], equal=True, expand=True))
    if len(panels) >= 4:
        console.print(Columns([panels[2], panels[3]], equal=True, expand=True))

    console.print()
    if decision:
        console.print(render_decision(decision))
        console.print()

    post_menu(ticker, snapshot, reports, decision)


# ─────────────────────────────────────────────────────────────
# MODE PORTEFEUILLE
# ─────────────────────────────────────────────────────────────

def run_portfolio_flow():
    console.print()
    console.print(render_header())
    console.print()

    tickers = prompt_portfolio_tickers()
    if not tickers:
        return

    console.print()
    console.print(f"[dim]Analyse de {len(tickers)} actif(s) : {', '.join(tickers)}[/dim]")
    console.print()

    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold cyan]{task.description:<50}"),
        BarColumn(bar_width=25, complete_style="yellow", finished_style="green"),
        TextColumn("[dim]{task.percentage:>3.0f}%[/dim]"),
        console=console, transient=False,
    ) as progress:
        task = progress.add_task("📊 Analyse Portefeuille...", total=100)
        def cb(msg, pct):
            progress.update(task, description=msg, completed=pct)
        results = orchestrator.run_portfolio(tickers=tickers, progress_callback=cb)

    console.print()
    console.print(Rule("[bold yellow]⚡ RÉSULTATS PORTEFEUILLE[/bold yellow]", style="yellow"))
    console.print()
    console.print(render_portfolio_table(results))
    console.print()

    # Options post-portefeuille
    console.print("[dim][N] Nouvelle analyse  [Q] Quitter[/dim]")
    choice = Prompt.ask("", choices=["N","n","Q","q"], default="N")
    if choice.upper() == "Q":
        sys.exit(0)


# ─────────────────────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────────────────────

def post_menu(asset, snapshot, reports, decision):
    while True:
        console.print()
        t = Text()
        t.append("[D] ", style="cyan");   t.append("Détail agent  ", style="dim")
        t.append("[S] ", style="green");  t.append("Sauvegarder  ", style="dim")
        t.append("[N] ", style="yellow"); t.append("Nouvelle analyse  ", style="dim")
        t.append("[Q] ", style="red");    t.append("Menu principal", style="dim")
        console.print(t)
        choice = Prompt.ask("", choices=["D","d","S","s","N","n","Q","q"], default="N").upper()

        if choice == "D":
            ag = Prompt.ask("Agent [F/M/T/S]", choices=["F","M","T","S"], default="F")
            name = {"F":"fundamentum","M":"macro","T":"technicus","S":"sentinel"}[ag]
            if name in reports:
                console.print()
                console.print(render_agent_report(reports[name], expanded=True))
                console.print(Panel(
                    reports[name].analysis,
                    title=f"[bold]Analyse complète — {reports[name].agent_name}[/bold]",
                    border_style="dim",
                ))
        elif choice == "S":
            if decision:
                fp = save_analysis(asset, decision, reports, snapshot)
                console.print(f"[green]✓ Sauvegardé : {fp}[/green]")
                analysis_history.append({
                    "asset": asset, "timestamp": decision.timestamp,
                    "recommendation": decision.recommendation,
                    "conviction": decision.conviction, "filepath": fp,
                })
        elif choice == "N":
            return
        elif choice == "Q":
            sys.exit(0)


def view_history():
    output_dir = os.path.join(ROOT, "outputs")
    files = []
    if os.path.exists(output_dir):
        files = sorted(Path(output_dir).glob("nexus_*.json"), reverse=True)[:10]

    if not files and not analysis_history:
        console.print("[dim]Aucun historique disponible.[/dim]")
        return

    table = Table(
        title="[bold]Historique des Analyses[/bold]",
        box=box.SIMPLE_HEAVY, border_style="yellow",
    )
    table.add_column("Date",      style="dim")
    table.add_column("Actif",     style="bold")
    table.add_column("Décision",  justify="center")
    table.add_column("Conviction",justify="right")

    for f in files:
        try:
            with open(f) as fp:
                data = json.load(fp)
            dec = data.get("decision", {})
            rec = dec.get("recommendation", "?")
            style = "green" if rec in ("BUY","ACCUMULATE") else ("red" if rec in ("SELL","AVOID") else "yellow")
            ts = data.get("timestamp","")[:16].replace("T"," ")
            table.add_row(ts, data.get("asset","?"), f"[{style}]{rec}[/{style}]", f"{dec.get('conviction',0)}%")
        except (OSError, json.JSONDecodeError, KeyError):
            continue
    console.print(table)


def test_ollama():
    console.print()
    ok, models = orchestrator.check_ollama()
    if ok:
        console.print(f"[green]✓ Ollama accessible[/green]")
        for m in models:
            console.print(f"  → {m}")
    else:
        console.print("[red]✗ Ollama inaccessible[/red]")
        console.print("[dim]Lancer: [bold]ollama serve[/bold][/dim]")
    console.print()
    Prompt.ask("[dim]Entrée pour continuer[/dim]", default="")


# ─────────────────────────────────────────────────────────────
# BOUCLE PRINCIPALE
# ─────────────────────────────────────────────────────────────

def main():
    splash_screen()
    try:
        while True:
            console.print()
            console.print(render_main_menu())
            choice = Prompt.ask(
                "[bold]Commande[/bold]",
                choices=["1","2","3","4","Q","q"],
                default="1",
            )
            if choice == "1":
                run_analysis_flow()
            elif choice == "2":
                run_portfolio_flow()
            elif choice == "3":
                console.print()
                view_history()
                Prompt.ask("[dim]Entrée pour continuer[/dim]", default="")
            elif choice == "4":
                test_ollama()
            elif choice.upper() == "Q":
                console.print()
                console.print("[bold yellow]⚡ NEXUS — À bientôt.[/bold yellow]")
                console.print()
                return
    finally:
        # Fermeture propre des pools HTTP partagés (agents + fetcher).
        try:
            orchestrator.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
