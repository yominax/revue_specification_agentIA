# Revue de spécifications (RAG + LLM)

**Auteur** : Sidi Mohamed Moutaouaffiq

Outil pour analyser des spécifications techniques : détection d'incohérences, contradictions et risques via RAG et LLM.

## Installation

```bash
git clone https://github.com/yominax/revue_specification_agentIA.git
cd AssistantGenAI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Renseigner `OPENAI_API_KEY` dans `.env`.

## Lancer

```bash
# CLI
python cli.py init
python cli.py review --output reports/rapport.json

# Web
streamlit run app.py
```

## Fichier d'exemple

Placer des PDF/TXT/DOCX dans `documents/` ou les ajouter via l’interface. Un exemple est fourni : `documents/specification_exemple.txt`.
