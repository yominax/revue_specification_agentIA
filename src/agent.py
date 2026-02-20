"""Agent IA pour la revue de spécifications."""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.documents import Document
import json
import logging

try:
    from langchain_community.callbacks import get_openai_callback
except ImportError:
    from langchain_community.callbacks.manager import get_openai_callback

from config import settings

logger = logging.getLogger(__name__)


class SpecificationReviewAgent:
    def __init__(self, vector_store_manager):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            openai_api_key=settings.openai_api_key,
        )
        self.vs = vector_store_manager
        self.system_prompt = """Tu es un expert en revue de spécifications techniques. Analyse les documents et détecte incohérences, contradictions, ambiguïtés et risques. Pour chaque problème: type, sévérité (critique/majeur/mineur), localisation, description, impact, recommandation."""
        self.review_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_prompt),
            HumanMessagePromptTemplate.from_template("""
Documents:
{context}

Questions:
{questions}

Réponds UNIQUEMENT par un JSON valide avec cette structure (sans texte avant/après):
{{"problemes": [{{"id": 1, "type": "...", "severite": "critique|majeur|mineur", "localisation": "...", "description": "...", "impact": "...", "recommandation": "..."}}]}}
Si aucun problème: {{"problemes": []}}
"""),
        ])

    def review_specifications(
        self, questions: Optional[List[str]] = None, k_context: int = 10
    ) -> Dict[str, Any]:
        if questions is None:
            questions = [
                "Contradictions entre sections ?",
                "Exigences claires et non ambiguës ?",
                "Informations manquantes ?",
                "Risques techniques ?",
            ]
        context_docs = []
        for q in questions:
            context_docs.extend(self.vs.similarity_search(q, k=k_context))
        seen = set()
        unique = []
        for doc in context_docs:
            key = f"{doc.metadata.get('source','')}-{doc.page_content[:50]}"
            if key not in seen:
                seen.add(key)
                unique.append(doc)
        context = "\n\n".join(
            f"[{d.metadata.get('file_name','?')}]\n{d.page_content}" for d in unique[: k_context * 2]
        )
        try:
            with get_openai_callback() as cb:
                chain = self.review_prompt | self.llm
                msg = chain.invoke({"context": context, "questions": "\n".join(f"- {q}" for q in questions)})
                response = msg.content if hasattr(msg, "content") else str(msg)
                logger.info(f"Tokens: {cb.total_tokens}")
        except Exception as e:
            logger.error(str(e))
            raise
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                json_str = response.strip()
            analysis = json.loads(json_str)
        except json.JSONDecodeError:
            analysis = {"problemes": [], "analyse_complete": response}
        return {
            "questions_analysees": questions,
            "documents_analyses": list(set(d.metadata.get("file_name", "?") for d in unique)),
            "nombre_chunks_analyses": len(unique),
            "analyse": analysis,
            "reponse_complete": response,
        }

    def query_specific(self, query: str, k: int = 5) -> Dict[str, Any]:
        docs = self.vs.similarity_search(query, k=k)
        context = "\n\n".join(f"[{d.metadata.get('file_name','?')}]\n{d.page_content}" for d in docs)
        prompt = f"Spécifications:\n{context}\n\nQuestion: {query}\n\nRéponse:"
        msg = self.llm.invoke(prompt)
        return {
            "question": query,
            "reponse": msg.content if hasattr(msg, "content") else str(msg),
            "sources": [d.metadata.get("file_name", "?") for d in docs],
        }
