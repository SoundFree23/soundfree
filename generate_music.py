"""
SoundFree.ro — Generator Melodie Ambientală
Generează un fișier WAV ambient de ~3 minute, gata de upload pe site.
Necesită: numpy (pip install numpy)
"""

import wave
import struct
import math
import os
import random

# ── CONFIGURARE ──────────────────────────────────────────────────
SAMPLE_RATE   = 44100       # Hz (calitate CD)
DURATION      = 180         # secunde (3 minute)
OUTPUT_FILE   = os.path.join(os.path.dirname(__file__), 'media', 'songs', 'morning_breeze_ambient.wav')
MASTER_VOLUME = 0.55        # volum general (0.0 - 1.0)

# ── FRECVENȚE NOTE (scala pentatonică Am — perfectă pentru ambient) ──
# A2, C3, D3, E3, G3, A3, C4, D4, E4, G4, A4
NOTES = {
    'A2': 110.00, 'C3': 130.81, 'D3': 146.83, 'E3': 164.81,
    'G3': 196.00, 'A3': 220.00, 'C4': 261.63, 'D4': 293.66,
    'E4': 329.63, 'G4': 392.00, 'A4': 440.00,
}

def sine(freq, t, phase=0.0):
    return math.sin(2 * math.pi * freq * t + phase)

def envelope(t, attack=2.0, decay=0.5, sustain=0.8, release=3.0, total=10.0):
    """ADSR envelope — contur de volum"""
    if t < attack:
        return t / attack
    elif t < attack + decay:
        return 1.0 - (1.0 - sustain) * ((t - attack) / decay)
    elif t < total - release:
        return sustain
    elif t < total:
        return sustain * (1.0 - (t - (total - release)) / release)
    return 0.0

def fade(t, total, fade_in=4.0, fade_out=6.0):
    """Fade in/out global"""
    if t < fade_in:
        return t / fade_in
    elif t > total - fade_out:
        return (total - t) / fade_out
    return 1.0

print("🎵 SoundFree.ro — Generez melodia ambientală...")
print(f"   Durată: {DURATION // 60} minute {DURATION % 60} secunde")
print(f"   Sample rate: {SAMPLE_RATE} Hz")
print()

total_samples = SAMPLE_RATE * DURATION
samples = []

# Secvență melodică — note și timpi de start (secunde)
# Acord de bază + melodie lentă
melody_sequence = [
    # (nota, start_sec, durata_sec, volum_rel)
    ('A2',  0,    16,  0.6),   # Drone bas
    ('E3',  0,    16,  0.4),
    ('A3',  0,    16,  0.3),

    ('A2',  16,   16,  0.6),
    ('G3',  16,   10,  0.35),
    ('A3',  20,    8,  0.3),
    ('C4',  24,    8,  0.25),

    ('A2',  32,   16,  0.6),
    ('E3',  32,   16,  0.35),
    ('D4',  36,    6,  0.3),
    ('E4',  42,    8,  0.28),

    ('A2',  48,   20,  0.6),
    ('C3',  48,   12,  0.35),
    ('G4',  52,    8,  0.22),
    ('A4',  58,    6,  0.18),

    ('A2',  64,   16,  0.6),
    ('E3',  66,   14,  0.38),
    ('C4',  68,    8,  0.3),
    ('A3',  74,   10,  0.28),

    ('A2',  80,   20,  0.6),
    ('D3',  80,   16,  0.35),
    ('E4',  84,    8,  0.25),
    ('D4',  90,    8,  0.28),

    ('A2',  96,   16,  0.6),
    ('G3',  96,   12,  0.35),
    ('C4', 100,   10,  0.3),
    ('E4', 106,    8,  0.22),

    ('A2', 112,   20,  0.6),
    ('A3', 112,   14,  0.38),
    ('G4', 116,    8,  0.2),
    ('E4', 122,    8,  0.25),

    ('A2', 128,   16,  0.6),
    ('C3', 130,   14,  0.35),
    ('D4', 132,   10,  0.28),
    ('C4', 140,    8,  0.25),

    ('A2', 144,   20,  0.6),
    ('E3', 144,   16,  0.38),
    ('A3', 148,   12,  0.3),
    ('C4', 154,    8,  0.22),

    ('A2', 160,   20,  0.55),
    ('G3', 162,   14,  0.3),
    ('E4', 164,   10,  0.2),
    ('A4', 170,    8,  0.15),  # vârf final

    # Coada — fade out lent
    ('A2', 168,   12,  0.5),
    ('E3', 170,   10,  0.3),
    ('A3', 172,    8,  0.2),
]

