import numpy as np
import wave
from pathlib import Path

def create_ambient_track(duration=265.0, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # Warm chords progression: Dm9, Bbmaj7, Fsus2, Csus4
    # Root frequencies (Hz)
    chords = [
        # Dm9: D2 (73.4), A2 (110), F3 (174.6), C4 (261.6), E4 (329.6)
        [73.42, 110.0, 174.61, 261.63, 329.63],
        # Bbmaj7: Bb1 (58.27), F2 (87.3), D3 (146.8), A3 (220.0), D4 (293.66)
        [58.27, 87.31, 146.83, 220.00, 293.66],
        # Fsus2: F2 (87.31), C3 (130.8), G3 (196.0), C4 (261.63), A4 (440.0)
        [87.31, 130.81, 196.00, 261.63, 440.00],
        # Cadd9 / Gsus: C2 (65.4), G2 (98.0), E3 (164.8), D4 (293.66), G4 (392.0)
        [65.41, 97.99, 164.81, 293.66, 392.00]
    ]

    chord_len = 16.0 # seconds per chord
    n_chords = len(chords)

    left = np.zeros_like(t)
    right = np.zeros_like(t)

    for i in range(int(np.ceil(duration / chord_len))):
        c_idx = i % n_chords
        chord_freqs = chords[c_idx]
        t_start = i * chord_len
        idx_start = int(t_start * sample_rate)
        idx_end = min(int((t_start + chord_len + 4.0) * sample_rate), len(t))
        actual_len = idx_end - idx_start
        if actual_len <= 0:
            break

        t_segment = np.linspace(0, actual_len / sample_rate, actual_len, endpoint=False)
        # Hann envelope with gentle overlap
        env = np.sin(np.pi * np.linspace(0, 1, actual_len)) ** 1.5

        sig_l = np.zeros(actual_len)
        sig_r = np.zeros(actual_len)

        for f_idx, f in enumerate(chord_freqs):
            weight = 1.0 / (1.0 + f_idx * 0.4)
            # subtle stereo chorus detune
            detune = 0.3 * (f_idx % 2 * 2 - 1)
            sig_l += weight * np.sin(2 * np.pi * (f - detune) * t_segment)
            sig_r += weight * np.sin(2 * np.pi * (f + detune) * t_segment)
            # gentle overtone
            sig_l += 0.25 * weight * np.sin(2 * np.pi * (f * 2) * t_segment)
            sig_r += 0.25 * weight * np.sin(2 * np.pi * (f * 2.01) * t_segment)

        left[idx_start:idx_end] += sig_l * env
        right[idx_start:idx_end] += sig_r * env

    # Add subtle organic low-frequency heartbeat / pulse (every 2.5s)
    pulse = (np.sin(2 * np.pi * 0.4 * t) ** 4) * np.sin(2 * np.pi * 55.0 * t) * 0.2
    left += pulse
    right += pulse

    # Master volume (ambient level)
    max_val = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-6)
    left = (left / max_val) * 0.12 # around -18 to -20 dB
    right = (right / max_val) * 0.12

    # Global fade in (3s) and fade out (4s)
    fade_in_len = int(3.0 * sample_rate)
    fade_out_len = int(4.0 * sample_rate)
    left[:fade_in_len] *= np.linspace(0, 1, fade_in_len)
    right[:fade_in_len] *= np.linspace(0, 1, fade_in_len)
    left[-fade_out_len:] *= np.linspace(1, 0, fade_out_len)
    right[-fade_out_len:] *= np.linspace(1, 0, fade_out_len)

    # Convert to 16-bit PCM
    audio_data = np.vstack((left, right)).T
    audio_int16 = (audio_data * 32767).astype(np.int16)

    out_file = Path("video_production/audio/ambient_track.wav")
    with wave.open(str(out_file), 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

    print(f"Generated ambient track: {out_file} ({out_file.stat().st_size} bytes, {duration}s)")

if __name__ == '__main__':
    create_ambient_track(320.0)
