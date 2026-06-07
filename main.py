import os
import json
from datetime import datetime
import feedparser
from dotenv import load_dotenv

load_dotenv()

# ===================== CONFIG =====================
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UC4DBLlq1x0AKmip1QJUcbXg"
DB_FILE = "posted_videos.json"
ARTIFACTS_DIR = "artifacts"

os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# ===================== GEMINI (SDK 2026) =====================
try:
    from google import genai
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    print("✅ Nouveau SDK Google GenAI chargé")
except ImportError:
    print("⚠️ Ancien SDK détecté")
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    gemini_client = None

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
            return db if isinstance(db, dict) else {"posted": []}
        except:
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
    """Version mise à jour 2026"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        # Méthode recommandée actuelle
        data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'fr'])
        return " ".join([entry['text'] for entry in data])
    except Exception as e:
        print(f"⚠️ Transcript error: {e}")
        return None

def generate_thread(title, transcript, video_url):
    prompt = f"""Tu es un expert Tesla/SpaceX qui crée du contenu viral sur X pour @aurel99.

Crée un thread X complet et prêt à publier.

**RÈGLES STRICTES :**
- Chaque tweet < 260 caractères
- Format : 1/N, 2/N, ..., N/N
- 4 à 7 tweets maximum
- Ton engageant et optimiste avec insights investing
- Français principal, termes Tesla en anglais
- Dernier tweet avec CTA + hashtags + @aurel99
- Sépare chaque tweet par ---

Titre : {title}
Lien : {video_url}
Transcript : {transcript[:16000] if transcript else "Pas de transcript disponible"}

Réponds UNIQUEMENT avec le thread, rien d'autre."""

    try:
        if gemini_client:  # Nouveau SDK
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=[prompt]
            )
            raw = response.text
        else:  # Ancien SDK fallback
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            raw = response.text

        tweets = [t.strip() for t in raw.split('---') if t.strip() and len(t.strip()) > 15]
        return tweets
    except Exception as e:
        print(f"❌ Erreur Gemini: {e}")
        return None

def save_artifact(video_id, title, tweets):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ARTIFACTS_DIR}/{timestamp}_{video_id[:8]}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Titre: {title}\n\n")
        for i, tweet in enumerate(tweets, 1):
            f.write(f"Tweet {i}/{len(tweets)} ({len(tweet)} chars):\n{tweet}\n\n")
    print(f"✅ Artifact sauvegardé : {filename}")

def main():
    db = load_db()
    video = get_latest_video()
    
    if not video or video["id"] in db.get("posted", []):
        print("✅ Aucune nouvelle vidéo à traiter.")
        return

    print(f"🎥 Nouvelle vidéo détectée : {video['title']}")

    transcript = get_transcript(video["id"])
    if not transcript:
        print("⚠️ Pas de transcript → thread basé sur titre uniquement")

    tweets = generate_thread(video["title"], transcript, video["url"])

    if not tweets:
        print("❌ Échec de la génération du thread.")
        return

    save_artifact(video["id"], video["title"], tweets)

    print("\n" + "="*80)
    print("🧐 THREAD GÉNÉRÉ (Review)")
    print("="*80)
    for i, t in enumerate(tweets, 1):
        print(f"\n[{i}/{len(tweets)}] ({len(t)} chars)")
        print(t)
        print("-" * 60)

if __name__ == "__main__":
    main()
