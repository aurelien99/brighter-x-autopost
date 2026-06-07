"""
Configuration globale du projet Brighter X Autopost.
Centralise toutes les constantes et chemins pour faciliter la maintenance.
"""

import os

# ──────────────────────────────────────────────────────────────────
# YOUTUBE
# ──────────────────────────────────────────────────────────────────

# Channel ID de Brighter with Herbert
# On le trouve dans la source de la page YouTube de la chaîne
# VÉRIFIÉ : https://www.youtube.com/feeds/videos.xml?channel_id=UC4DBLlq1x0AKmip1QJUcbXg
YOUTUBE_CHANNEL_ID = "UC4DBLlq1x0AKmip1QJUcbXg"
RSS_FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
CHANNEL_NAME = "Brighter with Herbert"
CHANNEL_HANDLE = "@BrighterwithHerbert"

# ──────────────────────────────────────────────────────────────────
# X / TWITTER
# ──────────────────────────────────────────────────────────────────

X_USERNAME = "aurel99"
X_USER_DISPLAY = "@aurel99"

# ──────────────────────────────────────────────────────────────────
# AI (Anthropic Claude)
# ──────────────────────────────────────────────────────────────────

# Modèle IA par défaut (Claude 3.5 Haiku pour vitesse, ou Sonnet pour qualité)
AI_MODEL = "claude-3-5-haiku-latest"  # ou "claude-sonnet-4-20250514"
AI_MAX_TOKENS = 1000
AI_TEMPERATURE = 0.7

# ──────────────────────────────────────────────────────────────────
# BASE DE DONNÉES (JSON)
# ──────────────────────────────────────────────────────────────────

PLANNING_DB_PATH = "planned_threads.json"
PLANNING_DB_DEFAULT = []
POSTED_DB_PATH = "posted_videos.json"
POSTED_DB_DEFAULT = {"videos": []}

# ──────────────────────────────────────────────────────────────────
# RATE LIMITING
# ──────────────────────────────────────────────────────────────────

X_TWEET_DELAY_SECONDS = 10  # Pause entre chaque tweet du thread (X rate limit)
X_MAX_RETRIES = 3           # Nombre de tentatives en cas d'erreur API

# ──────────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────────

LOG_FILE = "autopost.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ──────────────────────────────────────────────────────────────────
# PROMPT MASTER
# ──────────────────────────────────────────────────────────────────

PROMPT_MASTER = """
Tu es un expert Tesla/SpaceX/AI qui crée du contenu viral sur X pour {username}.

Crée un thread X complet à partir du titre et du transcript d'une vidéo de {channel_handle}.

**Règles strictes :**
- Chaque tweet < 260 caractères (marge de sécurité).
- Numérote clairement : 1/N, 2/N, ..., N/N.
- Ton : engageant, optimiste, professionnel mais accessible.
  Mélange insights investing, milestones Tesla, et hype raisonnée.
- Structure idéale :
  1/N : Hook puissant + titre vidéo + {channel_handle} + lien.
  2/N à N-1 : Points clés les plus impactants (chiffres, implications
              investing, Optimus, Robotaxi, FSD, SpaceX…).
  Dernier tweet : CTA (question ou appel à l'engagement) + hashtags
                  (#Tesla #TSLA #Optimus #Robotaxi #FSD #SpaceX) + {username}.
- Emojis pertinents mais pas excessifs (🔥 🚀 📈 🤖).
- Transitions fluides.
- Priorise les insights investing et actionnables.
- Langue principale : Français (termes Tesla en anglais).

Titre : {title}
Transcript : {transcript}
"""

# ──────────────────────────────────────────────────────────────────
# VALIDATION / ARTIFACT
# ──────────────────────────────────────────────────────────────────

ARTIFACT_DIR = "artifacts"
ARTIFACT_FILE_PATTERN = "thread_{video_id}.txt"
ARTIFACT_APPROVED_TOKEN = "APPROVED"
ARTIFACT_REJECTED_TOKEN = "REJECTED"
ARTIFACT_EDIT_REQUESTED_TOKEN = "EDIT_REQUESTED"
