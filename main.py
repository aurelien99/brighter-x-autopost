#!/usr/bin/env python3
"""
Brighter X Autopost - main.py
Automate la publication de threads X depuis les videos de Brighter with Herbert.
Architecture :
    1. Detection nouvelle video via RSS
    2. Extraction du transcript
    3. Generation du thread via IA (Gemini)
    4. Review humaine (console)
    5. Publication du thread sur X
    6. Tracking des videos postees (POSTED_DB / PLANNING_DB)
"""

import os
import sys
import json
import time
import logging
import feedparser
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# dotenv
from dotenv import load_dotenv
load_dotenv()

# IA (Google Gemini)
import google.generativeai as genai

# X / Twitter
import tweepy

# Local
from config import (
    RSS_FEED_URL, CHANNEL_NAME, CHANNEL_HANDLE, X_USERNAME, X_USER_DISPLAY,
    AI_MODEL, AI_MAX_TOKENS, AI_TEMPERATURE, PROMPT_MASTER,
    PLANNING_DB_PATH, PLANNING_DB_DEFAULT, POSTED_DB_PATH, POSTED_DB_DEFAULT,
    ARTIFACT_DIR, ARTIFACT_FILE_PATTERN, ARTIFACT_APPROVED_TOKEN,
    ARTIFACT_REJECTED_TOKEN, ARTIFACT_EDIT_REQUESTED_TOKEN,
    X_TWEET_DELAY_SECONDS, X_MAX_RETRIES, LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT,
    ensure_artifacts_dirs,
)

# ============================================================================
# SETUP: Creer les dossiers artifacts/ et logs/ AVANT le logging
# ============================================================================
ensure_artifacts_dirs()

# ============================================================================
# LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
    ],
)
logger = logging.getLogger(__name__)

# ============================================================================
# CLIENTS
# ============================================================================
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gen_client = genai.GenerativeModel(AI_MODEL)
    logger.info(f"Gemini client initialise avec le modele {AI_MODEL}.")
else:
    logger.error("GEMINI_API_KEY manquante. L'IA ne fonctionnera pas.")
    gen_client = None

X_API_KEY = os.environ['X_API_KEY']
X_API_SECRET = os.environ['X_API_SECRET']
X_ACCESS_TOKEN = os.environ['X_ACCESS_TOKEN']
X_ACCESS_SECRET = os.environ['X_ACCESS_SECRET']

XBot = tweepy.Client(
    consumer_key=X_API_KEY,
    consumer_secret=X_API_SECRET,
    access_token=X_ACCESS_TOKEN,
    access_token_secret=X_ACCESS_SECRET,
    wait_on_rate_limit=True,
)

