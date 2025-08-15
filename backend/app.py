import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Configuration
app = Flask(__name__)
CORS(app)  # Permet les requêtes depuis React

# Charger les variables d'environnement
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

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

Tu es un assistant amical et professionnel. Tu dois répondre uniquement à partir des informations ci-dessus, en les reformulant de manière claire, concise et engageante. Tes réponses doivent être lisibles et pas très longues. Tu répondras comme répondrait un véritable assistant humain (langage naturel).
"""

# Initialiser Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0
)

# Stockage temporaire des conversations (en production, utilisez une base de données)
conversations = {}

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message manquant'}), 400
        
        user_message = data['message']
        session_id = data.get('session_id', 'default')
        
        # Récupérer l'historique de la conversation
        if session_id not in conversations:
            conversations[session_id] = []
        
        history = conversations[session_id]
        
        # Ajouter le message de l'utilisateur à l'historique
        history.append(f"Utilisateur : {user_message}")
        
        # Construire le prompt avec l'historique
        prompt = f"""{cv_text}

=== HISTORIQUE DE LA CONVERSATION ===
{chr(10).join(history)}

Bot : """
        
        # Appel à l'API Gemini
        response = llm.invoke(prompt)
        bot_response = response.content.strip()
        
        # Ajouter la réponse du bot à l'historique
        history.append(f"Bot : {bot_response}")
        
        # Limiter l'historique à 20 messages pour éviter des prompts trop longs
        if len(history) > 20:
            conversations[session_id] = history[-20:]
        
        return jsonify({
            'response': bot_response,
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Erreur: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK', 'message': 'API fonctionnelle'})

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """Reset la conversation pour une session donnée"""
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    
    if session_id in conversations:
        conversations[session_id] = []
    
    return jsonify({'message': 'Conversation réinitialisée'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)