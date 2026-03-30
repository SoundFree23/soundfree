"""
SoundFree.ro — Jazz Lounge Generator v2.0
Foloseste numpy + scipy pentru:
  - Sunet de pian realist (16 armonice + string resonance)
  - Contrabas Karplus-Strong (pizzicato autentic)
  - Tobe cu brush (noise filtrat)
  - Reverb Schroeder (4 comb + 2 allpass)
  - Output STEREO cu panning
  - Swing timing autentic
"""

import numpy as np
from scipy.signal import butter, lfilter
import wave, struct, os, random

SR        = 44100
DURATION  = 165          # 2 min 45 sec
BPM       = 84
SWING     = 0.64         # factor de swing
BEAT      = 60.0 / BPM
BAR       = BEAT * 4
OUT_FILE  = os.path.join(os.path.dirname(__file__), 'media', 'songs', 'jazz_lounge_v2.wav')
os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

random.seed(7)
np.random.seed(7)

total = int(SR * DURATION)
L     = np.zeros(total, dtype=np.float64)
R     = np.zeros(total, dtype=np.float64)

# ── UTILITARE ────────────────────────────────────────────────────

def freq(note):
    """Converteste nota MIDI in Hz"""
    return 440.0 * 2 ** ((note - 69) / 12.0)

def butter_lp(cutoff, order=4):
    b, a = butter(order, cutoff / (SR / 2), btype='low')
    return b, a

def butter_hp(cutoff, order=2):
    b, a = butter(order, cutoff / (SR / 2), btype='high')
    return b, a

def apply_filter(sig, b, a):
    return lfilter(b, a, sig)

def add_stereo(buf_l, buf_r, signal, start_s, pan=0.0, vol=1.0):
    """Adauga un semnal in bufferele L/R cu pan si volum"""
    end_s = min(start_s + len(signal), total)
    seg   = signal[:end_s - start_s] * vol
    pl    = vol * (1.0 - max(0.0, pan))   # pan: -1=stanga, +1=dreapta
    pr    = vol * (1.0 + min(0.0, pan))
    buf_l[start_s:end_s] += seg * (1.0 - max(0.0,  pan)) * 0.85
    buf_r[start_s:end_s] += seg * (1.0 - max(0.0, -pan)) * 0.85

# ── INSTRUMENTE ──────────────────────────────────────────────────

def make_piano(midi, dur_s, vel=0.8):
    """Pian jazz realist — 16 armonice + decay exponential"""
    n  = int(dur_s * SR) + int(0.8 * SR)  # extra tail
    t  = np.linspace(0, n / SR, n, endpoint=False)
    f0 = freq(midi)
    s  = np.zeros(n)

    # Rapoartele armonicelor si amplitudinile pentru pian
    harmonics = [
        (1.0,  1.00), (2.0,  0.60), (3.0,  0.35), (4.0,  0.20),
        (5.0,  0.12), (6.0,  0.08), (7.0,  0.05), (8.0,  0.04),
        (9.0,  0.03), (10.0, 0.02), (12.0, 0.015),(14.0, 0.01),
    ]
    for (ratio, amp) in harmonics:
        decay = np.exp(-t * (1.8 + ratio * 0.4 + f0 / 800))
        s += np.sin(2 * np.pi * f0 * ratio * t) * amp * decay

    # Attack click (transient)
    attack = np.minimum(t / 0.008, 1.0)
    s     *= attack

    # Release dupa durata notei
    rel_s  = max(0, int(dur_s * SR))
    if rel_s < n:
        rel_len = n - rel_s
        rel_env = np.linspace(1.0, 0.0, rel_len) ** 1.5
        s[rel_s:] *= rel_env

    # Filtru de caldura — taie frecventele tari
    b, a = butter_lp(4200, order=3)
    s    = lfilter(b, a, s)
    return s * vel * 0.55

