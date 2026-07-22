import json
import os
import random

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
LEVELS = ["N5", "N4", "N3", "N2", "N1"]

LEVEL_INFO = {
    "N5": {"color": "#22C55E", "label": "Beginner", "desc": "Basic phrases, hiragana, katakana and ~100 kanji. Understand everyday expressions spoken slowly.", "vocab_goal": 800, "kanji_goal": 100, "study_hours": "150–300"},
    "N4": {"color": "#84CC16", "label": "Elementary", "desc": "Everyday conversation, ~300 kanji and ~1,500 words. Read simple passages on familiar topics.", "vocab_goal": 1500, "kanji_goal": 300, "study_hours": "300–600"},
    "N3": {"color": "#F59E0B", "label": "Intermediate", "desc": "The bridge level. Understand newspapers headlines, everyday conversations at natural speed.", "vocab_goal": 3700, "kanji_goal": 650, "study_hours": "450–900"},
    "N2": {"color": "#F97316", "label": "Upper Intermediate", "desc": "Business-ready. Read newspapers and magazines, follow TV news and native-speed conversation.", "vocab_goal": 6000, "kanji_goal": 1000, "study_hours": "600–1,500"},
    "N1": {"color": "#EF4444", "label": "Advanced", "desc": "Near-native comprehension. Abstract writing, editorials, complex discussions in any context.", "vocab_goal": 10000, "kanji_goal": 2000, "study_hours": "900–2,600"},
}


def load(name):
    with open(os.path.join(DATA_DIR, f"{name}.json"), encoding="utf-8") as f:
        return json.load(f)


KANA = load("kana")
VOCAB = load("vocab")
KANJI = load("kanji")
GRAMMAR = load("grammar")

KANA_FLAT = {
    script: [k for group in groups.values() for k in group if k]
    for script, groups in KANA.items()
}


# ---------- pages ----------

@app.route("/")
def index():
    stats = {
        "vocab": sum(len(v) for v in VOCAB.values()),
        "kanji": sum(len(v) for v in KANJI.values()),
        "grammar": sum(len(v) for v in GRAMMAR.values()),
        "kana": sum(len(v) for v in KANA_FLAT.values()),
    }
    return render_template("index.html", stats=stats, levels=LEVELS, level_info=LEVEL_INFO)


@app.route("/kana")
def kana_page():
    return render_template("kana.html", kana=KANA)


@app.route("/flashcards")
def flashcards_page():
    return render_template("flashcards.html", levels=LEVELS)


@app.route("/quiz")
def quiz_page():
    return render_template("quiz.html", levels=LEVELS)


@app.route("/matching")
def matching_page():
    return render_template("matching.html", levels=LEVELS)


@app.route("/typing")
def typing_page():
    return render_template("typing.html", levels=LEVELS)


@app.route("/listening")
def listening_page():
    return render_template("listening.html", levels=LEVELS)


@app.route("/kanji")
def kanji_page():
    return render_template("kanji.html", kanji=KANJI, levels=LEVELS, level_info=LEVEL_INFO)


@app.route("/grammar")
def grammar_page():
    return render_template("grammar.html", grammar=GRAMMAR, levels=LEVELS, level_info=LEVEL_INFO)


@app.route("/roadmap")
def roadmap_page():
    return render_template("roadmap.html", levels=LEVELS, level_info=LEVEL_INFO)


@app.route("/progress")
def progress_page():
    return render_template("progress.html")


# ---------- APIs ----------

def pick_level(default="N5"):
    lvl = request.args.get("level", default).upper()
    return lvl if lvl in LEVELS else default


@app.route("/api/vocab")
def api_vocab():
    lvl = pick_level()
    return jsonify({"level": lvl, "words": VOCAB[lvl]})


@app.route("/api/kana")
def api_kana():
    script = request.args.get("script", "hiragana")
    if script not in KANA_FLAT:
        script = "hiragana"
    return jsonify({"script": script, "kana": KANA_FLAT[script]})


