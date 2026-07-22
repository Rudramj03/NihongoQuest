/* ============ NihongoQuest shared engine: TTS, SFX, XP, confetti ============ */
window.NQ = (() => {

  /* ---------- Japanese text-to-speech (Web Speech API) ---------- */
  let jpVoice = null;
  function pickVoice() {
    const voices = speechSynthesis.getVoices();
    jpVoice =
      voices.find(v => v.lang === "ja-JP" && /Google|Kyoko|Otoya|Haruka|Nanami/i.test(v.name)) ||
      voices.find(v => v.lang === "ja-JP") ||
      voices.find(v => v.lang.startsWith("ja")) || null;
  }
  if ("speechSynthesis" in window) {
    pickVoice();
    speechSynthesis.onvoiceschanged = pickVoice;
  }

  function speak(text, rate = 0.9) {
    if (!text) return;
    // Android app: native TTS bridge (WebView has no speechSynthesis)
    if (window.AndroidTTS && typeof window.AndroidTTS.speak === "function") {
      try { window.AndroidTTS.speak(text, rate); return; } catch (e) { /* fall through */ }
    }
    if (!("speechSynthesis" in window)) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "ja-JP";
    if (jpVoice) u.voice = jpVoice;
    u.rate = rate;
    u.pitch = 1.05;
    speechSynthesis.speak(u);
  }

  /* ---------- sound effects (WebAudio synth — no files needed) ---------- */
  let ctx = null;
  const soundKey = "nq_sound";
  let soundOn = localStorage.getItem(soundKey) !== "off";

  function ac() {
    if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  }
  function tone(freq, start, dur, type = "sine", gainVal = 0.16) {
    const a = ac();
    const o = a.createOscillator();
    const g = a.createGain();
    o.type = type;
    o.frequency.value = freq;
    g.gain.setValueAtTime(0, a.currentTime + start);
    g.gain.linearRampToValueAtTime(gainVal, a.currentTime + start + 0.015);
    g.gain.exponentialRampToValueAtTime(0.001, a.currentTime + start + dur);
    o.connect(g).connect(a.destination);
    o.start(a.currentTime + start);
    o.stop(a.currentTime + start + dur + 0.05);
  }
  const sfx = {
    click()   { if (soundOn) tone(660, 0, 0.08, "triangle", 0.1); },
    flip()    { if (soundOn) { tone(440, 0, 0.09, "sine", 0.1); tone(590, 0.06, 0.1, "sine", 0.1); } },
    correct() { if (soundOn) { tone(523, 0, 0.12, "triangle"); tone(659, 0.09, 0.12, "triangle"); tone(784, 0.18, 0.2, "triangle"); } },
    wrong()   { if (soundOn) { tone(220, 0, 0.18, "sawtooth", 0.09); tone(180, 0.12, 0.25, "sawtooth", 0.09); } },
    fanfare() {
      if (!soundOn) return;
      [523, 659, 784, 1047].forEach((f, i) => tone(f, i * 0.12, 0.25, "triangle", 0.14));
      [392, 523].forEach((f, i) => tone(f, 0.5 + i * 0.12, 0.35, "sine", 0.12));
    },
  };

  /* ---------- XP / progress store (localStorage) ---------- */
  const storeKey = "nq_progress";
  function getStore() {
    try { return JSON.parse(localStorage.getItem(storeKey)) || {}; }
    catch { return {}; }
  }
  function saveStore(s) { localStorage.setItem(storeKey, JSON.stringify(s)); }

  function today() { return new Date().toISOString().slice(0, 10); }

  function ensure() {
    const s = getStore();
    s.xp = s.xp || 0;
    s.games = s.games || {};
    s.days = s.days || {};
    s.streak = s.streak || 0;
    s.lastDay = s.lastDay || null;
    return s;
  }

  function addXP(amount, game) {
    const s = ensure();
    s.xp += amount;
    if (game) {
      s.games[game] = s.games[game] || { plays: 0, xp: 0 };
      s.games[game].plays += 1;
      s.games[game].xp += amount;
    }
    const t = today();
    if (s.lastDay !== t) {
      const yest = new Date(Date.now() - 864e5).toISOString().slice(0, 10);
      s.streak = s.lastDay === yest ? s.streak + 1 : 1;
      s.lastDay = t;
    }
    s.days[t] = (s.days[t] || 0) + amount;
    saveStore(s);
    renderXP();
    return s;
  }

  const LEVEL_STEP = 250; // XP per learner level
  function learnerLevel(xp) { return Math.floor(xp / LEVEL_STEP) + 1; }

  function renderXP() {
    const el = document.getElementById("xpValue");
    if (el) el.textContent = ensure().xp.toLocaleString();
  }

  /* ---------- confetti ---------- */
  function confetti(count = 90) {
    const cv = document.getElementById("confettiCanvas");
    if (!cv) return;
    const c = cv.getContext("2d");
    cv.width = innerWidth; cv.height = innerHeight;
    const colors = ["#4F46E5", "#818CF8", "#22C55E", "#F59E0B", "#EF4444", "#EC4899"];
    const parts = Array.from({ length: count }, () => ({
      x: Math.random() * cv.width, y: -20 - Math.random() * 140,
      vx: (Math.random() - 0.5) * 3, vy: 2 + Math.random() * 3.5,
      s: 6 + Math.random() * 7, r: Math.random() * Math.PI,
      vr: (Math.random() - 0.5) * 0.25,
      col: colors[(Math.random() * colors.length) | 0],
    }));
    let frames = 0;
    (function draw() {
      c.clearRect(0, 0, cv.width, cv.height);
      parts.forEach(p => {
        p.x += p.vx; p.y += p.vy; p.r += p.vr;
        c.save(); c.translate(p.x, p.y); c.rotate(p.r);
        c.fillStyle = p.col; c.fillRect(-p.s / 2, -p.s / 2, p.s, p.s * 0.6);
        c.restore();
      });
      if (++frames < 210) requestAnimationFrame(draw);
      else c.clearRect(0, 0, cv.width, cv.height);
    })();
  }

  /* ---------- toast ---------- */
  let toastTimer;
  function toast(msg) {
    const t = document.getElementById("toast");
    if (!t) return;
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 2600);
  }

  /* ---------- chrome wiring ---------- */
  document.addEventListener("DOMContentLoaded", () => {
    renderXP();

    // active nav highlight
    const path = location.pathname.replace(/\/$/, "") || "/";
    document.querySelectorAll(".mainnav a").forEach(a => {
      const href = a.getAttribute("href").replace(/\/$/, "") || "/";
      if (href === path) a.classList.add("active");
    });

    // sound toggle
    const btn = document.getElementById("soundToggle");
    const onI = document.getElementById("soundOnIcon");
    const offI = document.getElementById("soundOffIcon");
    function paint() {
      if (onI) onI.style.display = soundOn ? "" : "none";
      if (offI) offI.style.display = soundOn ? "none" : "";
    }
    paint();
    if (btn) btn.addEventListener("click", () => {
      soundOn = !soundOn;
      localStorage.setItem(soundKey, soundOn ? "on" : "off");
      paint();
      if (soundOn) sfx.click();
      toast(soundOn ? "Sound on 🔊" : "Sound off 🔇");
    });
  });

  return { speak, sfx, addXP, getStore: ensure, learnerLevel, LEVEL_STEP, confetti, toast };
})();