# ============================================================================
# JSON / DATABASE
# ============================================================================
def load_json(path: str, default: Any) -> Any:
    """Charge un fichier JSON. Si le fichier n'existe pas, retourne la valeur par defaut et l'ecrit sur disque."""
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
        logger.warning(f"Fichier {path} n'existait pas, cree avec default.")
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path: str, data: Any) -> None:
    """Sauvegarde un objet dans un fichier JSON."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Fichier {path} sauvegarde.")

# ============================================================================
# YOUTUBE RSS
# ============================================================================
def fetch_latest_video() -> Optional[Dict[str, str]]:
    """Interroge le flux RSS de la chaine et retourne les metadonnees de la derniere video."""
    logger.info(f"Recuperation RSS: {RSS_FEED_URL}")
    feed = feedparser.parse(RSS_FEED_URL)
    if not feed.entries:
        logger.error("Aucune entree dans le RSS.")
        return None
    latest = feed.entries[0]
    return {
        'video_id': latest.yt_videoid,
        'title': latest.title,
        'link': latest.link,
        'published': latest.published,
    }

# ============================================================================
# TRANSCRIPT
# ============================================================================
def extract_transcript_with_fallback(video_id: str) -> str:
    """Tente l'extraction du transcript (auto ou manuel) avec un fallback sur un transcript synthetique si l'API echoue."""
    from youtube_transcript_api import YouTubeTranscriptApi
    logger.info(f"Extraction transcript pour {video_id}")
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['fr', 'en'])
        return ' '.join(entry['text'] for entry in transcript)
    except Exception as e:
        logger.warning(f"Echec extraction transcript: {e}")
        logger.info("Fallback: transcript synthetique (titre seul).")
        return "(transcript non disponible)"

# ============================================================================
# IA (Gemini)
# ============================================================================
def generate_thread_with_ai(title: str, transcript: str, link: str) -> List[str]:
    """Appelle Gemini avec le Prompt Master et retourne la liste des tweets (3 a 8)."""
    logger.info("Generation du thread via Gemini...")
    if not gen_client:
        logger.error("Client Gemini non initialise. Verifiez GEMINI_API_KEY.")
        return ["Erreur: Gemini non configure. Verifiez GEMINI_API_KEY."]
    
    prompt = PROMPT_MASTER.format(
        username=X_USER_DISPLAY,
        channel_handle=CHANNEL_HANDLE,
        title=title,
        transcript=transcript[:15000],
    )
    
    try:
        response = gen_client.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=AI_MAX_TOKENS,
                temperature=AI_TEMPERATURE,
            ),
        )
        raw = response.text.strip()
        logger.info("Response brute Gemini recue.")
    except Exception as e:
        logger.error(f"Erreur appel Gemini: {e}")
        return ["Erreur: echec appel AI. Verifiez GEMINI_API_KEY et le modele."]

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    tweets = []
    for line in lines:
        if len(line) <= 260 and len(line) >= 20:
            tweets.append(line)
            
    if not tweets:
        logger.error("Aucun tweet genere par Gemini.")
        tweets = ["Thread non genere. Verifiez le transcript ou le prompt."]
        
    tweets[0] += f"\n\n{link}"
    logger.info(f"{len(tweets)} tweets generes.")
    return tweets

# ============================================================================
# REVIEW / ARTIFACT
# ============================================================================
def compute_artifact_path(video_id: str) -> Path:
    """Calcule le chemin du fichier artifact pour un video_id donne."""
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    return Path(ARTIFACT_DIR) / ARTIFACT_FILE_PATTERN.format(video_id=video_id)

def save_artifact(video_id: str, tweets: List[str]) -> None:
    """Ecrit le thread complet dans un fichier artifact. Utilise un token en premiere ligne pour la validation. Approve si le token est APPROVED/EDIT_REQUESTED."""
    path = compute_artifact_path(video_id)
    header = f"# {ARTIFACT_EDIT_REQUESTED_TOKEN}\n"
    body = ""
    for i, t in enumerate(tweets, 1):
        body += f"{i}/{len(tweets)} | {len(t)} chars | {t}\n\n"
    path.write_text(header + body, encoding='utf-8')
    logger.info(f"Artifact sauvegarde: {path}")

def load_artifact(video_id: str) -> tuple[bool, List[str]]:
    """Lit un artifact existant. Retourne (is_approved, tweets). Si le token n'est pas APPROVED ou EDIT_REQUESTED, le fichier est supprime."""
    path = compute_artifact_path(video_id)
    if not path.exists():
        return False, []
    txt = path.read_text(encoding='utf-8')
    first_line, body = txt.split('\n', 1)
    approved = ARTIFACT_APPROVED_TOKEN in first_line
    or_edit = ARTIFACT_EDIT_REQUESTED_TOKEN in first_line
    if not (approved or or_edit):
        path.unlink()
        logger.warning(f"Artifact {video_id} non approuve, supprime.")
        return False, []
    
    tweets = []
    for line in body.splitlines():
        line = line.strip()
        if not line: continue
        parts = line.split(' | ', 2)
        if len(parts) >= 3:
            tweets.append(parts[2])
    
    if approved:
        path.unlink()
    return True, tweets

def review_thread(tweets: List[str], video_id: str) -> List[str]:
    """Affiche chaque tweet avec son nombre de caracteres. Demande a l'utilisateur: y -> publier n -> skip edit -> teleporter dans le fichier artifact."""
    print("\n" + "="*60)
    print(f"THREAD GENERE - {CHANNEL_NAME}")
    print("="*60)
    for i, t in enumerate(tweets, 1):
        print(f"\n[{i}/{len(tweets)}] ({len(t)} chars)")
        print(t)
    print("="*60)
    while True:
        choice = input("y = publier / n = skip / edit = modifier: ").strip().lower()
        if choice == 'y':
            return tweets
        elif choice == 'n':
            logger.info("Thread skippe par l'utilisateur.")
            return []
        elif choice == 'edit':
            path = save_artifact(video_id, tweets)
            print(f"Edit possible dans le fichier artifact. Sauvegardez avec APPROVED.")
            return tweets
        else:
            print("Choix invalide.")

