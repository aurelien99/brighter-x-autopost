# Brighter X Autopost

Automatisez la publication de threads X (Twitter) a partir des nouvelles videos de la chaine YouTube **Brighter with Herbert**.

## Fonctionnalites

- **Detection RSS**: Surveillance automatique du flux RSS YouTube toutes les 3 heures
- **Extraction de transcript**: Recuperation via youtube-transcript-api
- **Generation IA**: Threads X optimises via Claude API (Anthropic)
- **Revue humaine**: Validation manuelle avant publication
- **Publication auto**: Thread complet poste sur X via Tweepy
- **Anti-doublons**: Tracking JSON des videos deja traitees
- **Logs & Artifacts**: Historique detaille dans artifacts/

## Structure du projet

```
brighter-x-autopost/
|-- config.py              # Config + Prompts master
|-- main.py                # Script principal
|-- requirements.txt       # Dependances
|-- .env.example           # Template env
|-- .gitignore
|-- .github/
|   |-- workflows/
|       |-- post-brighter.yml
|-- artifacts/             # Logs, transcripts (auto)
|-- posted_videos.json     # DB videos (auto)
+-- README.md
```

## Pipeline (6 etapes)

1. **Detection RSS** -> Flux RSS YouTube Brighter with Herbert
2. **Transcript** -> Extraction via youtube-transcript-api
3. **Generation IA** -> Thread X optimise via Claude API
4. **Revue humaine** -> Validation console
5. **Publication** -> Thread complet sur X via Tweepy
6. **Tracking** -> posted_videos.json + logs

## Prompt MASTER

Impositions du PROMPT MASTER:
- Format 1/N, 2/N... N/N obligatoire
- Maximum 260 caracteres par tweet
- Thread de 3 a 8 tweets
- Lien YouTube en fin de thread
- Hashtags pertinents
- Ton engageant, Francais principal, termes tech Tesla en anglais

## Configuration

### Variables d'environnement

```bash
# X (Twitter) API credentials
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_secret

# Anthropic API key
ANTHROPIC_API_KEY=your_anthropic_key

# Options
AI_MODEL=claude-3-5-sonnet-20241022
AUTO_PUBLISH=false
```
### GitHub Secrets

Allez dans **Settings > Secrets and variables > Actions**:

| Secret | Description |
|--------|-------------|
| X_API_KEY | Cle X API v2 |
| X_API_SECRET | Secret X API |
| X_ACCESS_TOKEN | Token d'acces |
| X_ACCESS_SECRET | Secret du token |
| ANTHROPIC_API_KEY | Cle API Anthropic |

### Installation locale

```bash
git clone https://github.com/aurelien99/brighter-x-autopost.git
cd brighter-x-autopost
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Editez .env avec vos cles
python main.py
```
## GitHub Actions

Le workflow `.github/workflows/post-brighter.yml` s'execute:
- **Automatiquement** toutes les 3 heures (cron: 0 */3 * * *)
- **Manuellement** via Actions > Run workflow

## Test manuel

```bash
# Mode review: genere le thread, demande validation
python main.py

# Mode auto-publish: publie directement
AUTO_PUBLISH=true python main.py
```

## Dependances

- feedparser - Lecture des flux RSS
- youtube-transcript-api - Extraction des transcripts YouTube
- anthropic - API Claude pour la generation IA
- tweepy - Publication sur X (Twitter)

## License

MIT - Usage personnel et commercial autorise.
