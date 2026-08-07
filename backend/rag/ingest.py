"""
ingest.py — Script d'INDEXATION (1ère brique du RAG)
======================================================
Rôle : lire la base de connaissances (knowledge/profil.md), la découper
en petits morceaux ("chunks"), calculer un embedding (vecteur numérique)
pour chacun, puis sauvegarder le tout dans rag/index.json.

Quand le lancer ?
- Une fois au départ.
- À chaque fois que tu modifies knowledge/profil.md (nouveau projet,
  nouvelle expérience...). Il faut RE-générer l'index pour que le
  chatbot connaisse les changements.

Comment le lancer en local ?
    cd backend
    python -m rag.ingest

Ce script ne touche à rien d'autre : il ne modifie pas app.py, chat.py,
et n'a aucun effet sur le site déployé sur Railway tant que tu ne pousses
pas index.json + le nouveau code sur la branche "main".
"""

import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------------------

# On charge la clé API depuis le .env local (le même que pour Gemini).
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY manquant. Vérifie que backend/.env contient bien "
        "GOOGLE_API_KEY=ta_cle"
    )

genai.configure(api_key=GOOGLE_API_KEY)

# Modèle d'embedding de Google. C'est un modèle DIFFÉRENT de Gemini :
# il ne "discute" pas, il transforme un texte en une liste de nombres
# (un vecteur) qui représente le SENS du texte.
#
# Note d'ingénierie : "text-embedding-004" a été DÉPRÉCIÉ par Google
# (arrêté le 14 janvier 2026). On utilise son remplaçant officiel,
# "gemini-embedding-001". Comme le nom du modèle n'existe qu'ICI,
# une future dépréciation ne demandera qu'une seule ligne à changer.
EMBEDDING_MODEL = "models/gemini-embedding-001"

# Chemins des fichiers, calculés à partir de l'emplacement de ce script
# (pour que ça marche peu importe le dossier depuis lequel tu lances la commande).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # backend/rag
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "..", "knowledge", "profil.md")
INDEX_PATH = os.path.join(BASE_DIR, "index.json")


# ---------------------------------------------------------------------
# 2. Découpage en chunks ("chunking")
# ---------------------------------------------------------------------

def split_into_chunks(markdown_text: str) -> list[dict]:
    """
    Découpe le texte Markdown en chunks à chaque titre de section "## ".

    Stratégie choisie : découpage "par section sémantique".
    C'est la stratégie la plus simple qui existe, et elle est parfaitement
    adaptée ici car le contenu est déjà structuré par thème (Formation,
    Projets, Compétences...). Chaque chunk = une idée cohérente, ce qui
    donne de bons résultats de recherche sans complexité inutile.

    (Sur une base de connaissances plus grande et moins structurée, on
    utiliserait un découpage par nombre de mots/tokens avec chevauchement
    — mais ce serait de la sur-ingénierie pour ton cas actuel.)
    """
    # On sépare le texte à chaque "## Titre", en gardant le titre.
    # re.split avec un groupe capturant conserve le séparateur dans le résultat.
    sections = re.split(r"\n(?=## )", markdown_text.strip())

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Le titre est la première ligne (sans les "#")
        lines = section.split("\n", 1)
        title = lines[0].lstrip("#").strip()
        content = lines[1].strip() if len(lines) > 1 else ""

        chunks.append({
            "title": title,
            # On garde le titre DANS le texte du chunk : ça aide le modèle
            # d'embedding à mieux capturer le contexte (un texte "Formation : ..."
            # est plus clair pour la recherche qu'un texte sans thème).
            "text": f"{title}\n{content}".strip(),
        })

    return chunks


# ---------------------------------------------------------------------
# 3. Calcul des embeddings
# ---------------------------------------------------------------------

def embed_text(text: str) -> list[float]:
    """
    Transforme un texte en vecteur numérique via l'API Google.

    task_type="retrieval_document" : indique au modèle que ce texte fait
    partie d'une base à indexer (par opposition à "retrieval_query", utilisé
    plus tard pour la question de l'utilisateur). Google optimise légèrement
    le vecteur différemment selon ce paramètre — bonne pratique à respecter.
    """
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


# ---------------------------------------------------------------------
# 4. Script principal
# ---------------------------------------------------------------------

def main():
    print("Lecture de la base de connaissances...")
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    chunks = split_into_chunks(markdown_text)
    print(f"{len(chunks)} chunks détectés :")
    for c in chunks:
        print(f"  - {c['title']}")

    print("\nCalcul des embeddings (appel à l'API Google pour chaque chunk)...")
    indexed_chunks = []
    for c in chunks:
        vector = embed_text(c["text"])
        indexed_chunks.append({
            "title": c["title"],
            "text": c["text"],
            "embedding": vector,
        })
        print(f"  ✓ {c['title']} ({len(vector)} dimensions)")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(indexed_chunks, f, ensure_ascii=False, indent=2)

    print(f"\nIndex sauvegardé dans {INDEX_PATH}")
    print("Tu peux maintenant tester la recherche avec : python -m rag.retriever")


if __name__ == "__main__":
    main()
