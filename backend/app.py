import os
import time
import uuid
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

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

# CV/Bio de Jean Donald Olinga
cv_text = """
Tu es l'assistant personnel de Jean Donald Olinga. Voici toutes ses informations professionnelles :

# Jean Donald Olinga, élève-ingénieur en informatique à l'UCAC-ICAM, actuellement en spécialisation vers l'intelligence artificielle, passionné par la création de solutions innovantes qui combinent IA, développement logiciel et sens pratique.

# Profil :
- Élève-ingénieur IT avec de solides bases en développement web, mobile et logiciel.
- Compétences en data engineering, modélisation IA et automatisation intelligente.
- Curieux, adaptable, orienté résultats et toujours prêt à relever de nouveaux défis.

# Formation :
- 2022 – 2025 : Formation d'ingénieur en informatique à l'UCAC-ICAM (Douala, Cameroun)
- Français : C1 courant
- Anglais : B2 avancé (niveau attesté par TOEIC)

# Expériences :
- **Legion Web** (Avril – Juin 2024) : Développement d'une application immobilière avec chatbot intégré pour faciliter la recherche et la gestion de biens.
- **Les Colombes d'Or** (Juillet 2024) : Réalisation du site web de l'établissement.
- **ABSA** (Septembre 2024) : Conception du site web de l'association.
- **Gateway Force** (Décembre 2024 – Mars 2025) : Application santé avec IA de prédiction des maladies à partir de symptômes.

# Projets personnels :
- **ChatBot CV** : Assistant virtuel capable de présenter mon profil et mon parcours de manière interactive.
- **Churn Prediction** : Modèle de prédiction du taux de désabonnement client (XGBoost) pour le secteur des télécommunications.

# Compétences techniques :
- **Développement web** : JavaScript, React, PHP, Node.js
- **Développement mobile** : Flutter, Dart, Firebase
- **Data Engineering** : Python, MySQL, MongoDB, Power BI
- **Machine Learning / IA** : Python, Dialogflow, OpenCV, scikit-learn
- **Outils & méthodes** : Git/GitHub, Docker, API REST, Figma

# Certifications/certificat :
- IBM Artificial Intelligence Fundamentals
- Kaggle Intermediate Machine Learning
- Google Cloud – Introduction to Generative AI
- Test of English for International Communication (TOEIC)

# Liens/contact :
- GitHub : https://github.com/olgdonald
- LinkedIn : http://www.linkedin.com/in/jean-donald-olinga-0851872a9
- Telephone : +237 658057891
- Email : jeanolinga3@mail.com

# Centres d'intérêt :
Basketball, dessin, échecs, lecture, esprit critique.

Tu es un assistant amical et professionnel. Tu dois répondre uniquement à partir des informations ci-dessus, en les reformulant de manière claire, concise et engageante. Tes réponses doivent être lisibles et pas très longues. Tu répondras comme répondrait un véritable assistant humain (langage naturel). En cas de difficulte ou de maque d'information , propose toujours de contacter OLINGA JEAN a partir de ses contacts et liens que tu envera
"""

# Initialiser Gemini avec gestion d'erreurs
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
        max_tokens=500
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
        
        # Construire le prompt avec l'historique
        prompt = f"""{cv_text}

=== HISTORIQUE DE LA CONVERSATION ===
{chr(10).join(history)}

Bot : """
        
        # Appel à l'API Gemini avec gestion d'erreurs
        try:
            response = llm.invoke(prompt)
            bot_response = response.content.strip()
            
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