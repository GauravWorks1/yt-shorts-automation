"""
Edge Emotional TTS & Audio Generation Engine.
Uses Microsoft Edge TTS (hi-IN-MadhurNeural, hi-IN-SwaraNeural, en-IN-PrabhatNeural)
with per-line emotional modulation (rate, pitch, volume) and exact scene timing measurement.
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import edge_tts
import config

# Emotion presets mapped to exact rate and pitch modulations
EMOTION_PRESETS = {
    "hook": {"rate": "+7%", "pitch": "+0Hz", "desc": "Curious Hook"},
    "twist": {"rate": "+10%", "pitch": "+2Hz", "desc": "Comedic / Ironic Twist"},
    "shout": {"rate": "+16%", "pitch": "+15Hz", "desc": "Annoyed / Excited Shout"},
    "suspense": {"rate": "+5%", "pitch": "-3Hz", "desc": "Nervous / Dark Suspense"},
    "snitch": {"rate": "+18%", "pitch": "+14Hz", "desc": "Fast & Wicked / Playful"},
    "grumpy": {"rate": "+4%", "pitch": "-14Hz", "desc": "Deep Tapori / Authoritative"},
    "revelation": {"rate": "+8%", "pitch": "+3Hz", "desc": "Shocking Revelation"},
    "cta": {"rate": "+9%", "pitch": "+1Hz", "desc": "Urgent Outro & CTA"},
    "neutral": {"rate": "+6%", "pitch": "+0Hz", "desc": "Standard Storytelling"}
}

DEFAULT_HINDI_VOICE = "hi-IN-MadhurNeural"
DEFAULT_FEMALE_VOICE = "hi-IN-SwaraNeural"
DEFAULT_ENGLISH_VOICE = "en-IN-PrabhatNeural"


class VoiceEngine:
    """Generates expressive, emotionally modulated voiceovers using Edge-TTS."""

    def __init__(self, default_voice: str = DEFAULT_HINDI_VOICE):
        self.default_voice = default_voice
        self.ffmpeg = config.FFMPEG_EXE

    def get_audio_duration(self, audio_file: Path) -> float:
        """Measures exact duration in seconds using FFmpeg/ffprobe."""
        cmd = [self.ffmpeg, "-i", str(audio_file)]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in res.stderr.splitlines():
            if "Duration" in line:
                try:
                    parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
                    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                except Exception:
                    pass
        return 5.0

    async def _synth_line(self, text: str, voice: str, rate: str, pitch: str, out_path: Path):
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(str(out_path))

    def generate_emotional_line(
        self,
        text: str,
        output_path: Path,
        emotion: str = "neutral",
        voice: Optional[str] = None
    ) -> float:
        """
        Synthesizes a single emotional voice line and returns its exact duration in seconds.
        """
        preset = EMOTION_PRESETS.get(emotion.lower(), EMOTION_PRESETS["neutral"])
        selected_voice = voice or self.default_voice
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        asyncio.run(self._synth_line(
            text=text,
            voice=selected_voice,
            rate=preset["rate"],
            pitch=preset["pitch"],
            out_path=output_path
        ))

        duration = self.get_audio_duration(output_path)
        return duration

    def generate_scene_voiceovers(
        self,
        script: Dict,
        output_dir: Path
    ) -> Tuple[Path, List[Dict]]:
        """
        Generates individual audio lines for each scene in the script using
        emotional voice modulation, measures exact durations, and merges into
        a master voiceover track.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        scenes = script.get("scenes", [])
        
        # Emotion progression across 5-stage heartbeat engine
        default_emotions = ["hook", "suspense", "twist", "revelation", "cta"]
        updated_scenes = []
        audio_clip_paths = []

        print(f"[VoiceEngine] Synthesizing {len(scenes)} scenes with Edge Emotional TTS ({self.default_voice})...")

        for idx, sc in enumerate(scenes):
            emotion = sc.get("emotion") or (default_emotions[idx] if idx < len(default_emotions) else "neutral")
            line_audio = output_dir / f"scene_{idx + 1:02d}_vo.mp3"
            narration = sc.get("narration", "")

            # Generate line audio
            dur = self.generate_emotional_line(
                text=narration,
                output_path=line_audio,
                emotion=emotion,
                voice=sc.get("voice") or self.default_voice
            )

            # Update scene with exact measured duration
            sc_copy = sc.copy()
            sc_copy["dur"] = round(dur, 2)
            sc_copy["audio_path"] = str(line_audio)
            sc_copy["emotion"] = emotion
            updated_scenes.append(sc_copy)
            audio_clip_paths.append(line_audio)

            print(f"  [{idx + 1}/{len(scenes)}] [{emotion.upper()}] ({dur:.2f}s): {narration[:45]}...")

        # Concat all audio clips into a master voiceover track
        master_audio = output_dir / "master_voiceover.mp3"
        concat_txt = output_dir / "audio_concat.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for p in audio_clip_paths:
                f.write(f"file '{p.name}'\n")

        cmd = [
            self.ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(master_audio)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[VoiceEngine] Master voiceover assembled: {master_audio} (Total {sum(s['dur'] for s in updated_scenes):.2f}s)")

        return master_audio, updated_scenes


if __name__ == "__main__":
    v_engine = VoiceEngine()
    test_script = {
        "scenes": [
            {"narration": "क्या आप सिर्फ एक कदम चलकर टाइम ट्रैवल कर सकते हैं?!", "emotion": "hook"},
            {"narration": "चीन और अफगानिस्तान के बॉर्डर पर दुनिया की सबसे खतरनाक बर्फीली पहाड़ियां हैं!", "emotion": "suspense"},
            {"narration": "सिर्फ एक कदम और आप साढ़े तीन घंटे पास्ट में चले जाएंगे!", "emotion": "revelation"},
            {"narration": "क्या आप ऐसे टाइमज़ोन में रह सकते हैं? कमेंट में बताओ!", "emotion": "cta"}
        ]
    }
    out_dir = config.OUTPUT_DIR / "edge_tts_test"
    master, scenes = v_engine.generate_scene_voiceovers(test_script, out_dir)
    print("Test successful. Master audio created:", master.exists())
