# Dockerfile pour l'API Flask
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Variables d'environnement
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Railway fournit dynamiquement le port via la variable $PORT.
# On NE PEUT PAS coder un port en dur (5000, 8080...) : Railway route
# uniquement le trafic public vers le port qu'il assigne lui-même.
# Le format shell (sans crochets []) est nécessaire pour que $PORT soit interprété.
CMD gunicorn --bind 0.0.0.0:$PORT app:app