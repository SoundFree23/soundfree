"""
SoundFree.ro — Generator Melodie Jazz Lounge
Generează un fișier WAV jazz de ~2.5 minute, gata de upload pe site.
Scala: Blues/Dorian | Progresie: ii-V-I | Stil: Late Night Jazz
"""

import wave
import struct
import math
import os
import random

# ── CONFIGURARE ──────────────────────────────────────────────────
SAMPLE_RATE   = 44100
DURATION      = 150          # 2 min 30 sec
OUTPUT_FILE   = os.path.join(os.path.dirname(__file__), 'media', 'songs', 'late_night_jazz.wav')
MASTER_VOLUME = 0.52
BPM           = 88           # tempo jazz lent (swing feel)

BEAT          = 60.0 / BPM                  # durata unui beat în secunde
BAR           = BEAT * 4                    # o măsură = 4 beats
SWING         = 0.62                        # factor swing (0.5 = drept, 0.67 = swing pur)

# ── NOTE JAZZ (Do Major + Blues notes) ──────────────────────────
N = {
    'C2': 65.41,  'D2': 73.42,  'E2': 82.41,  'F2': 87.31,
    'G2': 98.00,  'A2':110.00,  'Bb2':116.54, 'B2':123.47,

    'C3':130.81,  'Db3':138.59, 'D3':146.83,  'Eb3':155.56,
    'E3':164.81,  'F3':174.61,  'Gb3':185.00, 'G3':196.00,
    'Ab3':207.65, 'A3':220.00,  'Bb3':233.08, 'B3':246.94,

    'C4':261.63,  'Db4':277.18, 'D4':293.66,  'Eb4':311.13,
    'E4':329.63,  'F4':349.23,  'Gb4':369.99, 'G4':392.00,
    'Ab4':415.30, 'A4':440.00,  'Bb4':466.16, 'B4':493.88,

    'C5':523.25,  'D5':587.33,  'E5':659.25,  'F5':698.46,
    'G5':783.99,  'A5':880.00,
}

def sine(f, t, ph=0.0):
    return math.sin(2 * math.pi * f * t + ph)

def tri(f, t):
    """Undă triunghiulară — sunet mai cald, ca un pian"""
    v = (t * f) % 1.0
    return 4 * abs(v - 0.5) - 1.0

def piano_tone(freq, local_t, duration):
    """Simulare ton de pian cu armonice și decay rapid"""
    decay = math.exp(-local_t * (2.5 + freq / 300))
    s  = sine(freq,       local_t) * 0.50
    s += sine(freq * 2.0, local_t) * 0.25 * math.exp(-local_t * 3)
    s += sine(freq * 3.0, local_t) * 0.12 * math.exp(-local_t * 4)
    s += sine(freq * 4.0, local_t) * 0.08 * math.exp(-local_t * 5)
    s += tri(freq, local_t)        * 0.05
    # attack click mic
    attack = min(local_t / 0.008, 1.0)
    return s * decay * attack

def bass_tone(freq, local_t):
    """Bas — contrabas pizzicato simulat"""
    decay = math.exp(-local_t * 4.0)
    s  = sine(freq,       local_t) * 0.60
    s += sine(freq * 2.0, local_t) * 0.25 * math.exp(-local_t * 5)
    s += sine(freq * 3.0, local_t) * 0.10
    attack = min(local_t / 0.005, 1.0)
    return s * decay * attack

def brush_drum(t_local):
    """Perie de tobe — hi-hat moale"""
    if t_local > 0.08:
        return 0.0
    noise = math.sin(t_local * 8000 + math.sin(t_local * 3000) * 5)
    decay = math.exp(-t_local * 60)
    return noise * decay * 0.18

def kick_drum(t_local):
    """Kick moale"""
    if t_local > 0.15:
        return 0.0
    freq = 80 * math.exp(-t_local * 20)
    s = math.sin(2 * math.pi * freq * t_local)
    decay = math.exp(-t_local * 25)
    return s * decay * 0.35

# ── PROGRESIE ACORDURI ii-V-I în C Major ────────────────────────
# Dm7 | G7 | Cmaj7 | Cmaj7  (se repetă cu variații)
# Fiecare acord durează 1 măsură (4 beats)

CHORD_PROGRESSION = []
bar = 0
while bar * BAR < DURATION:
    pos = bar * BAR
    cycle = bar % 8
    if cycle in (0, 4):
        # Dm7 — ii
        CHORD_PROGRESSION.append((pos, BAR, [N['D3'], N['F3'], N['A3'], N['C4']], 0.18))
    elif cycle in (1, 5):
        # G7 — V
        CHORD_PROGRESSION.append((pos, BAR, [N['G2'], N['B2'], N['D3'], N['F3']], 0.18))
    elif cycle in (2, 3, 6, 7):
        # Cmaj7 — I
        CHORD_PROGRESSION.append((pos, BAR, [N['C3'], N['E3'], N['G3'], N['B3']], 0.18))
    bar += 1

# ── WALKING BASS LINE ────────────────────────────────────────────
BASS_NOTES = []
bar = 0
while bar * BAR < DURATION - BAR:
    pos = bar * BAR
    cycle = bar % 8
    if cycle in (0, 4):       # Dm7
        seq = [N['D2'], N['F2'], N['A2'], N['C3']]
    elif cycle in (1, 5):     # G7
        seq = [N['G2'], N['B2'], N['D3'], N['F2']]
    else:                     # Cmaj7
        seq = [N['C2'], N['E2'], N['G2'], N['B2']]

    # Swing: beat 1 drept, beat 2 swing, etc.
    for beat_i, freq in enumerate(seq):
        if beat_i % 2 == 0:
            t_note = pos + beat_i * BEAT
        else:
            t_note = pos + beat_i * BEAT + (SWING - 0.5) * BEAT * 0.5
        if t_note < DURATION:
            BASS_NOTES.append((t_note, BEAT * 0.85, freq, 0.55))
    bar += 1

