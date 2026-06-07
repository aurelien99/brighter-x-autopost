# -*- coding: utf-8 -*-
"""
config.py - Configuration globale du projet Brighter X Autopost.
Centralise toutes les constantes, chemins et le PROMPT MASTER.
新一代版本：使用 Google Gemini（免费）代替 Anthropic Claude。
"""

import os
from pathlib import Path
import logging

# ============================================================================
# YOUTUBE
# ============================================================================
YOUTUBE_CHANNEL_ID = "UC4DBLlq1x0AKmip1QJUcbXg"
RSS_FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
CHANNEL_NAME = "Brighter with Herbert"
CHANNEL_HANDLE = "@BrighterwithHerbert"

# ============================================================================
# X / TWITTER
# ============================================================================
X_USERNAME = "aurel99"
X_USER_DISPLAY = "@aurel99"
X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET", "")
X_TWEET_DELAY_SECONDS = int(os.getenv("TWEET_SLEEP_SECONDS", "3"))
X_MAX_RETRIES = int(os.getenv("X_MAX_RETRIES", "3"))

# ============================================================================
# AI (Google Gemini - gratuit)
# ============================================================================
# Modeles disponibles :
#   gemini-2.5-flash          : rapide, gratuit, bon rapport qualite/prix
#   gemini-2.5-flash-lite     : plus rapide, moins de contexte
#   gemini-2.5-pro            : qualite max (payant)
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "1500"))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ============================================================================
# PUBLICATION & REVIEW
# ============================================================================
AUTO_PUBLISH = os.getenv("AUTO_PUBLISH", "false").lower() == "true"
TWEET_SLEEP_SECONDS = int(os.getenv("TWEET_SLEEP_SECONDS", "3"))

# ============================================================================
# DATABASE & FILES
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.resolve()
ARTIFACT_DIR = str(PROJECT_ROOT / "artifacts")
PLANNING_DB_PATH = str(PROJECT_ROOT / "artifacts" / "planned_threads.json")
POSTED_DB_PATH = str(PROJECT_ROOT / "artifacts" / "posted_videos.json")
LOG_FILE = str(PROJECT_ROOT / "artifacts" / "logs" / "autopost.log")

PLANNING_DB_DEFAULT = []
POSTED_DB_DEFAULT = {"videos": []}

ARTIFACT_FILE_PATTERN = "thread_{video_id}.txt"
ARTIFACT_APPROVED_TOKEN = "APPROVED"
ARTIFACT_REJECTED_TOKEN = "REJECTED"
ARTIFACT_EDIT_REQUESTED_TOKEN = "EDIT_REQUESTED"

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# UTILITAIRE: S'assurer que le dossier artifacts existe
# ============================================================================
def ensure_artifacts_dirs():
    """Cree les dossiers artifacts/ et logs/ s'ils n'existent pas."""
    Path(ARTIFACT_DIR).mkdir(parents=True, exist_ok=True)
    (Path(ARTIFACT_DIR) / "logs").mkdir(parents=True, exist_ok=True)

# ============================================================================
# PROMPT MASTER - Generation de threads X optimises (pour Gemini)
# ============================================================================
PROMPT_MASTER = """
ROLE: Tu es un expert en social media et en creation de threads X (Twitter) viraux dans le domaine de la tech automobile (Tesla, EV, energie, IA).
TACHE: A partir du transcript d'une video YouTube ci-dessous, genere un thread X de 3 a 8 tweets qui resume les points cles de maniere engageante, claire et optimisee pour les interactions (likes, retweets, reponses).

=== REGLES STRICTES A RESPECTER ===
[1] FORMAT NUMEROTATION
- Chaque tweet DOIT commencer par "N/N" ou N est le numero du tweet et N le total (ex: 1/5, 2/5, 3/5, 4/5, 5/5).
- Le SEUL caractere autorise APRES le numero est un espace ou un saut de ligne.
[2] LIMITE DE CARACTERES
- Chaque tweet doit faire MAXIMUM 260 caracteres (espaces inclus).
- Toujours laisser une marge de securite de 10 caracteres.
[3] LONGUEUR DU THREAD
- Minimum 3 tweets, maximum 8 tweets.
[4] STRUCTURE DU THREAD
- Tweet 1/N: ACCROCHE. Met en evidence le point le plus surprenant.
- Tweet 2/N a (N-2)/N: CORPS. Developpe les points cles principaux.
- Tweet (N-1)/N: INSIGHT. Ajoute une analyse personnelle.
- Tweet N/N: CTA. Invite a regarder la video. Termine par le lien YouTube.
[5] LIEN YOUTUBE
- Le DERNIER tweet DOIT inclure le lien YouTube de la video.
[6] HASHTAGS
- Maximum 2 a 3 hashtags par tweet.
- Hashtags recommandes: #Tesla #EV #AI #Tech (adapter au contenu).
[7] LANGUE & TON
- Francais MAIN. Termes techniques en anglais (AI, LLM, OTA, FSD, BMS, BEV...).
- Ton: dynamique, direct, un peu provocateur mais factuel.
- Utilise des emojis avec parcimonie (1-2 par tweet max).
[8] VERIFICATION FINALE (obligatoire)
- Compte les caracteres de CHAQUE tweet avant d'afficher.

=== FORMAT DE SORTIE ATTENDU ===
Reponds UNIQUEMENT avec les tweets au format suivant, rien d'autre:
1/N [Accroche]
---
2/N [Point cle 1]
---
3/N [Point cle 2]
---
...
---
N/N [CTA + Lien YouTube + Hashtags]
Le separateur "---" permet de delimiter les tweets.

=== TRANSCRIPT DE LA VIDEO ===
{transcript}

=== METADONNEES VIDEO ===
Titre: {title}
URL: {url}
Duree: {duration}

Genere maintenant le thread en respectant TOUTES les regles strictes ci-dessus.
"""
