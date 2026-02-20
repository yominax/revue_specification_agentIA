"""Workflow de validation des spécifications."""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from config import settings
from src.document_loader import DocumentLoader
from src.vector_store import VectorStoreManager
from src.agent import SpecificationReviewAgent

logger = logging.getLogger(__name__)


class ValidationWorkflow:
    def __init__(self):
        self.document_loader = DocumentLoader(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.vector_store_manager = VectorStoreManager()
        self.agent = None

    def initialize(self, rebuild_vector_store: bool = False):
        if rebuild_vector_store:
            self._build_vector_store()
        else:
            vs = self.vector_store_manager.load_vector_store()
            if vs is None:
                self._build_vector_store()
        self.agent = SpecificationReviewAgent(self.vector_store_manager)

    def _build_vector_store(self):
        docs = self.document_loader.load_directory(settings.documents_path)
        if not docs:
            raise ValueError(f"Aucun document dans {settings.documents_path}")
        chunks = self.document_loader.split_documents(docs)
        self.vector_store_manager.create_vector_store(chunks, persist=True)

    def add_documents(self, file_paths: List[Path]):
        all_docs = []
        for fp in file_paths:
            all_docs.extend(self.document_loader.load_document(fp))
        if not all_docs:
            raise ValueError("Aucun document valide à ajouter.")
        chunks = self.document_loader.split_documents(all_docs)
        try:
            self.vector_store_manager.add_documents(chunks, persist=True)
        except ValueError as ve:
            if "Aucun vector store chargé" in str(ve):
                self.vector_store_manager.create_vector_store(chunks, persist=True)
            else:
                raise

    def run_full_review(
        self,
        custom_questions: Optional[List[str]] = None,
        output_file: Optional[Path] = None,
    ) -> Dict[str, Any]:
        if self.agent is None:
            raise ValueError("Workflow non initialisé. Lancer init d'abord.")
        review_result = self.agent.review_specifications(questions=custom_questions)
        report = {
            "metadata": {
                "date_analyse": datetime.now().isoformat(),
                "workflow": "Validation Automatisée des Spécifications",
            },
            "resume": {
                "documents_analyses": review_result.get("documents_analyses", []),
                "nombre_documents": len(review_result.get("documents_analyses", [])),
                "nombre_chunks_analyses": review_result.get("nombre_chunks_analyses", 0),
                "questions_analysees": review_result.get("questions_analysees", []),
            },
            "analyse": review_result.get("analyse", {}),
            "reponse_complete": review_result.get("reponse_complete", ""),
        }
        problemes = report["analyse"].get("problemes") or []
        if isinstance(problemes, list):
            report["statistiques"] = {
                "total_problemes": len(problemes),
                "problemes_critiques": sum(1 for p in problemes if p.get("severite") == "critique"),
                "problemes_majeurs": sum(1 for p in problemes if p.get("severite") == "majeur"),
                "problemes_mineurs": sum(1 for p in problemes if p.get("severite") == "mineur"),
            }
        if output_file:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            if output_file.suffix == ".json":
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
            elif output_file.suffix.lower() == ".html":
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(self._report_html(report))
            else:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(self._report_text(report))
        return report

    def query(self, question: str) -> Dict[str, Any]:
        if self.agent is None:
            raise ValueError("Workflow non initialisé. Lancer init d'abord.")
        return self.agent.query_specific(question)

    def _report_text(self, report: Dict) -> str:
        lines = [
            "# Rapport de revue",
            f"Date: {report['metadata']['date_analyse']}",
            f"Documents: {report['resume']['nombre_documents']}",
            "",
        ]
        if "statistiques" in report:
            s = report["statistiques"]
            lines.append(f"Problèmes: {s.get('total_problemes',0)} (critiques: {s.get('problemes_critiques',0)})")
        lines.append(report.get("reponse_complete", ""))
        return "\n".join(lines)

    def _report_html(self, report: Dict) -> str:
        stats = report.get("statistiques", {})
        problemes = report.get("analyse", {}).get("problemes") or []
        def esc(s):
            return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") if s else ""
        rows = "".join(
            f'<tr><td>{i}</td><td>{esc(p.get("type"))}</td><td>{esc(p.get("severite"))}</td><td>{esc(p.get("description"))}</td></tr>'
            for i, p in enumerate(problemes, 1)
        ) or "<tr><td colspan='4'>Aucun problème.</td></tr>"
        return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>Rapport</title></head><body>
<h1>Rapport de revue</h1><p>{report['metadata']['date_analyse']}</p>
<p>Documents: {report['resume']['nombre_documents']} | Chunks: {report['resume']['nombre_chunks_analyses']}</p>
<p>Total problèmes: {stats.get('total_problemes',0)} | Critiques: {stats.get('problemes_critiques',0)}</p>
<table border="1"><tr><th>#</th><th>Type</th><th>Sévérité</th><th>Description</th></tr>{rows}</table>
<pre>{esc(report.get('reponse_complete',''))}</pre></body></html>"""