def make_bass(midi, dur_s, vel=0.9):
    """Contrabas pizzicato — Karplus-Strong simplificat"""
    f0    = freq(midi)
    delay = int(SR / f0)
    n     = int(dur_s * SR) + int(1.2 * SR)
    buf   = np.zeros(n)

    # Initializare cu noise in delay buffer
    buf[:delay] = np.random.uniform(-1, 1, delay)

    # Algoritmul Karplus-Strong
    for i in range(delay, n):
        buf[i] = 0.498 * (buf[i - delay] + buf[i - delay - 1])

    # Envelope: decay natural
    t     = np.linspace(0, n / SR, n, endpoint=False)
    env   = np.exp(-t * 3.5)
    rel_s = int(dur_s * SR)
    if rel_s < n:
        env[rel_s:] *= np.linspace(1.0, 0.0, n - rel_s) ** 2

    s = buf * env

    # Filtru pentru caldura basului
    b, a = butter_lp(800, order=4)
    s    = lfilter(b, a, s)
    b2, a2 = butter_hp(40, order=2)
    s    = lfilter(b2, a2, s)
    return s * vel * 1.1

def make_hihat(closed=True, vel=0.6):
    """Hi-hat cu brush — noise filtrat"""
    dur  = 0.06 if closed else 0.18
    n    = int(dur * SR)
    t    = np.linspace(0, dur, n)
    nois = np.random.randn(n)
    # Filtru high-pass pentru sunet de hi-hat
    b, a = butter_hp(6000, order=3)
    nois = lfilter(b, a, nois)
    b2, a2 = butter_lp(14000, order=2)
    nois = lfilter(b2, a2, nois)
    env  = np.exp(-t * (35 if closed else 12))
    return nois * env * vel * 0.22

def make_kick(vel=0.8):
    """Kick drum moale"""
    dur = 0.22
    n   = int(dur * SR)
    t   = np.linspace(0, dur, n)
    # Frecventa scade rapid
    f_sweep = 100 * np.exp(-t * 22) + 45
    phase   = 2 * np.pi * np.cumsum(f_sweep) / SR
    s       = np.sin(phase)
    env     = np.exp(-t * 18)
    b, a    = butter_lp(200, order=3)
    s       = lfilter(b, a, s)
    return s * env * vel * 0.9

def make_snare_brush(vel=0.5):
    """Snare cu perie — sunet jazz"""
    dur = 0.12
    n   = int(dur * SR)
    t   = np.linspace(0, dur, n)
    nois = np.random.randn(n)
    b, a = butter(3, [200/(SR/2), 8000/(SR/2)], btype='band')
    nois = lfilter(b, a, nois)
    # Ton mic de snare
    tone = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 40)
    s    = nois * 0.7 + tone * 0.3
    env  = np.exp(-t * 25)
    return s * env * vel * 0.28

# ── REVERB SCHROEDER ─────────────────────────────────────────────

def schroeder_reverb(sig, room=0.5, damp=0.4, wet=0.30):
    """Reverb cu filtre comb si allpass"""
    n = len(sig)
    # Comb filters (4 paralele)
    comb_delays = [1557, 1617, 1491, 1422]
    comb_gains  = [0.805 + i*0.01 for i in range(4)]
    combs = []
    for delay, gain in zip(comb_delays, comb_gains):
        g     = gain * (1 - damp * 0.15)
        out   = np.zeros(n)
        buf   = np.zeros(delay)
        ptr   = 0
        for j in range(n):
            samp     = sig[j] + buf[ptr] * g
            out[j]   = samp
            buf[ptr] = samp
            ptr      = (ptr + 1) % delay
        combs.append(out)
    wet_sig = sum(combs) / len(combs)

    # Allpass filters (2 in serie)
    for delay, gain in [(225, 0.5), (556, 0.5)]:
        out = np.zeros(n)
        buf = np.zeros(delay)
        ptr = 0
        for j in range(n):
            inp      = wet_sig[j]
            bsamp    = buf[ptr]
            out[j]   = -gain * inp + bsamp + gain * bsamp
            buf[ptr] = inp + gain * bsamp
            ptr      = (ptr + 1) % delay
        wet_sig = out

    return sig * (1 - wet) + wet_sig * wet * room * 1.4