@app.route("/api/quiz")
def api_quiz():
    """Multiple-choice questions. mode: meaning | reading | reverse | kanji"""
    lvl = pick_level()
    mode = request.args.get("mode", "meaning")
    count = min(int(request.args.get("count", 10)), 20)

    questions = []
    if mode == "kanji":
        pool = KANJI[lvl]
        chosen = random.sample(pool, min(count, len(pool)))
        for item in chosen:
            wrong = random.sample([k["meaning"] for k in pool if k["kanji"] != item["kanji"]], 3)
            options = wrong + [item["meaning"]]
            random.shuffle(options)
            questions.append({
                "prompt": item["kanji"],
                "sub": "What does this kanji mean?",
                "speak": item["example"].split(" ")[0],
                "options": options,
                "answer": item["meaning"],
                "explain": f"{item['kanji']} — on: {item['onyomi']} / kun: {item['kunyomi']} • {item['example']}",
            })
    else:
        pool = VOCAB[lvl]
        chosen = random.sample(pool, min(count, len(pool)))
        for item in chosen:
            if mode == "reading":
                wrong = random.sample([w["kana"] for w in pool if w["kana"] != item["kana"]], 3)
                options = wrong + [item["kana"]]
                q = {"prompt": item["word"], "sub": "Choose the correct reading",
                     "speak": item["word"], "answer": item["kana"]}
            elif mode == "reverse":
                wrong = random.sample([w["word"] for w in pool if w["word"] != item["word"]], 3)
                options = wrong + [item["word"]]
                q = {"prompt": item["meaning"], "sub": "Choose the Japanese word",
                     "speak": None, "answer": item["word"]}
            else:  # meaning
                wrong = random.sample([w["meaning"] for w in pool if w["meaning"] != item["meaning"]], 3)
                options = wrong + [item["meaning"]]
                q = {"prompt": item["word"], "sub": f"({item['kana']}) — what does it mean?",
                     "speak": item["word"], "answer": item["meaning"]}
            random.shuffle(options)
            q["options"] = options
            q["explain"] = f"{item['word']}（{item['kana']}） = {item['meaning']} [{item['romaji']}]"
            questions.append(q)

    return jsonify({"level": lvl, "mode": mode, "questions": questions})


@app.route("/api/matching")
def api_matching():
    """Pairs for the memory game. type: kana | vocab"""
    lvl = pick_level()
    kind = request.args.get("type", "vocab")
    pairs = int(request.args.get("pairs", 8))
    if kind == "kana":
        script = request.args.get("script", "hiragana")
        pool = KANA_FLAT.get(script, KANA_FLAT["hiragana"])
        chosen = random.sample(pool, min(pairs, len(pool)))
        out = [{"a": c["kana"], "b": c["romaji"], "speak": c["kana"]} for c in chosen]
    else:
        pool = VOCAB[lvl]
        chosen = random.sample(pool, min(pairs, len(pool)))
        out = [{"a": c["word"], "b": c["meaning"], "speak": c["word"]} for c in chosen]
    return jsonify({"pairs": out})


@app.route("/api/typing")
def api_typing():
    """Items for the typing game. type: kana | vocab"""
    lvl = pick_level()
    kind = request.args.get("type", "kana")
    count = min(int(request.args.get("count", 15)), 40)
    if kind == "vocab":
        pool = VOCAB[lvl]
        chosen = random.sample(pool, min(count, len(pool)))
        items = [{"show": c["word"], "hint": c["meaning"], "accept": [c["romaji"].lower()], "speak": c["word"]}
                 for c in chosen]
    else:
        script = request.args.get("script", "hiragana")
        pool = KANA_FLAT.get(script, KANA_FLAT["hiragana"])
        chosen = random.sample(pool, min(count, len(pool)))
        items = []
        for c in chosen:
            accept = {c["romaji"].lower()}
            alt = {"shi": "si", "chi": "ti", "tsu": "tu", "fu": "hu", "ji": "zi",
                   "sha": "sya", "shu": "syu", "sho": "syo",
                   "cha": "tya", "chu": "tyu", "cho": "tyo",
                   "ja": "zya", "ju": "zyu", "jo": "zyo"}
            if c["romaji"] in alt:
                accept.add(alt[c["romaji"]])
            items.append({"show": c["kana"], "hint": None, "accept": sorted(accept), "speak": c["kana"]})
    return jsonify({"items": items})


@app.route("/api/listening")
def api_listening():
    """Listening rounds: hear the word (TTS on client), pick what you heard."""
    lvl = pick_level()
    count = min(int(request.args.get("count", 10)), 20)
    pool = VOCAB[lvl]
    chosen = random.sample(pool, min(count, len(pool)))
    rounds = []
    for item in chosen:
        wrong = random.sample([w for w in pool if w["word"] != item["word"]], 3)
        options = [{"word": w["word"], "kana": w["kana"], "meaning": w["meaning"]} for w in wrong]
        options.append({"word": item["word"], "kana": item["kana"], "meaning": item["meaning"]})
        random.shuffle(options)
        rounds.append({"speak": item["kana"], "answer": item["word"], "options": options,
                       "explain": f"{item['word']}（{item['kana']}） = {item['meaning']}"})
    return jsonify({"level": lvl, "rounds": rounds})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
