#!/usr/bin/env python3
"""
Porte de validation des spécifications pour intégration CI/CD.

Usage:
    python validate_specs.py [--max-critiques 0] [--max-majeurs 5] [--output rapport.json]

Exit codes:
    0 = Validation OK
    1 = Seuils dépassés
    2 = Erreur d'exécution
"""
import argparse
import sys
from pathlib import Path

from config import settings
from src.workflow import ValidationWorkflow


def main():
    parser = argparse.ArgumentParser(description="Porte de validation des spécifications")
    parser.add_argument("--max-critiques", type=int, default=0, help="Nombre max de problèmes critiques acceptés")
    parser.add_argument("--max-majeurs", type=int, default=5, help="Nombre max de problèmes majeurs acceptés")
    parser.add_argument("--output", type=Path, default=None, help="Fichier de sortie pour le rapport")
    parser.add_argument("--rebuild", action="store_true", help="Reconstruire le vector store avant la revue")
    args = parser.parse_args()

    try:
        workflow = ValidationWorkflow()
        workflow.initialize(rebuild_vector_store=args.rebuild)
        report = workflow.run_full_review(output_file=args.output)
    except Exception as e:
        print(f"ERREUR: {e}", file=sys.stderr)
        return 2

    stats = report.get("statistiques") or {}
    n_critiques = stats.get("problemes_critiques", 0)
    n_majeurs = stats.get("problemes_majeurs", 0)

    if n_critiques > args.max_critiques:
        print(f"VALIDATION KO: {n_critiques} problème(s) critique(s) (seuil: {args.max_critiques})", file=sys.stderr)
        return 1
    if n_majeurs > args.max_majeurs:
        print(f"VALIDATION KO: {n_majeurs} problème(s) majeur(s) (seuil: {args.max_majeurs})", file=sys.stderr)
        return 1

    print(f"VALIDATION OK: {n_critiques} critique(s), {n_majeurs} majeur(s)")
    if args.output:
        print(f"Rapport: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
