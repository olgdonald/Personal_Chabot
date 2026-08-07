import os
import time
import uuid
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from rag.retriever import Retriever

# Charger les variables d'environnement
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# URL(s) du frontend autorisé(s) a appeler cette API.
# Definir la variable FRONTEND_URL sur Railway (Settings > Variables du service backend)
# avec l'URL publique exacte du service frontend, ex: https://mon-frontend.up.railway.app
# Plusieurs origines peuvent etre listees, separees par une virgule.
frontend_urls_env = os.getenv("FRONTEND_URL", "http://localhost:5173")
ALLOWED_ORIGINS = [url.strip() for url in frontend_urls_env.split(",") if url.strip()]

# Configuration
app = Flask(__name__)
CORS(
    app,
    origins=ALLOWED_ORIGINS,
    methods=["GET", "POST", "OPTIONS"],  # methodes autorisees
    allow_headers=["Content-Type", "Authorization"],  # headers autorises
    supports_credentials=True
)

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY manquant dans les variables d'environnement")

# ---------------------------------------------------------------------
# RAG — Chargement du moteur de recherche (retriever)
# ---------------------------------------------------------------------
# Le retriever charge rag/index.json (généré par "python -m rag.ingest")
# UNE SEULE FOIS au démarrage du serveur. Le garder en mémoire est bien
# plus rapide que de relire/recalculer les embeddings à chaque question.
try:
    retriever = Retriever()
    print(f"RAG prêt : {len(retriever.chunks)} chunks chargés depuis rag/index.json")
except FileNotFoundError:
    raise ValueError(
        "rag/index.json introuvable. Lance d'abord 'python -m rag.ingest' "
        "pour générer l'index de connaissances avant de démarrer le serveur."
    )

# Instructions système : le "mode d'emploi" donné à Gemini à chaque requête.
# Différence clé avec l'ancienne version : on N'Y MET PLUS le CV entier.
# Seul le contexte pertinent, retrouvé par le retriever, est inséré dans
# {context} au moment de chaque requête (voir la route /api/chat plus bas).
SYSTEM_INSTRUCTIONS = """Tu es l'assistant personnel de Jean Donald Olinga, un élève-ingénieur en informatique spécialisé en intelligence artificielle.

Voici les informations de son profil qui sont pertinentes pour répondre à la question posée :
---
{context}
---

Consignes :
- Réponds UNIQUEMENT à partir des informations ci-dessus. N'invente rien.
- Si les informations ne permettent pas de répondre, dis-le simplement et propose de contacter Jean Donald directement (voir ses coordonnées si elles sont dans le contexte).
- Réponds comme un véritable assistant humain : naturel, clair, concis (pas de réponse trop longue).
- Adopte un ton amical et professionnel.
"""

# Initialiser Gemini avec gestion d'erreurs
#
# Note d'ingénierie (3ème rencontre avec ce problème, et la plus édifiante) :
# "gemini-2.5-flash" existe encore, mais Google a fermé son accès aux
# NOUVEAUX comptes API (le tien). On passe donc à la génération Gemini 3,
# avec "gemini-3.5-flash-lite" : le modèle stable (GA) le plus rapide et
# le moins cher de la gamme actuelle. Très bien adapté à notre cas : on
# ne demande pas un raisonnement complexe, juste de reformuler un
# contexte déjà fourni par le RAG.
#
# thinking_level="low" : sur Gemini 3, on ne parle plus de "budget de
# tokens" (thinking_budget, spécifique à Gemini 2.5) mais de "niveau"
# (low / medium / high). Gemini 3 ne permet pas de désactiver entièrement
# la réflexion, mais "low" la réduit au minimum : réponses plus rapides
# et moins de tokens "invisibles" grignotés sur max_tokens.
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
        max_tokens=800,
        thinking_level="low"
    )
except Exception as e:
    print(f"Erreur initialisation Gemini: {e}")
    llm = None

# Stockage des conversations avec nettoyage automatique
class ConversationManager:
    def __init__(self):
        self.conversations = {}
        self.lock = threading.Lock()
        self.last_cleanup = time.time()
        self.CLEANUP_INTERVAL = 3600  # 1 heure
        self.MAX_SESSION_AGE = 7200   # 2 heures
        self.MAX_HISTORY_LENGTH = 20  # Limite messages par session
        
    def get_session(self, session_id):
        with self.lock:
            self._cleanup_if_needed()
            
            if session_id not in self.conversations:
                self.conversations[session_id] = {
                    'messages': [],
                    'created_at': time.time(),
                    'last_activity': time.time()
                }
            else:
                self.conversations[session_id]['last_activity'] = time.time()
                
            return self.conversations[session_id]
    
    def add_message(self, session_id, message_type, content):
        session = self.get_session(session_id)
        session['messages'].append(f"{message_type} : {content}")
        
        # Limiter la taille de l'historique
        if len(session['messages']) > self.MAX_HISTORY_LENGTH:
            session['messages'] = session['messages'][-self.MAX_HISTORY_LENGTH:]
    
    def get_history(self, session_id):
        session = self.get_session(session_id)
        return session['messages']
    
    def reset_session(self, session_id):
        with self.lock:
            if session_id in self.conversations:
                self.conversations[session_id]['messages'] = []
                self.conversations[session_id]['last_activity'] = time.time()
    
    def _cleanup_if_needed(self):
        current_time = time.time()
        if current_time - self.last_cleanup > self.CLEANUP_INTERVAL:
            self._cleanup_old_sessions()
            self.last_cleanup = current_time
    
    def _cleanup_old_sessions(self):
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_data in self.conversations.items():
            if current_time - session_data['last_activity'] > self.MAX_SESSION_AGE:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.conversations[session_id]
        
        print(f"Nettoyage: {len(expired_sessions)} sessions expirées supprimées")
    
    def get_stats(self):
        with self.lock:
            return {
                'total_sessions': len(self.conversations),
                'active_sessions': len([s for s in self.conversations.values() 
                                      if time.time() - s['last_activity'] < 300]),  # 5 min
                'total_messages': sum(len(s['messages']) for s in self.conversations.values())
            }

