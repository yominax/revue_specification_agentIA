"""Interface en ligne de commande pour la revue de spécifications."""
import argparse
import sys
from pathlib import Path
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import settings
from src.workflow import ValidationWorkflow

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


def print_banner():
    """Affiche la bannière."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║     Assistant GenAI pour la Revue de Spécifications         ║
    ║     Analyse Automatisée de Documents Techniques              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def check_setup():
    """Vérifie la configuration."""
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        console.print("[bold red]❌ Erreur:[/bold red] Clé API OpenAI non configurée")
        console.print("Veuillez créer un fichier .env avec votre OPENAI_API_KEY")
        return False
    if not settings.documents_path.exists():
        settings.documents_path.mkdir(parents=True, exist_ok=True)
        console.print(f"[yellow]⚠[/yellow]  Dossier documents créé: {settings.documents_path}")
    return True


def cmd_init(args):
    """Initialise le workflow"""
    console.print("[bold]Initialisation du workflow...[/bold]")
    workflow = ValidationWorkflow()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Initialisation...", total=None)
        workflow.initialize(rebuild_vector_store=args.rebuild)
        progress.update(task, completed=True)
    console.print("[bold green]✅ Workflow initialisé avec succès![/bold green]")


def cmd_review(args):
    """Exécute une revue complète"""
    console.print("[bold]Démarrage de la revue des spécifications...[/bold]")
    workflow = ValidationWorkflow()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task1 = progress.add_task("Chargement du workflow...", total=None)
        workflow.initialize()
        progress.update(task1, completed=True)
        task2 = progress.add_task("Analyse en cours...", total=None)
        custom_questions = args.questions.split(";") if args.questions else None
        report = workflow.run_full_review(custom_questions=custom_questions, output_file=args.output)
        progress.update(task2, completed=True)
    console.print("\n[bold green]✅ Analyse terminée![/bold green]\n")
    resume_table = Table(title="Résumé de l'Analyse")
    resume_table.add_column("Métrique", style="cyan")
    resume_table.add_column("Valeur", style="green")
    resume_table.add_row("Documents analysés", str(report['resume']['nombre_documents']))
    resume_table.add_row("Chunks analysés", str(report['resume']['nombre_chunks_analyses']))
    if "statistiques" in report:
        stats = report["statistiques"]
        resume_table.add_row("Total problèmes", str(stats.get('total_problemes', 0)))
        resume_table.add_row("Critiques", str(stats.get('problemes_critiques', 0)), style="red")
        resume_table.add_row("Majeurs", str(stats.get('problemes_majeurs', 0)), style="yellow")
        resume_table.add_row("Mineurs", str(stats.get('problemes_mineurs', 0)), style="green")
    console.print(resume_table)
    if "analyse" in report and isinstance(report["analyse"], dict) and "problemes" in report["analyse"]:
        problemes = report["analyse"]["problemes"]
        if problemes:
            console.print("\n[bold]Problèmes Détectés:[/bold]\n")
            for i, p in enumerate(problemes, 1):
                sev = p.get("severite", "mineur")
                style = "bold red" if sev == "critique" else "bold yellow" if sev == "majeur" else "bold green"
                console.print(Panel(
                    f"[bold]Type:[/bold] {p.get('type', 'N/A')}\n[bold]Localisation:[/bold] {p.get('localisation', 'N/A')}\n[bold]Description:[/bold] {p.get('description', 'N/A')}\n[bold]Impact:[/bold] {p.get('impact', 'N/A')}\n[bold]Recommandation:[/bold] {p.get('recommandation', 'N/A')}",
                    title=f"Problème #{i}", border_style=style))
    if args.output:
        console.print(f"\n[bold]Rapport sauvegardé:[/bold] {args.output}")
    else:
        console.print("\n[bold yellow]💡 Astuce:[/bold yellow] Utilisez --output pour sauvegarder le rapport")


def cmd_query(args):
    """Pose une question spécifique"""
    console.print(f"[bold]Question:[/bold] {args.question}\n")
    workflow = ValidationWorkflow()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Recherche et analyse...", total=None)
        workflow.initialize()
        result = workflow.query(args.question)
        progress.update(task, completed=True)
    console.print("\n[bold green]✅ Réponse:[/bold green]\n")
    console.print(Panel(result['reponse'], title="Réponse", border_style="green"))
    if result.get('sources'):
        console.print("\n[bold]Sources utilisées:[/bold]")
        for s in result['sources']:
            console.print(f"  • {s}")


def cmd_add(args):
    """Ajoute des documents"""
    workflow = ValidationWorkflow()
    workflow.initialize()
    file_paths = [Path(f) for f in args.files]
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Ajout des documents...", total=None)
        workflow.add_documents(file_paths)
        progress.update(task, completed=True)
    console.print(f"[bold green]✅ {len(file_paths)} document(s) ajouté(s)![/bold green]")


def main():
    print_banner()
    if not check_setup():
        sys.exit(1)
    parser = argparse.ArgumentParser(description="Assistant GenAI pour la Revue de Spécifications")
    sub = parser.add_subparsers(dest='command', help='Commandes')
    p_init = sub.add_parser('init', help='Initialise le workflow')
    p_init.add_argument('--rebuild', action='store_true', help='Reconstruit le vector store')
    p_review = sub.add_parser('review', help='Exécute une revue complète')
    p_review.add_argument('--questions', type=str, help='Questions (séparées par ;)')
    p_review.add_argument('--output', type=Path, help='Fichier de sortie (.json, .html, .md)')
    p_query = sub.add_parser('query', help='Pose une question')
    p_query.add_argument('question', type=str)
    p_add = sub.add_parser('add', help='Ajoute des documents')
    p_add.add_argument('files', nargs='+', help='Fichiers à ajouter')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    try:
        if args.command == 'init':
            cmd_init(args)
        elif args.command == 'review':
            cmd_review(args)
        elif args.command == 'query':
            cmd_query(args)
        elif args.command == 'add':
            cmd_add(args)
    except Exception as e:
        console.print(f"[bold red]❌ Erreur:[/bold red] {str(e)}")
        logger.exception("Erreur")
        sys.exit(1)


if __name__ == "__main__":
    main()