# Textura ambientală: acorduri pad
pad_chords = [
    # (frecvente, start, durata, vol)
    ([220.00, 261.63, 329.63], 0,  32, 0.15),   # Am
    ([196.00, 246.94, 293.66], 32, 32, 0.13),   # G
    ([174.61, 220.00, 261.63], 64, 32, 0.12),   # F
    ([220.00, 261.63, 329.63], 96, 32, 0.14),   # Am
    ([196.00, 246.94, 293.66],128, 32, 0.13),   # G
    ([174.61, 220.00, 261.63],160, 20, 0.10),   # F
]

# Construiește sunetul sample cu sample
step = 100  # raportăm progresul la fiecare N%
report_at = total_samples // 10

for i in range(total_samples):
    t = i / SAMPLE_RATE
    sample_val = 0.0

    # ── MELODIE cu armonice ──────────────────────────────────────
    for (note, start, dur, vol) in melody_sequence:
        if start <= t < start + dur:
            freq = NOTES[note]
            local_t = t - start
            env = envelope(local_t, attack=min(2.5, dur*0.3), release=min(3.0, dur*0.4), total=dur)
            # Fundamental + armonice ușoare
            s  = sine(freq,       local_t) * 0.70
            s += sine(freq * 2.0, local_t) * 0.15
            s += sine(freq * 3.0, local_t) * 0.08
            s += sine(freq * 0.5, local_t) * 0.07  # sub-armonica
            sample_val += s * env * vol

    # ── PAD CHORDS (acorduri lente, soft) ───────────────────────
    for (freqs, start, dur, vol) in pad_chords:
        if start <= t < start + dur:
            local_t = t - start
            env = envelope(local_t, attack=5.0, release=6.0, sustain=0.6, total=dur)
            chord_s = 0.0
            for freq in freqs:
                chord_s += sine(freq, local_t, phase=random.uniform(0, 0.1)) * (1.0 / len(freqs))
                chord_s += sine(freq * 1.5, local_t) * 0.05  # quinta
            sample_val += chord_s * env * vol

    # ── FADE IN / OUT GLOBAL ─────────────────────────────────────
    sample_val *= fade(t, DURATION, fade_in=5.0, fade_out=8.0)
    sample_val *= MASTER_VOLUME

    # Clamp -1.0 .. 1.0
    sample_val = max(-1.0, min(1.0, sample_val))

    # Convertește la 16-bit signed integer
    samples.append(int(sample_val * 32767))

    # Progress
    if i % report_at == 0:
        pct = int(i / total_samples * 100)
        print(f"   Generez... {pct}%", end='\r')

print("   Generez... 100% ✓        ")
print()

# ── SALVEAZĂ WAV ─────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with wave.open(OUTPUT_FILE, 'w') as wf:
    wf.setnchannels(1)         # mono
    wf.setsampwidth(2)         # 16-bit
    wf.setframerate(SAMPLE_RATE)
    packed = struct.pack(f'<{len(samples)}h', *samples)
    wf.writeframes(packed)

size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
print(f"✅ Melodia a fost generată!")
print(f"   Fișier: {OUTPUT_FILE}")
print(f"   Mărime: {size_mb:.1f} MB")
print(f"   Durată: {DURATION // 60}:{DURATION % 60:02d} minute")
print()
print("📤 Acum poți face upload pe site:")
print("   http://127.0.0.1:8000/backend/upload/")
print()