# ============================================================================
# X POSTING
# ============================================================================
def clean_tweet(text: str) -> str:
    """Nettoie le texte avant envoi a l'API X."""
    return text.replace('\n', ' ').strip()

def post_thread(tweets: List[str]) -> None:
    """Publie le thread complet (1er tweet + replies) avec sleep entre chaque."""
    parent_id = None
    for i, t in enumerate(tweets, 1):
        clean = clean_tweet(t)
        for attempt in range(X_MAX_RETRIES):
            try:
                if parent_id is None:
                    resp = XBot.create_tweet(text=clean)
                else:
                    resp = XBot.create_tweet(text=clean, in_reply_to_tweet_id=parent_id)
                parent_id = resp.data['id']
                logger.info(f"Tweet {i}/{len(tweets)} poste, ID: {parent_id}")
                break
            except Exception as e:
                logger.warning(f"Echec tweet {i}: {e}")
                if attempt < X_MAX_RETRIES - 1:
                    time.sleep(X_TWEET_DELAY_SECONDS)
        if i < len(tweets):
            time.sleep(X_TWEET_DELAY_SECONDS)
    logger.info("Thread completes sur X.")

# ============================================================================
# OUTPUT / ENV
# ============================================================================
def print_env_diagnosis():
    """Affiche l'etat des variables d'environnement necessaires."""
    required = ['X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_SECRET', 'GEMINI_API_KEY']
    print("\nENV DIAGNOSIS:")
    for k in required:
        if os.environ.get(k):
            print(f" {k}: OK")
        else:
            print(f" {k}: MISSING !")

# ============================================================================
# MAIN LOOP
# ============================================================================
def check_for_new_video() -> Optional[Dict[str, str]]:
    """Interroge le RSS et ne retourne la video que si elle est nouvelle (non dans POSTED_DB ni dans PLANNING_DB)."""
    latest = fetch_latest_video()
    if not latest:
        return None
    posted = load_json(POSTED_DB_PATH, POSTED_DB_DEFAULT)
    planning = load_json(PLANNING_DB_PATH, PLANNING_DB_DEFAULT)
    vid = latest['video_id']
    
    for p in posted.get('videos', []):
        if p['video_id'] == vid:
            logger.info(f"Video {vid} deja postee.")
            return None
    for p in planning:
        if p['video_id'] == vid:
            logger.info(f"Video {vid} deja en planification.")
            return None
            
    logger.info(f"Nouvelle video detectee: {latest['title']}")
    return latest

def main():
    """Point d'entree principal. Executable localement ou via GitHub Actions."""
    logger.info("--- Brighter X Autopost demarre ---")
    print_env_diagnosis()
    if not gen_client:
        logger.error("Gemini non configure. Arret.")
        return

    # 0. Review artifact precedent (mode asynchrone)
    if os.path.exists(ARTIFACT_DIR):
        for f in Path(ARTIFACT_DIR).glob("thread_*.txt"):
            vid = f.stem.replace("thread_", "")
            approved, tweets = load_artifact(vid)
            if approved and tweets:
                logger.info(f"Publication thread approuve pour {vid}.")
                post_thread(tweets)
                posted = load_json(POSTED_DB_PATH, POSTED_DB_DEFAULT)
                posted['videos'].append({'video_id': vid, 'posted_at': datetime.now().isoformat()})
                save_json(POSTED_DB_PATH, posted)
                logger.info("Video marquee comme postee.")
                return

    # 1. Detection nouvelle video
    video = check_for_new_video()
    if not video:
        logger.info("Rien de nouveau.")
        return

    # 2. Transcript
    title = video['title']
    link = video['link']
    vid = video['video_id']
    transcript = extract_transcript_with_fallback(vid)

    # 3. IA
    tweets = generate_thread_with_ai(title, transcript, link)
    if not tweets:
        logger.error("Thread vide, abandon.")
        return

    # 4. Review humaine
    final = review_thread(tweets, vid)
    if not final:
        logger.info("Thread annule par l'utilisateur.")
        return

    # 5. Publication
    post_thread(final)

    # 6. Sauvegarde tracking
    posted = load_json(POSTED_DB_PATH, POSTED_DB_DEFAULT)
    posted['videos'].append({
        'video_id': vid,
        'title': title,
        'posted_at': datetime.now().isoformat(),
    })
    save_json(POSTED_DB_PATH, posted)
    logger.info("--- Brighter X Autopost termine ---")

if __name__ == '__main__':
    main()
