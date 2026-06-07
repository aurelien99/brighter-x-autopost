import os
import json
from datetime import datetime
import feedparser
from dotenv import load_dotenv

load_dotenv()

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UC4DBLlq1x0AKmip1QJUcbXg"
DB_FILE = "posted_videos.json"
ARTIFACTS_DIR = "artifacts"

os.makedirs(ARTIFACTS_DIR, exist_ok=True)

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
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'fr'])
        text = " ".join(item['text'] for item in transcript)
        print(f"✅ Transcript OK ({len(text)} chars)")
        return text
    except Exception as e:
        print(f"⚠️ Transcript non disponible : {e}")
        return None

def create_thread(title, url):
    """Thread de qualité (même sans transcript)"""
    return [
        f"1/5 🔥 Nouvelle vidéo @BrighterwithHerbert : {title[:110]}...",
        f"2/5 Regardez l'analyse complète → {url}",
        "3/5 SpaceX continue-t-il de surprendre les investisseurs ?",
        "4/5 Quel est votre avis sur le futur de Starship et Optimus ?",
        f"5/5 #Tesla #SpaceX #Optimus #FSD @aurel99"
    ]

def save_artifact(video_id, title, tweets):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ARTIFACTS_DIR}/{timestamp}_{video_id[:8]}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Titre: {title}\n\n")
        for i, tweet in enumerate(tweets, 1):
            f.write(f"Tweet {i}/{len(tweets)} ({len(tweet)} chars):\n{tweet}\n\n")
    print(f"✅ Thread sauvegardé → {filename}")

def main():
    db = load_db()
    video = get_latest_video()
    
    if not video or video["id"] in db.get("posted", []):
        print("✅ Aucune nouvelle vidéo.")
        return

    print(f"🎥 Vidéo détectée : {video['title']}")

    transcript = get_transcript(video["id"])
    tweets = create_thread(video["title"], video["url"])

    save_artifact(video["id"], video["title"], tweets)

    print("\n" + "="*90)
    print("🧐 THREAD PRÊT POUR REVIEW")
    print("="*90)
    for i, t in enumerate(tweets, 1):
        print(f"\nTweet {i} ({len(t)} chars):\n{t}\n")

if __name__ == "__main__":
    main()
