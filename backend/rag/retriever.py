"""
retriever.py — Module de RECHERCHE (2ème brique du RAG)
==========================================================
Rôle : étant donné une question, retrouver les chunks de la base de
connaissances les plus pertinents pour y répondre.

Fonctionnement :
1. On transforme la question en vecteur (même technique que pour les chunks).
2. On compare ce vecteur à chaque vecteur de l'index avec la "similarité
   cosinus" (une mesure d'angle entre deux vecteurs : plus l'angle est
   petit, plus les textes parlent de la même chose).
3. On garde les "top_k" chunks les plus proches.

Ce module est indépendant de Flask : on peut le tester seul, en ligne de
commande, sans lancer le serveur. C'est une bonne pratique — plus un
composant est isolé, plus il est facile à tester et à déboguer.

Test rapide en local :
    cd backend
    python -m rag.retriever
"""

import os
import json
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

EMBEDDING_MODEL = "models/gemini-embedding-001"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "index.json")


class Retriever:
    """
    Charge l'index une seule fois (au démarrage du serveur), puis répond
    aux questions de recherche sans refaire de calcul lourd à chaque fois.
    """

    def __init__(self, index_path: str = INDEX_PATH):
        with open(index_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        # On convertit les embeddings en une seule matrice numpy :
        # forme (nombre_de_chunks, dimension_du_vecteur).
        # Ça permet de calculer TOUTES les similarités en une seule opération
        # vectorisée, plutôt qu'avec une boucle Python lente.
        self.embeddings_matrix = np.array([c["embedding"] for c in self.chunks])

    def _embed_query(self, question: str) -> np.ndarray:
        """Transforme la question utilisateur en vecteur."""
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=question,
            # "retrieval_query" (et non "retrieval_document") : on indique
            # au modèle que ce texte est une QUESTION, pas un document à indexer.
            task_type="retrieval_query",
        )
        return np.array(result["embedding"])

    def search(self, question: str, top_k: int = 3) -> list[dict]:
        """
        Retourne les `top_k` chunks les plus pertinents pour `question`,
        triés du plus pertinent au moins pertinent.
        """
        query_vector = self._embed_query(question)

        # Similarité cosinus entre la question et CHAQUE chunk, en une fois :
        #   cos(theta) = (A . B) / (||A|| * ||B||)
        dot_products = self.embeddings_matrix @ query_vector
        norms = np.linalg.norm(self.embeddings_matrix, axis=1) * np.linalg.norm(query_vector)
        similarities = dot_products / norms

        # On récupère les indices des top_k meilleurs scores (ordre décroissant).
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "title": self.chunks[idx]["title"],
                "text": self.chunks[idx]["text"],
                "score": float(similarities[idx]),
            })
        return results


# ---------------------------------------------------------------------
# Mode test : lance "python -m rag.retriever" pour essayer des questions
# directement dans le terminal, sans passer par Flask ni le frontend.
# ---------------------------------------------------------------------
if __name__ == "__main__":
    retriever = Retriever()
    print(f"Index chargé : {len(retriever.chunks)} chunks disponibles.")
    print("Tape une question (ou 'exit' pour quitter).\n")

    while True:
        question = input("Question : ")
        if question.lower() in ("exit", "quit"):
            break

        results = retriever.search(question, top_k=3)
        print("\nChunks les plus pertinents trouvés :")
        for r in results:
            print(f"  [{r['score']:.3f}] {r['title']}")
        print()