# ── MELODIE JAZZ (scala Dorian în D: D E F G A B C) ─────────────
jazz_melody = []
MELODY_NOTES = [
    N['D4'], N['E4'], N['F4'], N['G4'], N['A4'],
    N['B4'], N['C5'], N['D5'], N['E5'], N['F5'],
    # Note de trecere blues
    N['F4'], N['Ab4'], N['Bb4'],
]

random.seed(42)
t_pos = 8.0  # melodia începe după 2 măsuri de intro

while t_pos < DURATION - 4.0:
    # Alege o notă din scală
    note = random.choice(MELODY_NOTES)
    # Durată variabilă — swing jazz
    dur_choices = [BEAT * 0.5, BEAT * 0.75, BEAT, BEAT * 1.5, BEAT * 2.0]
    weights     = [0.25,        0.30,         0.20, 0.15,       0.10]
    dur = random.choices(dur_choices, weights=weights)[0]

    # Swing offset
    swing_off = random.uniform(-0.04, 0.04)

    if t_pos + dur < DURATION:
        vol = random.uniform(0.28, 0.45)
        jazz_melody.append((t_pos + swing_off, dur * 0.88, note, vol))

    t_pos += dur

    # Pauze ocazionale
    if random.random() < 0.15:
        t_pos += BEAT * random.choice([0.5, 1.0, 1.5])

# ── RITMUL DE PERCUȚIE ───────────────────────────────────────────
BRUSH_HITS = []
KICK_HITS  = []
t = 0.0
while t < DURATION:
    # Hi-hat pe fiecare optime (cu swing)
    for eighth in range(8):
        if eighth % 2 == 0:
            btime = t + eighth * BEAT * 0.5
        else:
            btime = t + eighth * BEAT * 0.5 + (SWING - 0.5) * BEAT * 0.25
        if btime < DURATION:
            vol = 0.9 if eighth % 2 == 0 else 0.55
            BRUSH_HITS.append((btime, vol))
    # Kick pe beat 1 și 3
    KICK_HITS.append((t, 0.8))
    KICK_HITS.append((t + BEAT * 2, 0.65))
    t += BAR

# ── GENERARE SAMPLES ─────────────────────────────────────────────
print("🎷 SoundFree.ro — Generez melodia Jazz Lounge...")
print(f"   Tempo: {BPM} BPM · Swing: {int(SWING*100)}% · Durată: {DURATION//60}:{DURATION%60:02d}")
print()

total_samples = SAMPLE_RATE * DURATION
samples = []
report_step = total_samples // 10

for i in range(total_samples):
    t = i / SAMPLE_RATE
    val = 0.0

    # ACORDURI PAD (pian soft în fundal)
    for (start, dur, freqs, vol) in CHORD_PROGRESSION:
        if start <= t < start + dur:
            lt = t - start
            # Strum ușor — notele nu intră simultan
            for fi, freq in enumerate(freqs):
                strum_delay = fi * 0.018
                lt2 = lt - strum_delay
                if lt2 > 0:
                    env = min(lt2 / 0.04, 1.0) * math.exp(-lt2 * 0.8)
                    val += piano_tone(freq, lt2, dur) * env * vol

    # WALKING BASS
    for (start, dur, freq, vol) in BASS_NOTES:
        if start <= t < start + dur:
            lt = t - start
            val += bass_tone(freq, lt) * vol

    # MELODIE JAZZ
    for (start, dur, freq, vol) in jazz_melody:
        if start <= t < start + dur:
            lt = t - start
            attack = min(lt / 0.015, 1.0)
            release_t = dur - 0.05
            release = 1.0 if lt < release_t else max(0.0, 1.0 - (lt - release_t) / 0.05)
            env = attack * release * math.exp(-lt * 0.4)
            val += piano_tone(freq, lt, dur) * env * vol

    # PERCUȚIE
    for (hit_t, vol) in BRUSH_HITS:
        lt = t - hit_t
        if 0.0 <= lt < 0.1:
            val += brush_drum(lt) * vol

    for (hit_t, vol) in KICK_HITS:
        lt = t - hit_t
        if 0.0 <= lt < 0.2:
            val += kick_drum(lt) * vol

    # FADE IN / OUT
    fade_in  = min(t / 3.0, 1.0)
    fade_out = min((DURATION - t) / 5.0, 1.0)
    val *= fade_in * fade_out * MASTER_VOLUME

    val = max(-1.0, min(1.0, val))
    samples.append(int(val * 32767))

    if i % report_step == 0:
        print(f"   Generez... {i * 100 // total_samples}%", end='\r')

print("   Generez... 100% ✓        ")
print()

# ── SALVEAZĂ ─────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with wave.open(OUTPUT_FILE, 'w') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))

size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
print(f"✅ Melodia Jazz a fost generată!")
print(f"   Fișier  : {OUTPUT_FILE}")
print(f"   Mărime  : {size_mb:.1f} MB")
print(f"   Durată  : {DURATION//60}:{DURATION%60:02d} minute")
print()
print("📤 Upload pe site: http://127.0.0.1:8000/backend/upload/")
print()
print("   Titlu sugerat : Late Night Jazz")
print("   Artist        : SoundFree Studio")
print("   Gen           : Jazz Lounge")
print("   Mood          : Misterios")
print("   BPM           : 88")
print("   Durata        : 150")
