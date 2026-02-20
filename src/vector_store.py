"""Vector store pour le RAG."""
import os
import shutil
import time
from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStore
import logging

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

logger = logging.getLogger(__name__)


class VectorStoreManager:
    def __init__(self):
        from config import settings
        self.settings = settings
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
        self.vector_store: Optional[VectorStore] = None
        self.vector_store_path = settings.vector_store_path

    def create_vector_store(self, documents: List[Document], persist: bool = True) -> VectorStore:
        if self.settings.vector_store_type == "chroma":
            persist_dir = str(self.vector_store_path / "chroma") if persist else None
            if persist_dir and Path(persist_dir).exists():
                persist_path = Path(persist_dir)
                self._force_remove_chroma_dir(persist_path)
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=persist_dir,
            )
        else:
            self.vector_store = FAISS.from_documents(documents=documents, embedding=self.embeddings)
            if persist:
                fp = self.vector_store_path / "faiss"
                fp.mkdir(exist_ok=True)
                self.vector_store.save_local(str(fp))
        return self.vector_store

    def load_vector_store(self) -> Optional[VectorStore]:
        try:
            if self.settings.vector_store_type == "chroma":
                persist_dir = str(self.vector_store_path / "chroma")
                if Path(persist_dir).exists():
                    self.vector_store = Chroma(
                        persist_directory=persist_dir,
                        embedding_function=self.embeddings,
                    )
                    return self.vector_store
            elif self.settings.vector_store_type == "faiss":
                fp = self.vector_store_path / "faiss"
                if fp.exists():
                    self.vector_store = FAISS.load_local(
                        str(fp), self.embeddings, allow_dangerous_deserialization=True
                    )
                    return self.vector_store
        except Exception as e:
            error_msg = str(e).lower()
            if "no such column" in error_msg or "sqlite3.operationalerror" in error_msg or "topic" in error_msg:
                logger.warning(f"Base de données ChromaDB incompatible (schéma obsolète): {e}")
                if self.settings.vector_store_type == "chroma":
                    persist_dir = Path(self.vector_store_path / "chroma")
                    if persist_dir.exists():
                        logger.warning(f"Suppression de la base de données corrompue: {persist_dir}")
                        self._force_remove_chroma_dir(persist_dir)
                self.vector_store = None
            else:
                logger.error(f"Chargement vector store: {e}")
                self.vector_store = None
        return None

    def add_documents(self, documents: List[Document], persist: bool = True):
        if self.vector_store is None:
            raise ValueError("Aucun vector store chargé.")
        try:
            self.vector_store.add_documents(documents)
        except Exception as e:
            error_msg = str(e).lower()
            if "no such column" in error_msg or "sqlite3.operationalerror" in error_msg or "topic" in error_msg:
                logger.warning(f"Erreur lors de l'ajout de documents (vector store corrompu): {e}")
                persist_dir = Path(self.vector_store_path / "chroma")
                if persist_dir.exists():
                    logger.warning("Suppression du vector store corrompu et recréation...")
                    self._force_remove_chroma_dir(persist_dir)
                self.create_vector_store(documents, persist=persist)
                return
            else:
                raise
        if persist and self.settings.vector_store_type == "chroma":
            pass
        elif persist and self.settings.vector_store_type == "faiss":
            (self.vector_store_path / "faiss").mkdir(exist_ok=True)
            self.vector_store.save_local(str(self.vector_store_path / "faiss"))

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        if self.vector_store is None:
            raise ValueError("Aucun vector store chargé.")
        return self.vector_store.similarity_search(query, k=k)

    def _force_remove_chroma_dir(self, persist_dir: Path):
        """Force la suppression du répertoire ChromaDB avec retry."""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                if self.vector_store is not None:
                    try:
                        if hasattr(self.vector_store, '_client'):
                            self.vector_store._client = None
                    except:
                        pass
                    self.vector_store = None
                time.sleep(0.5)
                if persist_dir.exists():
                    shutil.rmtree(persist_dir)
                    logger.info("Base de données supprimée avec succès.")
                    return
            except PermissionError as pe:
                if attempt < max_retries - 1:
                    logger.warning(f"Tentative {attempt + 1}/{max_retries}: Fichier verrouillé, nouvel essai dans 1 seconde...")
                    time.sleep(1)
                else:
                    logger.error(f"Impossible de supprimer {persist_dir} après {max_retries} tentatives: {pe}")
                    logger.error("Veuillez fermer l'application et supprimer manuellement le dossier vector_store/chroma")
            except Exception as cleanup_error:
                logger.error(f"Erreur lors de la suppression de {persist_dir}: {cleanup_error}")
                break