# Instance globale du gestionnaire de conversations
conversation_manager = ConversationManager()

# Rate limiting simple
class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.lock = threading.Lock()
        
    def is_allowed(self, ip, limit=10, window=60):
        with self.lock:
            current_time = time.time()
            
            if ip not in self.requests:
                self.requests[ip] = []
            
            # Nettoyer les anciennes requêtes
            self.requests[ip] = [req_time for req_time in self.requests[ip] 
                               if current_time - req_time < window]
            
            # Vérifier la limite
            if len(self.requests[ip]) >= limit:
                return False
            
            # Ajouter la nouvelle requête
            self.requests[ip].append(current_time)
            return True

rate_limiter = RateLimiter()


def extract_response_text(response) -> str:
    """
    Extrait le texte d'une réponse Gemini, quel que soit son format.

    Depuis le passage à langchain-google-genai 4.x (nouveau SDK google-genai),
    response.content peut être :
    - une simple chaîne de caractères (ancien comportement), OU
    - une LISTE de blocs, ex: [{"type": "text", "text": "..."}], qui permet
      par exemple de distinguer du texte normal d'un appel d'outil.

    On gère les deux cas pour que le code reste robuste même si Google fait
    encore évoluer ce format plus tard.
    """
    content = response.content

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts).strip()

    # Cas de secours, très improbable : on convertit simplement en texte.
    return str(content).strip()

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not rate_limiter.is_allowed(client_ip, limit=30, window=60):
            return jsonify({'error': 'Trop de requêtes. Veuillez patienter.'}), 429
        
        # Validation de la requête
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message manquant'}), 400
        
        user_message = data['message'].strip()
        if not user_message or len(user_message) > 1000:
            return jsonify({'error': 'Message invalide (vide ou trop long)'}), 400
        
        # Génération d'un ID de session unique si non fourni
        session_id = data.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Vérification de la disponibilité de Gemini
        if not llm:
            return jsonify({'error': 'Service temporairement indisponible'}), 503
        
        # Ajouter le message utilisateur à l'historique
        conversation_manager.add_message(session_id, "Utilisateur", user_message)
        
        # Récupérer l'historique de la conversation
        history = conversation_manager.get_history(session_id)

        # ---- ETAPE RAG 1/2 : RECHERCHE (retrieval) ----
        # On cherche, dans la base de connaissances, les chunks les plus
        # pertinents par rapport à LA QUESTION (pas tout l'historique :
        # on veut cibler ce que l'utilisateur demande maintenant).
        relevant_chunks = retriever.search(user_message, top_k=3)
        context_text = "\n\n".join(
            f"### {chunk['title']}\n{chunk['text']}" for chunk in relevant_chunks
        )

        # ---- ETAPE RAG 2/2 : GENERATION AUGMENTEE ----
        # Le prompt final ne contient plus TOUT le CV, seulement le contexte
        # retrouvé ci-dessus + l'historique récent + la question. Un prompt
        # plus court = réponse plus rapide, moins coûteuse et plus ciblée.
        prompt = f"""{SYSTEM_INSTRUCTIONS.format(context=context_text)}

=== HISTORIQUE DE LA CONVERSATION ===
{chr(10).join(history)}

Bot : """
        
        # Appel à l'API Gemini avec gestion d'erreurs
        try:
            response = llm.invoke(prompt)
            bot_response = extract_response_text(response)
            
            if not bot_response:
                bot_response = "Désolé, je n'ai pas pu générer une réponse appropriée. Pouvez-vous reformuler votre question ?"
                
        except Exception as e:
            print(f"Erreur Gemini API: {e}")
            bot_response = "Je rencontre actuellement des difficultés techniques. Veuillez réessayer dans quelques instants."
        
        # Ajouter la réponse du bot à l'historique
        conversation_manager.add_message(session_id, "Bot", bot_response)
        
        return jsonify({
            'response': bot_response,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Erreur générale: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    stats = conversation_manager.get_stats()
    return jsonify({
        'status': 'OK', 
        'message': 'API fonctionnelle',
        'gemini_available': llm is not None,
        'rag_chunks_loaded': len(retriever.chunks),
        'stats': stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """Reset la conversation pour une session donnée"""
    try:
        data = request.get_json()
        session_id = data.get('session_id') if data else None
        
        if not session_id:
            return jsonify({'error': 'Session ID manquant'}), 400
        
        conversation_manager.reset_session(session_id)
        
        return jsonify({
            'message': 'Conversation réinitialisée',
            'session_id': session_id
        })
    except Exception as e:
        print(f"Erreur reset: {e}")
        return jsonify({'error': 'Erreur lors de la réinitialisation'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Statistiques pour monitoring (optionnel)"""
    stats = conversation_manager.get_stats()
    return jsonify(stats)

# Gestion des erreurs globales
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint non trouvé'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erreur interne du serveur'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Démarrage de l'API sur le port {port}")
    print(f"Mode debug: {debug}")
    print(f"Gemini disponible: {llm is not None}")
    
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)