import os
import json
import time
from datetime import datetime
import feedparser
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Config
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UC4DBLlq1x0AKmip1QJUcbXg"
DB_FILE = "posted_videos.json"
ARTIFACTS_DIR = "artifacts"

os.makedirs(ARTIFACTS_DIR, exist_ok=True)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def load_db():
    """Charge la DB avec gestion robuste des erreurs."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
            
            if not isinstance(db, dict):
                db = {}
            if "posted" not in db or not isinstance(db.get("posted"), list):
                db["posted"] = []
            
            return db
        except Exception as e:
            print(f"⚠️ Fichier {DB_FILE} corrompu ({e}). Réinitialisation.")
            return {"posted": []}
    
    return {"posted": []}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
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
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'fr'])
        return " ".join([t['text'] for t in transcript])
    except Exception as e:
        print(f"⚠️ Transcript error: {e}")
        return None

def generate_thread_with_gemini(title, transcript, video_url):
    prompt = f"""Tu es un expert Tesla, SpaceX, Optimus et AI qui crée du contenu viral sur X pour @aurel99.

Crée un thread X complet et prêt à publier.

**RÈGLES STRICTES :**
- Chaque tweet < 260 caractères
- Format : 1/N, 2/N, ..., N/N
- Thread de 3 à 8 tweets
- Ton engageant, optimiste, insights investing
- Français principal, termes Tesla en anglais
- Dernier tweet : CTA + hashtags + @aurel99
- Sépare chaque tweet par ---

Titre : {title}
Lien : {video_url}
Transcript : {transcript[:18000]}

Réponds UNIQUEMENT avec le thread, séparé par ---"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        raw = response.text.strip()
        
        tweets = [t.strip() for t in raw.split('---') if t.strip() and len(t.strip()) > 5]
        return tweets
    except Exception as e:
        print(f"❌ Erreur Gemini: {e}")
        return None

def save_artifact(video_id, title, tweets):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ARTIFACTS_DIR}/{timestamp}_{video_id[:8]}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Titre: {title}\nVideo ID: {video_id}\n\n")
        for i, tweet in enumerate(tweets, 1):
            f.write(f"Tweet {i}/{len(tweets)} ({len(tweet)} chars):\n{tweet}\n\n")
    print(f"✅ Artifact sauvegardé : {filename}")
    return filename

def main():
    db = load_db()
    video = get_latest_video()
    
    if not video or video["id"] in db.get("posted", []):
        print("✅ Aucune nouvelle vidéo à traiter.")
        return

    print(f"🎥 Nouvelle vidéo détectée : {video['title']}")

    transcript = get_transcript(video["id"])
    if not transcript:
        print("❌ Impossible d'obtenir le transcript.")
        return

    tweets = generate_thread_with_gemini(video["title"], transcript, video["url"])
    if not tweets:
        print("❌ Échec de la génération du thread.")
        return

    artifact_file = save_artifact(video["id"], video["title"], tweets)

    print("\n" + "="*80)
    print("🧐 REVIEW HUMAINE - Thread prêt")
    print("="*80)
    for i, tweet in enumerate(tweets, 1):
        print(f"\nTweet {i}/{len(tweets)} ({len(tweet)} chars):")
        print(tweet)
        print("-" * 60)

    approval = input("\nPublier ce thread sur X ? (y/n) : ").lower().strip()
    if approval == 'y':
        # Publication Tweepy à implémenter plus tard
        print("🔄 Publication simulée (Tweepy non encore activé)")
        db.setdefault("posted", []).append(video["id"])
        save_db(db)
        print("✅ Vidéo marquée comme traitée.")
    else:
        print("⏭️ Publication annulée.")

if __name__ == "__main__":
    main()
