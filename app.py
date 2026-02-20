"""Interface web Streamlit pour la revue de spécifications."""
import sys
import os
import shutil
from pathlib import Path

def _project_root():
    for candidate in [Path(__file__).resolve().parent, Path(os.getcwd())]:
        if (candidate / "config.py").exists() and (candidate / "src" / "workflow.py").exists():
            return candidate
    return Path(__file__).resolve().parent

_root = _project_root()
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import streamlit as st
from datetime import datetime

from config import settings
from src.workflow import ValidationWorkflow
from src.agent import SpecificationReviewAgent

st.set_page_config(
    page_title="Revue de Spécifications",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "workflow" not in st.session_state:
    st.session_state.workflow = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False


def _css():
    """Applique le thème dark."""
    st.markdown("""
    <style>
    /* Fond noir partout */
    .stApp, .main, [data-testid="stAppViewContainer"], body {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    .main .block-container {
        padding: 2.5rem 4rem 4rem !important;
        max-width: 720px;
        background-color: #000000 !important;
        margin: 0 auto;
        margin-top: 1rem;
    }
    /* Texte blanc partout */
    h1, h2, h3, p, .stMarkdown, label, span, div, .stCaption {
        color: #ffffff !important;
    }
    h1 { font-size: 1.5rem; font-weight: 600; margin-bottom: 0.25rem; color: #ffffff !important; }
    h2 { font-size: 1.15rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #333333; color: #ffffff !important; }
    h3 { font-size: 1rem; font-weight: 600; margin-top: 1.25rem; color: #ffffff !important; }
    p, .stMarkdown { line-height: 1.6; color: #ffffff !important; }
    .stCaption { color: #cccccc !important; }
    /* Zones de saisie : fond noir, texte blanc, bordure blanche */
    .stTextArea textarea, .stTextInput input, [data-testid="stTextInput"] input {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 1px solid #ffffff !important;
        border-radius: 6px;
    }
    .stTextArea textarea::placeholder, .stTextInput input::placeholder {
        color: #888888 !important;
    }
    /* Selectbox : fond noir, texte blanc */
    [data-baseweb="select"] {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 1px solid #ffffff !important;
    }
    [data-baseweb="select"] [data-baseweb="popover"] {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: 0.5rem;
    }
    /* Tabs : texte blanc */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid #333333;
        margin-bottom: 1.5rem;
        gap: 0;
        background-color: #000000 !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.65rem 1.25rem;
        font-size: 0.9rem;
        color: #cccccc !important;
        background-color: #000000 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        font-weight: 600;
        background-color: #000000 !important;
    }
    /* Métriques : texte blanc */
    [data-testid="stMetricValue"] { font-size: 1.2rem; font-weight: 600; color: #ffffff !important; }
    [data-testid="stMetricLabel"] { color: #cccccc !important; }
    [data-testid="stMetricDelta"] { color: #ffffff !important; }
    /* Bouton primary : seulement changer la couleur du texte en noir */
    .stButton button[kind="primary"],
    button[kind="primary"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #ffffff !important;
    }
    /* Forcer le texte des boutons primary en noir (tous les enfants) */
    .stButton button[kind="primary"] *,
    .stButton button[kind="primary"] p,
    .stButton button[kind="primary"] span,
    .stButton button[kind="primary"] div,
    .stButton button[kind="primary"] label,
    button[kind="primary"] *,
    button[kind="primary"] p,
    button[kind="primary"] span,
    button[kind="primary"] div,
    button[kind="primary"] label {
        color: #000000 !important;
    }
    /* Bouton secondary : seulement les couleurs */
    .stButton button[kind="secondary"] {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 2px solid #ffffff !important;
    }
    /* Tous les autres boutons : seulement les couleurs */
    .stButton button:not([kind="primary"]):not([kind="secondary"]) {
        background-color: #ffffff !important;
        border: 2px solid #ffffff !important;
        color: #000000 !important;
    }
    /* Fichiers uploadés : fond noir, texte blanc, bordure blanche */
    [data-testid="stFileUploader"] {
        background-color: #000000 !important;
        border: 2px dashed #ffffff !important;
        border-radius: 8px !important;
        padding: 1.5rem !important;
    }
    [data-testid="stFileUploader"] label, 
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] div {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    /* Liste des fichiers uploadés : fond noir, texte blanc */
    [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"],
    [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] span,
    [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] div,
    .uploadedFile {
        color: #ffffff !important;
        font-weight: 600 !important;
        background-color: #000000 !important;
        padding: 0.75rem 1rem !important;
        border-radius: 6px !important;
        border: 1px solid #ffffff !important;
        margin: 0.5rem 0 !important;
    }
    /* Tous les textes dans la zone d'upload */
    [data-testid="stFileUploader"] * {
        color: #ffffff !important;
    }
    /* Expander : texte blanc */
    .streamlit-expanderHeader {
        color: #ffffff !important;
        background-color: #000000 !important;
    }
    .streamlit-expanderContent {
        color: #ffffff !important;
        background-color: #000000 !important;
    }
    /* Textarea disabled : fond noir, texte blanc */
    textarea[disabled] {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
    }
    /* Séparateur */
    hr { margin: 1.5rem 0; border-color: #333333; }
    /* Success/Error messages */
    .stSuccess { background-color: #000000 !important; color: #ffffff !important; border: 1px solid #ffffff !important; }
    .stError { background-color: #000000 !important; color: #ff6b6b !important; border: 1px solid #ff6b6b !important; }
    .stWarning { background-color: #000000 !important; color: #ffd93d !important; border: 1px solid #ffd93d !important; }
    </style>
    """, unsafe_allow_html=True)


def initialize_workflow():
    if not st.session_state.initialized:
        with st.spinner("Initialisation..."):
            try:
                w = ValidationWorkflow()
                w.initialize()
                st.session_state.workflow = w
                st.session_state.initialized = True
                return True
            except Exception as e:
                error_msg = str(e).lower()
                if "no such column" in error_msg or "topic" in error_msg:
                    st.warning("Base de données corrompue détectée. Elle sera recréée lors de l'ajout de documents.")
                    st.session_state.initialized = False
                    st.session_state.workflow = None
                    return False
                else:
                    st.error(str(e))
                    return False
    return True


def main():
    _css()

    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        st.error("Clé API OpenAI manquante. Configurez le fichier .env avec OPENAI_API_KEY.")
        st.stop()

    st.title("Revue de Spécifications")
    st.caption("Analyse automatisée des documents techniques par RAG et LLM.")
    st.markdown("---")

    tab_review, tab_query, tab_add = st.tabs([
        "Revue complète",
        "Question ciblée",
        "Ajouter des documents",
    ])

    with tab_review:
        st.header("Revue automatisée")
        st.markdown("Analyse des spécifications avec détection d'incohérences, contradictions et risques. Les questions ci-dessous sont optionnelles.")
        st.markdown("")  # marge
        custom_questions = st.text_area(
            "Questions personnalisées (une par ligne, optionnel)",
            height=100,
            placeholder="Y a-t-il des contradictions entre les sections ?\nLes exigences de sécurité sont-elles claires ?",
            label_visibility="collapsed",
        )
        st.markdown("")
        col_a, col_b = st.columns([1, 1])
        with col_a:
            output_format = st.selectbox("Format du rapport", ["JSON", "Markdown", "Texte"])
        with col_b:
            st.markdown("<div style='padding-top: 0.5rem;'></div>", unsafe_allow_html=True)  # Alignement vertical
            run_review = st.button("Lancer l'analyse", type="primary", use_container_width=True)

        if run_review:
            if not initialize_workflow():
                st.stop()
            questions_list = [q.strip() for q in custom_questions.split("\n") if q.strip()] if custom_questions.strip() else None
            with st.spinner("Analyse en cours..."):
                try:
                    output_file = None
                    if output_format == "JSON":
                        output_file = settings.output_path / f"rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    elif output_format == "Markdown":
                        output_file = settings.output_path / f"rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    report = st.session_state.workflow.run_full_review(
                        custom_questions=questions_list,
                        output_file=output_file,
                    )
                    st.success("Analyse terminée.")
                    st.subheader("Résumé")
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("Documents", report["resume"]["nombre_documents"])
                    with c2:
                        st.metric("Segments analysés", report["resume"]["nombre_chunks_analyses"])
                    stats = report.get("statistiques") or {}
                    with c3:
                        st.metric("Problèmes", stats.get("total_problemes", 0))
                    with c4:
                        st.metric("Critiques", stats.get("problemes_critiques", 0))
                    problemes = (report.get("analyse") or {}).get("problemes") or []
                    if problemes:
                        st.subheader("Problèmes détectés")
                        for i, p in enumerate(problemes, 1):
                            with st.expander(
                                f"#{i} — {p.get('type', 'N/A')} ({p.get('severite', 'N/A')})",
                                expanded=(p.get("severite") == "critique"),
                            ):
                                st.write("**Localisation** —", p.get("localisation", "N/A"))
                                st.write("**Description** —", p.get("description", "N/A"))
                                st.write("**Impact** —", p.get("impact", "N/A"))
                                st.write("**Recommandation** —", p.get("recommandation", "N/A"))
                    st.subheader("Analyse détaillée")
                    st.text_area("", report.get("reponse_complete", ""), height=320, disabled=True, label_visibility="collapsed")
                    if output_file:
                        st.caption(f"Rapport enregistré : {output_file}")
                except Exception as e:
                    st.error(str(e))

    with tab_query:
        st.header("Question ciblée")
        st.markdown("Interrogez le contenu des spécifications indexées. La réponse s'appuie sur les passages pertinents (RAG).")
        st.markdown("")
        question = st.text_input("Question", placeholder="Ex : Quelles sont les exigences de sécurité ?")
        st.markdown("")
        if st.button("Rechercher", type="primary"):
            if not question.strip():
                st.warning("Saisissez une question.")
            else:
                if not initialize_workflow():
                    st.stop()
                with st.spinner("Recherche..."):
                    try:
                        result = st.session_state.workflow.query(question.strip())
                        st.subheader("Réponse")
                        st.write(result["reponse"])
                        if result.get("sources"):
                            st.subheader("Sources")
                            for s in result["sources"]:
                                st.markdown(f"— {s}")
                    except Exception as e:
                        st.error(str(e))

    with tab_add:
        st.header("Ajouter des documents")
        st.markdown("Déposez des fichiers PDF, TXT ou DOCX. Après ajout, utilisez le bouton « Réinitialiser le workflow » en bas pour réindexer.")
        st.markdown("")
        uploaded = st.file_uploader("Fichiers", type=["pdf", "txt", "docx"], accept_multiple_files=True, label_visibility="collapsed")
        st.markdown("")
        if uploaded and st.button("Ajouter et indexer"):
            with st.spinner("Ajout en cours..."):
                try:
                    temp_dir = Path("temp_uploads")
                    temp_dir.mkdir(exist_ok=True)
                    paths = []
                    for f in uploaded:
                        p = temp_dir / f.name
                        p.write_bytes(f.getbuffer())
                        paths.append(p)
                    if not st.session_state.initialized:
                        w = ValidationWorkflow()
                        try:
                            vs = w.vector_store_manager.load_vector_store()
                        except Exception as load_error:
                            error_msg = str(load_error).lower()
                            if "no such column" in error_msg or "topic" in error_msg:
                                vs = None
                            else:
                                raise
                        if vs is None:
                            all_docs = []
                            for fp in paths:
                                all_docs.extend(w.document_loader.load_document(fp))
                            chunks = w.document_loader.split_documents(all_docs)
                            w.vector_store_manager.create_vector_store(chunks, persist=True)
                        else:
                            w.vector_store_manager.vector_store = vs
                        w.agent = SpecificationReviewAgent(w.vector_store_manager)
                        st.session_state.workflow = w
                        st.session_state.initialized = True
                    else:
                        st.session_state.workflow.add_documents(paths)
                    for p in paths:
                        if p.exists():
                            p.unlink()
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    st.success(f"{len(paths)} fichier(s) ajouté(s) et indexé(s).")
                except Exception as e:
                    st.error(str(e))
        st.markdown("---")
        st.subheader("Réinitialiser le workflow")
        st.markdown("À faire après avoir ajouté ou modifié des documents dans le dossier des spécifications.")
        if st.button("Réinitialiser le workflow", type="secondary"):
            st.session_state.initialized = False
            st.session_state.workflow = None
            st.rerun()


if __name__ == "__main__":
    main()
