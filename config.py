# -*- coding: utf-8 -*-
"""
config.py - Configuration globale du projet Brighter X Autopost.
Centralise toutes les constantes, chemins et le PROMPT MASTER.
"""

import os

# ============================================================================
# YOUTUBE
# ============================================================================

# Channel ID de Brighter with Herbert (verifie dans la source YouTube)
YOUTUBE_CHANNEL_ID = "UC4DBLlq1x0AKmip1QJUcbXg"
RSS_FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
CHANNEL_NAME = "Brighter with Herbert"
CHANNEL_HANDLE = "@BrighterwithHerbert"

# ============================================================================
# X / TWITTER
# ============================================================================

X_USERNAME = "aurel99"
X_USER_DISPLAY = "@aurel99"

# ============================================================================
# AI (Anthropic Claude)
# ============================================================================

# Modele IA utilise (Haiku pour vitesse, Sonnet pour qualite)
AI_MODEL = os.getenv("AI_MODEL", "claude-3-5-haiku-latest")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "1000"))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))

# Cle API Anthropic (chargee depuis .env ou GitHub Secrets)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ============================================================================
# X API CREDENTIALS (charges depuis .env ou GitHub Secrets)
# ============================================================================

X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET", "")

# ============================================================================
# PUBLICATION & REVIEW
# ============================================================================

# AUTO_PUBLISH: False = revue humaine en console | True = publie directement
AUTO_PUBLISH = os.getenv("AUTO_PUBLISH", "false").lower() == "true"

# Delai entre chaque tweet du thread (rate limiting safe)
TWEET_SLEEP_SECONDS = int(os.getenv("TWEET_SLEEP_SECONDS", "3"))

# ============================================================================
# DATABASES & FILES
# ============================================================================

# Repertoire du projet (racine du repo)
PROJECT_ROOT = Path(__file__).parent.resolve()

# Fichiers de database JSON (stockes dans artifacts/)
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
POSTED_DB = ARTIFACTS_DIR / "posted_videos.json"
PLANNED_DB = ARTIFACTS_DIR / "planned_threads.json"

# Log file
LOG_DIR = ARTIFACTS_DIR / "logs"

# ============================================================================
# PROMPT MASTER - Generation de threads X optimises
# ============================================================================

# Ce prompt est transmis tel quel a l API Claude pour generer les threads.
# Il encode toutes les regles strictes a respecter.

PROMPT_MASTER = """
ROLE: Tu es un expert en social media et en creation de threads X (Twitter)
viraux dans le domaine de la tech automobile (Tesla, EV, energie, IA).

TACHE: A partir du transcript d'une video YouTube ci-dessous, genere un thread
X de 3 a 8 tweets qui resume les points cles de maniere engageante, claire et
optimisee pour les interactions (likes, retweets, reponses).

=== REGLES STRICTES A RESPECTER ===

[1] FORMAT NUMEROTATION
- Chaque tweet DOIT commencer par "N/N" ou N est le numero du tweet et N le
  total (ex: 1/5, 2/5, 3/5, 4/5, 5/5).
- Le SEUL caractere autorise APRES le numero est un espace ou un saut de ligne.
- Exemples valides: "1/5 Voici..." ou "1/5\nVoici..."
- Exemples invalides: "Tweet 1:" ou "(1/5) Tout..."

[2] LIMITE DE CARACTERES
- Chaque tweet doit faire MAXIMUM 260 caracteres (espaces inclus).
- Toujours laisser une marge de securite de 10 caracteres.
- Aucun tweet ne doit depasser 260 caracteres.

[3] LONGUEUR DU THREAD
- Minimum 3 tweets, maximum 8 tweets.
- Choisir le nombre optimal en fonction de la richesse du contenu.

[4] STRUCTURE DU THREAD
- Tweet 1/N: ACCROCHE. Je mets en evidence le point le plus surprenant ou
  controverse de la video. Utilise un hook fort (chiffre, question,
  affirmation choc).
- Tweet 2/N a (N-2)/N: CORPS. Developpe les 2 a 5 points cles principaux.
  Utilise des listes a puces (avec emoji), des chiffres, des comparaisons.
  Un point = un tweet quand c'est dense.
- Tweet (N-1)/N: INSIGHT. Ajoute une analyse personnelle, un angle unique,
  ou une mise en perspective que l'on ne trouve pas dans la video.
- Tweet N/N: CTA (Call To Action). Invite a regarder la video, pose une
  question ouverte, ou appelle a partager. Termine par le lien YouTube.

[5] LIEN YOUTUBE
- Le DERNIER tweet (N/N) DOIT inclure le lien YouTube de la video.
- Format du lien: https://www.youtube.com/watch?v=VIDEO_ID
- Aussi court que possible.

[6] HASHTAGS
- Maximum 2 a 3 hashtags par tweet.
- Toujours sur le tweet N/N (CTA), eventuellement sur le 1/N.
- Hashtags recommandes: #Tesla #EV #EI #Tech (adapter au contenu).

[7] LANGUE & TON
- Francais MAIN. Utilise les termes techniques en anglais (AI, LLM, OTA,
  FSD, BMS, BEV...) sans traduction.
- Ton: dynamique, direct, un peu provocateur mais factuel. Comme si tu parlais
  a un ami passionne de tech.
- Utilise des emojis avec parcimonie (1-2 par tweet max): 
  - Accroche:  ,  ,  , , 
  - Corps: ,  , ,  , , 
  - CTA: , ,  , 
- Pas de ton pr met en valeur les faiblesses ou erreurs eventuelles.
- Apporte une valeur ajoutee qu on ne trouve pas dans la transcription brute.

[8] MISE EN FORME
- Utilise des sauts de ligne pour aerer les tweets.
- Les listes utilise les emojis comme puces ( ,  , , , , ).
- Mets les chiffres et pourcentages en evidence.
- Utilise MAJUSCULES avec parcimonie pour les mots CLES importants.

[9] VERIFICATION FINALE (obligatoire)
- Compte les caracteres de CHAQUE tweet avant d afficher.
- Si un tweet depasse 250 caracteres, reduis-le.
- Verifie la coherence du fil narratif entre les tweets.
- Assure-toi que le thread se suffit a lui-meme (pas besoin de video).

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

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = logging.INFO

# ============================================================================
# UTILITAIRE: S'assurer que le dossier artifacts existe
# ============================================================================

def ensure_artifacts_dirs():
    """Cree les dossiers artifacts/ et logs/ s'ils n'existent pas."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
