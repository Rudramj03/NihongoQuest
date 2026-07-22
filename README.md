# NihongoQuest 🇯🇵

A self-hosted Japanese learning web app covering the full JLPT range (N5–N1). Study kana, vocabulary, kanji and grammar through flashcards, quizzes, matching games, typing drills and listening practice.

**Live:** https://nihongo.13-61-25-153.sslip.io

## Features

- **Kana charts** — hiragana and katakana reference tables
- **Flashcards** — vocab review by JLPT level
- **Quiz** — multiple-choice questions on vocab, kanji and grammar
- **Matching** — pair Japanese words with their meanings
- **Typing** — type the romaji/reading for prompted words
- **Listening** — audio-based comprehension rounds (browser TTS)
- **Kanji & Grammar browsers** — searchable lists per level
- **Roadmap & Progress** — JLPT level goals and study tracking (stored in localStorage)
- **Android app** — WebView wrapper APK, downloadable from the site

All learning content lives in JSON files under `data/` (`kana.json`, `vocab.json`, `kanji.json`, `grammar.json`), keyed by JLPT level.

## Tech stack

- **Backend:** Flask (Python), no database — content loaded from JSON at startup
- **Frontend:** Jinja2 templates + vanilla JS/CSS, installable as a PWA
- **Serving:** gunicorn behind nginx, managed with PM2 (`ecosystem.config.js`)

## Running locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py          # dev server on http://localhost:5001
```

Production:

```bash
gunicorn -b 127.0.0.1:5001 app:app
```

## Project layout

```
app.py                 # Flask app: pages + JSON APIs (quiz, matching, typing, listening)
data/                  # learning content per JLPT level
templates/             # Jinja2 pages
static/                # CSS, JS, PWA icons, Android APK
android/               # manual Android build (aapt2/d8, no Gradle) — see android/build.sh
ecosystem.config.js    # PM2 process config
```

## Android APK

The `android/` directory contains a minimal WebView app built directly with `aapt2` and `d8` (no Gradle). Run `android/build.sh` to build; the signed APK is served from `/static/app/` for download from the site.
