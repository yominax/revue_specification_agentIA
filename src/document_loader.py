"""Chargement et découpage des documents techniques."""
from pathlib import Path
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)


class DocumentLoader:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def load_document(self, file_path: Path) -> List[Document]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier introuvable: {file_path}")
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            loader = PyPDFLoader(str(file_path))
        elif ext == ".txt":
            loader = TextLoader(str(file_path), encoding="utf-8")
        elif ext in (".docx", ".doc"):
            loader = Docx2txtLoader(str(file_path))
        else:
            raise ValueError(f"Format non supporté: {ext}")
        docs = loader.load()
        for d in docs:
            d.metadata["source"] = str(file_path)
            d.metadata["file_name"] = file_path.name
        return docs

    def load_directory(self, directory_path: Path) -> List[Document]:
        directory_path = Path(directory_path)
        if not directory_path.exists():
            raise FileNotFoundError(f"Dossier introuvable: {directory_path}")
        all_docs = []
        for f in directory_path.iterdir():
            if f.is_file() and f.suffix.lower() in (".pdf", ".txt", ".docx", ".doc"):
                try:
                    all_docs.extend(self.load_document(f))
                except Exception as e:
                    logger.warning(f"Skip {f}: {e}")
        return all_docs

    def split_documents(self, documents: List[Document]) -> List[Document]:
        return self.text_splitter.split_documents(documents)