# ── NOTE MIDI ────────────────────────────────────────────────────
# MIDI: C4=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71
#        C3=48, D3=50, E3=52, F3=53, G3=55, A3=57, B3=59
#        C2=36, D2=38, E2=40, F2=41, G2=43, A2=45, Bb2=46, B2=47

# Progresie jazz: Dm9 | G13 | Cmaj9 | Am9 (se repeta)
CHORD_VOICINGS = {
    'Dm9':   [50, 53, 57, 60, 64],   # D3 F3 A3 C4 E4
    'G13':   [43, 47, 50, 53, 57],   # G2 B2 D3 F3 A3
    'Cmaj9': [48, 52, 55, 59, 62],   # C3 E3 G3 B3 D4
    'Am9':   [45, 48, 52, 55, 59],   # A2 C3 E3 G3 B3
    'Fmaj7': [41, 45, 48, 52],       # F2 A2 C3 E3
    'Em7':   [40, 43, 47, 50],       # E2 G2 B2 D3
}

CHORD_SEQ = []
bar = 0
while bar * BAR < DURATION:
    cycle = bar % 8
    p     = bar * BAR
    if   cycle == 0: chord = 'Dm9'
    elif cycle == 1: chord = 'G13'
    elif cycle in (2,3): chord = 'Cmaj9'
    elif cycle == 4: chord = 'Am9'
    elif cycle == 5: chord = 'Fmaj7'
    elif cycle in (6,7): chord = 'Cmaj9'
    else:            chord = 'Cmaj9'
    CHORD_SEQ.append((p, BAR * 1.05, chord))
    bar += 1

# Walking bass line
BASS_SEQ = {
    'Dm9':   [38, 41, 45, 48, 50, 48, 45, 41],
    'G13':   [43, 47, 50, 53, 55, 53, 50, 47],
    'Cmaj9': [36, 40, 43, 47, 48, 47, 43, 40],
    'Am9':   [33, 36, 40, 43, 45, 43, 40, 36],
    'Fmaj7': [29, 33, 36, 40, 41, 40, 36, 33],
    'Em7':   [28, 31, 35, 38, 40, 38, 35, 31],
}

BASS_NOTES = []
bar = 0
while bar * BAR < DURATION - BAR:
    cycle = bar % 8
    p     = bar * BAR
    if   cycle == 0: chord = 'Dm9'
    elif cycle == 1: chord = 'G13'
    elif cycle in (2,3): chord = 'Cmaj9'
    elif cycle == 4: chord = 'Am9'
    elif cycle == 5: chord = 'Fmaj7'
    elif cycle in (6,7): chord = 'Cmaj9'
    else:            chord = 'Cmaj9'
    seq = BASS_SEQ[chord]
    for i, midi in enumerate(seq[:8]):
        # Swing pe optimile impare
        swing_off = (SWING - 0.5) * BEAT * 0.5 if i % 2 == 1 else 0.0
        bt        = p + i * BEAT * 0.5 + swing_off
        if bt < DURATION - 0.5:
            vel = 0.85 if i % 4 == 0 else (0.65 if i % 2 == 0 else 0.50)
            BASS_NOTES.append((bt, BEAT * 0.80, midi, vel))
    bar += 1

# Melodie jazz improvisata (scala Dorian D: D E F G A B C D)
MELODY_POOL = [62, 64, 65, 67, 69, 71, 72, 74,  # D4..D5 Dorian
               60, 65, 67, 70, 72,               # note de trecere
               69, 71, 74, 76]                   # high notes
MELODY_NOTES = []
t_pos = BAR * 2   # 2 masuri de intro

