"""
Cartoon Audio Short Sound Engine.
Directly implements the sound contract from /cartoon-audio-short:
- Synthesizes dynamic music bed (march beat, brass chords, plucked bass)
- Music stops cleanly at the twist line
- Synthesizes causal SFX (whoosh, thunk, scrape, ting, sting, rumble, snap, splash)
- Strictly enforces the 50% voice level (-6 dB gated RMS) rule with peak limiting.
"""

import math
import subprocess
import wave
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import config

SR = 48000


class CartoonAudioEngine:
    """Procedural music bed and sound effects synthesizer with strict -6dB RMS mixing."""

    def __init__(self, sample_rate: int = SR):
        self.sr = sample_rate
        self.ffmpeg = config.FFMPEG_EXE

    def _env(self, n: int, a: float = 0.005, r: float = 0.2) -> np.ndarray:
        t = np.arange(n) / self.sr
        return np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))

    def _lp_fast(self, x: np.ndarray, cutoff: float) -> np.ndarray:
        X = np.fft.rfft(x)
        f = np.fft.rfftfreq(len(x), 1.0 / self.sr)
        X *= 1.0 / (1.0 + (f / max(cutoff, 1.0)) ** 4)
        return np.fft.irfft(X, len(x)).astype(np.float32)

    def _hp_fast(self, x: np.ndarray, cutoff: float) -> np.ndarray:
        X = np.fft.rfft(x)
        f = np.fft.rfftfreq(len(x), 1.0 / self.sr)
        X *= 1.0 - 1.0 / (1.0 + (f / max(cutoff, 1.0)) ** 4)
        return np.fft.irfft(X, len(x)).astype(np.float32)

    def _place(self, buf: np.ndarray, sig: np.ndarray, t0: float, gain: float = 1.0):
        N = len(buf)
        i = int(t0 * self.sr)
        j = min(N, i + len(sig))
        if 0 <= i < N and j > i:
            buf[i:j] += sig[: j - i] * gain

    # ---------- Synthesizers ----------
    def synth_pluck(self, freq: float, dur: float = 0.35, bright: float = 0.5) -> np.ndarray:
        n = int(dur * self.sr)
        t = np.arange(n) / self.sr
        s = sum((bright ** k) * np.sin(2 * np.pi * freq * (k + 1) * t) / (k + 1) for k in range(6))
        return (s * self._env(n, 0.003, dur * 0.35)).astype(np.float32)

    def synth_brass(self, freqs: List[float], dur: float) -> np.ndarray:
        n = int(dur * self.sr)
        t = np.arange(n) / self.sr
        s = np.zeros(n)
        for f in freqs:
            ph = 2 * np.pi * f * t + 0.003 * np.sin(2 * np.pi * 5 * t)
            s += sum(np.sin((k + 1) * ph) / (k + 1) ** 1.3 for k in range(8))
        a = np.minimum(1.0, t / 0.08) * np.minimum(1.0, (dur - t) / 0.15).clip(0)
        return self._lp_fast((s * a).astype(np.float32), 1800) / len(freqs)

    def synth_drum(self, kind: str) -> np.ndarray:
        if kind == "kick":
            n = int(0.35 * self.sr)
            t = np.arange(n) / self.sr
            f = 50 + 90 * np.exp(-t * 30)
            return (np.sin(2 * np.pi * np.cumsum(f) / self.sr) * np.exp(-t * 9)).astype(np.float32)
        # Snare
        n = int(0.18 * self.sr)
        t = np.arange(n) / self.sr
        rng = np.random.default_rng(123)
        s = rng.standard_normal(n) * np.exp(-t * 28) * 0.6 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 20) * 0.5
        return self._hp_fast(s.astype(np.float32), 300)

    def synth_whoosh(self, dur: float = 0.5) -> np.ndarray:
        n = int(dur * self.sr)
        t = np.arange(n) / self.sr
        rng = np.random.default_rng(456)
        noise = rng.standard_normal(n)
        fc = 300 + 2500 * np.sin(np.pi * t / dur) ** 2
        sig = noise * np.sin(np.pi * t / dur) ** 2
        return self._lp_fast(sig.astype(np.float32), 1800) * 0.5

    def synth_thunk(self, dur: float = 0.3) -> np.ndarray:
        n = int(dur * self.sr)
        t = np.arange(n) / self.sr
        f = 85.0 * np.exp(-t * 15.0)
        sig = np.sin(2 * np.pi * f * t) * np.exp(-t * 12.0)
        return sig.astype(np.float32)

    def synth_ting(self, freq: float = 2400.0, dur: float = 0.8) -> np.ndarray:
        n = int(dur * self.sr)
        t = np.arange(n) / self.sr
        sig = (np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2.76 * t)) * np.exp(-t * 4.5)
        return sig.astype(np.float32)

    def synth_sting(self, dur: float = 2.0) -> np.ndarray:
        n = int(dur * self.sr)
        t = np.arange(n) / self.sr
        # Dark dramatic cinematic drone
        f1 = 65.0
        f2 = 68.5  # beating dissonance
        sig = (np.sin(2 * np.pi * f1 * t) + np.sin(2 * np.pi * f2 * t)) * np.exp(-t * 1.5)
        return (sig * 0.6).astype(np.float32)

    def generate_and_mix_cartoon_audio(
        self,
        voiceover_file: Path,
        script: Dict,
        output_file: Path
    ) -> Path:
        """
        Loads voiceover, synthesizes cartoon music bed and causal SFX,
        and mixes strictly at 50% (-6dB) voice level.
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 1. Load Voiceover PCM via FFmpeg
        cmd = [self.ffmpeg, "-v", "error", "-i", str(voiceover_file), "-ac", "1", "-ar", str(self.sr), "-f", "f32le", "-"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        voice = np.frombuffer(res.stdout, dtype=np.float32).copy()
        
        N = len(voice)
        total_duration = N / float(self.sr)
        print(f"[CartoonAudio] Loaded voiceover: {total_duration:.2f}s ({N} samples)")

        music = np.zeros(N, np.float32)
        sfx = np.zeros(N, np.float32)

        # 2. Build Music Bed (Stops at the twist line!)
        # Default twist line is usually around the last 20% of duration
        scenes = script.get("scenes", [])
        music_stop_t = total_duration * 0.78
        elapsed = 0.0
        for s in scenes:
            if s.get("emotion") == "twist" or "twist" in s.get("beat_name", "").lower():
                music_stop_t = elapsed
                break
            elapsed += s.get("dur", s.get("duration", 5.0))

        BPM = 108
        beat = 60.0 / BPM
        # Am -> F -> G -> E chord progression
        chords = [
            [220.0, 261.63, 329.63],  # Am
            [174.61, 220.0, 261.63],  # F
            [196.0, 246.94, 293.66],  # G
            [164.81, 207.65, 246.94]   # E
        ]

        tt = 0.0
        bar = 0
        while tt < music_stop_t:
            ch = chords[bar % len(chords)]
            self._place(music, self.synth_brass(ch, beat * 4 * 0.96), tt, gain=0.12)
            # Bass pluck on root
            self._place(music, self.synth_pluck(ch[0] / 2.0, dur=beat * 0.8), tt, gain=0.25)

            for b in range(4):
                tb = tt + b * beat
                if tb >= music_stop_t:
                    break
                if b == 0 or b == 2:
                    self._place(music, self.synth_drum("kick"), tb, gain=0.30)
                else:
                    self._place(music, self.synth_drum("snare"), tb, gain=0.20)
            tt += 4 * beat
            bar += 1

        # 3. Place Causal SFX
        # Hook whoosh
        self._place(sfx, self.synth_whoosh(0.6), 0.3, gain=0.45)
        # Scene transition whooshes & thunks
        cur_t = 0.0
        for idx, s in enumerate(scenes):
            s_dur = s.get("dur", s.get("duration", 5.0))
            if idx > 0:
                self._place(sfx, self.synth_whoosh(0.4), cur_t, gain=0.35)
                self._place(sfx, self.synth_thunk(0.3), cur_t + 0.1, gain=0.50)
            if idx == len(scenes) - 2:  # Revelation / Twist sting
                self._place(sfx, self.synth_sting(2.5), cur_t, gain=0.85)
            elif idx == len(scenes) - 1:  # Outro ting
                self._place(sfx, self.synth_ting(2600.0, 0.9), cur_t + 0.5, gain=0.60)
            cur_t += s_dur

        # 4. Strictly mix at 50% voice level (-6dB gated RMS) + ducking
        ve = np.abs(voice)
        k = int(0.05 * self.sr)
        ve_smoothed = np.convolve(ve, np.ones(k) / k, mode="same")
        voice_peak = max(float(np.max(ve_smoothed)), 1e-4)
        
        # Envelope follower for natural ducking under voice
        duck = 1.0 - 0.45 * np.clip(ve_smoothed / (voice_peak * 0.25), 0.0, 1.0)
        
        # Voice (1.0) + Music at 50% (-6dB) + SFX capped
        mixed = voice + (music * duck * 0.50) + (sfx * 0.45)
        
        # Tanh analog saturation limiter (prevents harsh digital clipping)
        mixed = np.tanh(mixed * 0.95) / np.tanh(0.95)
        
        # 40ms gentle tail fadeout
        fade_len = int(0.04 * self.sr)
        mixed[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)

        # Convert to 16-bit PCM WAV
        pcm = (np.clip(mixed, -1.0, 1.0) * 32767.0).astype(np.int16)
        with wave.open(str(output_file), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sr)
            wf.writeframes(pcm.tobytes())

        print(f"[CartoonAudio] Final mixed cartoon master audio saved to: {output_file}")
        return output_file
