import os
import json
import time
from datetime import datetime
import feedparser
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# ===================== CONFIG =====================
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UC4DBLlq1x0AKmip1QJUcbXg"
ARTIFACTS_DIR = "artifacts"

os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# Configuration Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ===================== FONCTIONS =====================

def load_db():
    """Charge la DB avec gestion robuste des erreurs."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
            
            # Normalisation robuste
            if not isinstance(db, dict):
                db = {}
            if "posted" not in db or not isinstance(db.get("posted"), list):
                db["posted"] = []
            
            return db
        except (json.JSONDecodeError, IOError, Exception) as e:
            print(f"⚠️ Fichier {DB_FILE} corrompu ou illisible ({e}). Réinitialisation.")
            return {"posted": []}
    
            return db
        except Exception as e:
            print(f"⚠️ Fichier {DB_FILE} corrompu ({e}). Réinitialisation.")
            return {"posted": []}
    return {"posted": []}


def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)
        json.dump(db, f, indent=2, ensure_ascii=False)


def get_latest_video():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return None
    entry = feed.entries[0]
    return {
        "id": entry.yt_videoid,
        "title": entry.title,
        "url": entry.link
    }


def get_transcript(video_id):
    """Récupère le transcript avec plusieurs fallbacks."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Méthode 1 : Liste des transcripts disponibles
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en', 'fr'])
        data = transcript.fetch()
        return " ".join([entry['text'] for entry in data])
    except Exception as e:
        print(f"⚠️ Première méthode transcript échouée: {e}")
        
        # Méthode 2 : Fallback simple
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'fr'])
            return " ".join([entry['text'] for entry in data])
        except Exception as e2:
            print(f"⚠️ Tous les essais de transcript ont échoué: {e2}")
            return None


def generate_thread_with_gemini(title, transcript, video_url):
    prompt = f"""Tu es un expert Tesla, SpaceX, Optimus et AI qui crée du contenu viral sur X pour @aurel99.

Crée un thread X complet et prêt à publier.

**RÈGLES STRICTES :**
- Chaque tweet doit faire moins de 260 caractères
- Format obligatoire : 1/N, 2/N, ..., N/N
- Thread entre 3 et 8 tweets
- Ton engageant, optimiste, avec insights investing
- Français principal, termes Tesla en anglais
- Dernier tweet : CTA + hashtags (#Tesla #TSLA #Optimus #Robotaxi #FSD #SpaceX) + @aurel99
- Sépare chaque tweet par ---

Titre : {title}
Lien : {video_url}
Transcript : {transcript[:18000] if transcript else "Pas de transcript disponible"}

Réponds UNIQUEMENT avec le thread, séparé par ---. Pas d'introduction ni d'explication."""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        raw = response.text.strip()
        
        # Parsing robuste
        tweets = [t.strip() for t in raw_thread.split('---') if t.strip()]
        return tweets
    except Exception as e:
        print(f"❌ Erreur Gemini: {e}")
        return None


def save_artifact(video_id, title, tweets):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ARTIFACTS_DIR}/{timestamp}_{video_id[:8]}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Titre: {title}\nVideo ID: {video_id}\nDate: {datetime.now()}\n\n")
        for i, tweet in enumerate(tweets, 1):
            f.write(f"Tweet {i}/{len(tweets)} ({len(tweet)} chars):\n{tweet}\n\n")
    print(f"✅ Artifact sauvegardé : {filename}")
    return filename

def post_thread(tweets):
    print("🔄 Simulation de publication du thread...")
    for tweet in tweets:
        print(f"→ {tweet[:100]}...")
    return True

def main():
    db = load_db()
    video = get_latest_video()
    
    if not video or video["id"] in db.get("posted", []):
        print("✅ Aucune nouvelle vidéo.")
        return

    print(f"🎥 Nouvelle vidéo détectée : {video['title']}")

    transcript = get_transcript(video["id"])
    if not transcript:
        print("❌ Impossible d'obtenir le transcript. Passage en mode description seulement (limité).")
        # On continue quand même avec un thread minimal

    print(f"🎥 Nouvelle vidéo détectée : {video['title']}")
    tweets = generate_thread_with_gemini(video["title"], transcript, video["url"])
    if not tweets:
        print("❌ Échec génération thread.")
        return

    artifact_file = save_artifact(video["id"], video["title"], tweets)

    # Review humaine
    print("\n" + "="*80)
    print("🧐 REVIEW HUMAINE - Thread prêt :")
    print("="*80)
    for i, tweet in enumerate(tweets):
        print(f"\nTweet {i+1}/{len(tweets)} ({len(tweet)} chars):")
        print(tweet)
        print("-" * 70)

    approval = input("\nPublier ce thread ? (y/n) : ").lower()
    if approval == 'y':
        if post_thread(tweets):
            db["posted"].append(video["id"])
            save_db(db)
            print("✅ Thread publié avec succès !")
    else:
        print("⏭️ Publication annulée.")

if __name__ == "__main__":
    main()