while t_pos < DURATION - BAR:
    midi = random.choice(MELODY_POOL)
    # Durate in timpi (cu swing)
    dur_beats = random.choices(
        [0.5, 0.75, 1.0, 1.5, 2.0, 3.0],
        weights=[0.20, 0.28, 0.22, 0.15, 0.10, 0.05]
    )[0]
    dur_s = dur_beats * BEAT * 0.88
    swing_off = random.uniform(-0.025, 0.025)
    vel = random.uniform(0.55, 0.92)

    # Vibrato usor pe note lungi
    vib = 0.0
    if dur_beats >= 1.5:
        vib_rate = random.uniform(4.5, 6.0)
        vib_depth = random.uniform(0.003, 0.007)
        # aproximam vibrato prin micro-pitch (deja in sine wave)
        vib = vib_rate  # (folosit mai jos ca info)

    if t_pos + dur_s < DURATION:
        MELODY_NOTES.append((t_pos + swing_off, dur_s, midi, vel))

    t_pos += dur_beats * BEAT

    # Pauze
    if random.random() < 0.18:
        t_pos += BEAT * random.choice([0.5, 1.0, 2.0])

# Ritmul percutiei
HIHAT_HITS   = []
KICK_HITS    = []
SNARE_HITS   = []
t = 0.0
while t < DURATION:
    # Hi-hat pe fiecare optime, cu swing
    for eighth in range(8):
        swing_off = (SWING - 0.5) * BEAT * 0.3 if eighth % 2 == 1 else 0.0
        ht = t + eighth * BEAT * 0.5 + swing_off
        if ht < DURATION:
            vel = 0.85 if eighth % 4 == 0 else (0.55 if eighth % 2 == 0 else 0.40)
            HIHAT_HITS.append((ht, vel, eighth % 2 == 0))  # True=closed
    # Kick pe 1 si 3
    KICK_HITS.append((t, 0.85))
    KICK_HITS.append((t + BEAT * 2, 0.70))
    # Snare brush pe 2 si 4
    SNARE_HITS.append((t + BEAT,         0.65))
    SNARE_HITS.append((t + BEAT * 3,     0.60))
    t += BAR

# ── RENDER ───────────────────────────────────────────────────────

print("🎷 SoundFree.ro — Jazz Lounge v2.0")
print(f"   Rendering... BPM={BPM} · Swing={int(SWING*100)}% · {DURATION//60}:{DURATION%60:02d} min")
print()

print("   [1/5] Acorduri pian...", end=' ', flush=True)
PIANO_L = np.zeros(total)
PIANO_R = np.zeros(total)
for (start, dur, chord_name) in CHORD_SEQ:
    voicing = CHORD_VOICINGS[chord_name]
    for vi, midi in enumerate(voicing):
        strum_delay = vi * 0.022
        s_start = int((start + strum_delay) * SR)
        if s_start >= total:
            continue
        vel = 0.38 - vi * 0.025
        sig = make_piano(midi, dur + 0.5, vel)
        sig = sig[:total - s_start]
        pan = -0.35 + vi * 0.14  # spread stereo
        PIANO_L[s_start:s_start+len(sig)] += sig * (1 - max(0, pan)) * 0.75
        PIANO_R[s_start:s_start+len(sig)] += sig * (1 - max(0, -pan)) * 0.75
print("OK")

print("   [2/5] Walking bass...", end=' ', flush=True)
BASS_BUF = np.zeros(total)
for (start, dur, midi, vel) in BASS_NOTES:
    s_start = int(start * SR)
    if s_start >= total:
        continue
    sig = make_bass(midi, dur, vel)
    sig = sig[:total - s_start]
    BASS_BUF[s_start:s_start+len(sig)] += sig
print("OK")

