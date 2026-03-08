#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║         ⚡ NEXUS — Multi-Agent Financial Intelligence ⚡     ║
║      FUNDAMENTUM · MACRO · TECHNICUS · SENTINEL · APEX       ║
╚══════════════════════════════════════════════════════════════╝
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
from rich.align import Align
from rich import box

from core.orchestrator import NexusOrchestrator
from tui.display import (
    render_header, render_market_snapshot, render_agent_report,
    render_decision, render_menu, save_analysis, console
)
from config.settings import ASSET_CLASSES

orchestrator     = NexusOrchestrator()
analysis_history = []


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
        time.sleep(0.3)
        progress.update(task, description="🔍 Vérification Ollama...")
        ollama_ok, models = orchestrator.check_ollama()
        time.sleep(0.3)
        progress.update(task, description="✅ Système prêt")
        time.sleep(0.3)

    status = Table(box=None, show_header=False, padding=(0, 2))
    status.add_column(width=20)
    status.add_column()

    ollama_status = (f"[green]✓ OK[/green] ({', '.join(models[:3])})" if models
                     else "[green]✓ Connecté[/green]") if ollama_ok \
                    else "[red]✗ Hors ligne[/red] → lancer: ollama serve"

    status.add_row("[dim]Ollama[/dim]",  ollama_status)
    status.add_row("[dim]APEX[/dim]",    "[green]✓ qwen3.5:35b-a3b[/green]")
    status.add_row("[dim]Agents[/dim]",  "[green]✓ qwen3.5:9b × 4[/green]")

    console.print(Panel(Align.center(status), title="[bold]Statut Système[/bold]",
                        border_style="bright_black", width=60))
    console.print()


def select_asset_class() -> str:
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column(style="bold yellow", width=4)
    table.add_column()
    table.add_column(style="dim")
    for key, label, ex in [
        ("1", "Actions & Marchés globaux",    "TSMC, NVDA, AAPL, ASML..."),
        ("2", "Cryptomonnaies",               "BTC, ETH, SOL, ARB..."),
        ("3", "Matières premières (ETFs)",    "GLD, SLV, USO..."),
        ("4", "Macro / ETFs / Obligations",   "TLT, SPY, QQQ..."),
        ("A", "Détection automatique",        ""),
    ]:
        table.add_row(f"[{key}]", label, ex)
    console.print(Panel(table, title="[bold]Classe d'actif[/bold]", border_style="bright_black"))
    choice = Prompt.ask("Choix", choices=["1","2","3","4","A","a"], default="A")
    return {"1":"equity","2":"crypto","3":"commodities","4":"macro","A":"auto","a":"auto"}[choice.upper()]


def run_analysis_flow():
    console.print()
    console.print(render_header())
    console.print()

    ticker = Prompt.ask("[bold cyan]Ticker[/bold cyan] [dim](ex: NVDA, BTC, GLD)[/dim]").upper().strip()
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
        console=console,
    ) as progress:
        task = progress.add_task(f"⚡ Analyse NEXUS — {ticker}", total=100)

        def update(msg, pct):
            progress.update(task, description=msg, completed=pct)

        snapshot, reports, decision = orchestrator.run_analysis(
            asset=ticker, asset_class=asset_class, progress_callback=update
        )

    console.print()
    from rich.rule import Rule
    console.print(Rule("[bold yellow]⚡ RÉSULTATS NEXUS[/bold yellow]", style="yellow"))
    console.print()

    if snapshot:
        console.print(render_market_snapshot(snapshot))
        console.print()

    from rich.columns import Columns
    panels = [render_agent_report(reports[n]) for n in ["fundamentum","macro","technicus","sentinel"] if n in reports]
    if len(panels) >= 2:
        console.print(Columns([panels[0], panels[1]], equal=True, expand=True))
    if len(panels) >= 4:
        console.print(Columns([panels[2], panels[3]], equal=True, expand=True))

    console.print()
    if decision:
        console.print(render_decision(decision))
        console.print()

    post_menu(ticker, snapshot, reports, decision)


def post_menu(asset, snapshot, reports, decision):
    while True:
        console.print()
        t = Text()
        t.append("[D] ", style="cyan");  t.append("Détail agent  ", style="dim")
        t.append("[S] ", style="green"); t.append("Sauvegarder  ", style="dim")
        t.append("[N] ", style="yellow"); t.append("Nouvelle analyse  ", style="dim")
        t.append("[Q] ", style="red");   t.append("Quitter", style="dim")
        console.print(t)
        choice = Prompt.ask("", choices=["D","d","S","s","N","n","Q","q"], default="N").upper()

        if choice == "D":
            a = Prompt.ask("Agent [F]undamentum [M]acro [T]echnicus [S]entinel",
                           choices=["F","M","T","S"], default="F")
            name = {"F":"fundamentum","M":"macro","T":"technicus","S":"sentinel"}[a]
            if name in reports:
                console.print()
                console.print(render_agent_report(reports[name], expanded=True))
        elif choice == "S":
            if decision:
                fp = save_analysis(asset, decision, reports, snapshot)
                console.print(f"[green]✓ Sauvegardé : {fp}[/green]")
                analysis_history.append({"asset": asset, "recommendation": decision.recommendation,
                                          "conviction": decision.conviction, "filepath": fp})
        elif choice == "N":
            return
        elif choice == "Q":
            console.print("\n[bold yellow]⚡ NEXUS — À bientôt.[/bold yellow]\n")
            sys.exit(0)


def view_history():
    output_dir = os.path.join(ROOT, "outputs")
    if os.path.exists(output_dir):
        files = sorted(Path(output_dir).glob("nexus_*.json"), reverse=True)[:10]
        if files:
            table = Table(title="[bold]Historique[/bold]", box=box.SIMPLE_HEAVY, border_style="yellow")
            table.add_column("Date", style="dim")
            table.add_column("Actif", style="bold")
            table.add_column("Décision", justify="center")
            table.add_column("Conviction", justify="right")
            for f in files:
                try:
                    data = json.loads(f.read_text())
                    dec  = data.get("decision", {})
                    rec  = dec.get("recommendation", "?")
                    style = "green" if rec in ("BUY","ACCUMULATE") else ("red" if rec in ("SELL","AVOID") else "yellow")
                    table.add_row(data.get("timestamp","")[:16].replace("T"," "), data.get("asset","?"),
                                  f"[{style}]{rec}[/{style}]", f"{dec.get('conviction',0)}%")
                except:
                    pass
            console.print(table)
            return
    console.print("[dim]Aucun historique disponible.[/dim]")


def test_ollama():
    console.print()
    ok, models = orchestrator.check_ollama()
    if ok:
        console.print("[green]✓ Ollama accessible[/green]")
        for m in models:
            console.print(f"  → {m}")
    else:
        console.print("[red]✗ Ollama inaccessible[/red]")
        console.print("[dim]Lancer : [bold]ollama serve[/bold][/dim]")
    console.print()
    Prompt.ask("[dim]Entrée pour continuer[/dim]", default="")


def main():
    splash_screen()
    while True:
        console.print()
        console.print(render_menu())
        choice = Prompt.ask("[bold]Commande[/bold]", choices=["1","2","3","Q","q"], default="1").upper()
        if choice == "1":
            run_analysis_flow()
        elif choice == "2":
            console.print()
            view_history()
            Prompt.ask("[dim]Entrée pour continuer[/dim]", default="")
        elif choice == "3":
            test_ollama()
        elif choice == "Q":
            console.print("\n[bold yellow]⚡ NEXUS — À bientôt.[/bold yellow]\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