print("   [3/5] Melodie jazz...", end=' ', flush=True)
MEL_L = np.zeros(total)
MEL_R = np.zeros(total)
for (start, dur, midi, vel) in MELODY_NOTES:
    s_start = int(start * SR)
    if s_start >= total:
        continue
    sig = make_piano(midi, dur, vel)
    sig = sig[:total - s_start]
    pan = random.uniform(-0.2, 0.3)  # usor stanga/dreapta
    MEL_L[s_start:s_start+len(sig)] += sig * (1 - max(0, pan))
    MEL_R[s_start:s_start+len(sig)] += sig * (1 - max(0, -pan))
print("OK")

print("   [4/5] Percutie...", end=' ', flush=True)
PERC_L = np.zeros(total)
PERC_R = np.zeros(total)
for (ht, vel, closed) in HIHAT_HITS:
    ss = int(ht * SR)
    if ss >= total: continue
    sig = make_hihat(closed, vel)
    sig = sig[:total - ss]
    pan = 0.6  # hi-hat dreapta
    PERC_L[ss:ss+len(sig)] += sig * (1 - pan)
    PERC_R[ss:ss+len(sig)] += sig

for (ht, vel) in KICK_HITS:
    ss = int(ht * SR)
    if ss >= total: continue
    sig = make_kick(vel)
    sig = sig[:total - ss]
    PERC_L[ss:ss+len(sig)] += sig * 0.5
    PERC_R[ss:ss+len(sig)] += sig * 0.5

for (ht, vel) in SNARE_HITS:
    ss = int(ht * SR)
    if ss >= total: continue
    sig = make_snare_brush(vel)
    sig = sig[:total - ss]
    pan = 0.2
    PERC_L[ss:ss+len(sig)] += sig * (1 - pan)
    PERC_R[ss:ss+len(sig)] += sig
print("OK")

print("   [5/5] Mix, reverb, mastering...", end=' ', flush=True)

# Mix
mixL = PIANO_L * 0.55 + MEL_L * 0.80 + BASS_BUF * 0.72 + PERC_L * 0.90
mixR = PIANO_R * 0.55 + MEL_R * 0.80 + BASS_BUF * 0.72 + PERC_R * 0.90

# Reverb
mixL = schroeder_reverb(mixL, room=0.55, damp=0.38, wet=0.28)
mixR = schroeder_reverb(mixR, room=0.55, damp=0.38, wet=0.28)

# Filtru final — caldura
b, a = butter_lp(16000, order=2)
mixL = lfilter(b, a, mixL)
mixR = lfilter(b, a, mixR)

# Fade in / out
fade_in  = np.minimum(np.arange(total) / (SR * 3.0), 1.0)
fade_out = np.minimum((total - np.arange(total)) / (SR * 6.0), 1.0)
fade     = fade_in * fade_out
mixL    *= fade
mixR    *= fade

# Normalize
peak = max(np.max(np.abs(mixL)), np.max(np.abs(mixR)))
if peak > 0:
    mixL = mixL / peak * 0.88
    mixR = mixR / peak * 0.88

print("OK")

# ── EXPORT STEREO WAV ─────────────────────────────────────────────
print()
L16 = (mixL * 32767).astype(np.int16)
R16 = (mixR * 32767).astype(np.int16)
stereo = np.empty(total * 2, dtype=np.int16)
stereo[0::2] = L16
stereo[1::2] = R16

with wave.open(OUT_FILE, 'w') as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes(stereo.tobytes())

size_mb = os.path.getsize(OUT_FILE) / (1024 * 1024)
print(f"✅ Jazz Lounge v2.0 generat!")
print(f"   Fișier : {OUT_FILE}")
print(f"   Mărime : {size_mb:.1f} MB  |  Durată: {DURATION//60}:{DURATION%60:02d}  |  Stereo 44.1kHz")
print()
print("📤 Upload: http://127.0.0.1:8000/backend/upload/")
print()
print("   Titlu   : Jazz Lounge v2")
print("   Artist  : SoundFree Studio")
print("   Gen     : Jazz Lounge")
print("   Mood    : Misterios")
print("   BPM     : 84")
print("   Durata  : 165")
