"""
Voice & Audio Generation Engine for YouTube Shorts Automation.
Supports ElevenLabs API (eleven_multilingual_v2) with emotional pacing settings,
and falls back to Edge-TTS / gTTS when no API key is present.
"""

import json
import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional
import config


class VoiceEngine:
    """Handles text-to-speech generation with high retention acoustic settings."""

    def __init__(self, api_key: Optional[str] = None, default_voice_id: Optional[str] = None):
        self.api_key = api_key or config.ELEVENLABS_API_KEY
        self.voice_id = default_voice_id or config.ELEVENLABS_DEFAULT_VOICE

    def generate_voiceover(
        self,
        text: str,
        output_path: Path,
        voice_id: Optional[str] = None,
        stability: float = 0.40,
        similarity_boost: float = 0.85,
        style: float = 0.35
    ) -> Path:
        """
        Generates voiceover audio. If ElevenLabs API key is present, calls ElevenLabs.
        Otherwise falls back to edge-tts or system synthesis.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        vid = voice_id or self.voice_id

        if self.api_key:
            try:
                print(f"[VoiceEngine] Synthesizing audio with ElevenLabs (Voice ID: {vid})...")
                self._generate_elevenlabs(text, output_path, vid, stability, similarity_boost, style)
                print(f"[VoiceEngine] Audio saved to {output_path}")
                return output_path
            except Exception as e:
                print(f"[VoiceEngine] ElevenLabs API error: {e}. Falling back to offline/system TTS...")

        # Fallback to local / edge-tts
        return self._generate_fallback_tts(text, output_path)

    def _generate_elevenlabs(
        self,
        text: str,
        output_path: Path,
        voice_id: str,
        stability: float,
        similarity_boost: float,
        style: float
    ):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": True
            }
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            audio_bytes = resp.read()
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

    def _generate_fallback_tts(self, text: str, output_path: Path) -> Path:
        """Generates synthetic audio via edge-tts or Windows PowerShell SAPI."""
        print("[VoiceEngine] Using Windows Speech API / local synthesizer fallback...")
        wav_path = output_path.with_suffix(".wav")

        # Clean text for PowerShell string
        safe_text = text.replace('"', '""').replace("'", "''")
        ps_script = f"""
Add-Type -AssemblyName System.Speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Rate = 1
$speak.SetOutputToWaveFile('{str(wav_path)}')
$speak.Speak('{safe_text}')
$speak.Dispose()
"""
        cmd = ["powershell", "-NoProfile", "-Command", ps_script]
        subprocess.run(cmd, check=True)

        # Convert wav to mp3 via ffmpeg if ffmpeg is available
        if output_path.suffix.lower() == ".mp3" and os.path.exists(config.FFMPEG_EXE):
            conv_cmd = [
                config.FFMPEG_EXE, "-y",
                "-i", str(wav_path),
                "-codec:a", "libmp3lame",
                "-qscale:a", "2",
                str(output_path)
            ]
            subprocess.run(conv_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if wav_path.exists():
                wav_path.unlink()
            return output_path

        return wav_path


if __name__ == "__main__":
    engine = VoiceEngine()
    test_out = config.OUTPUT_DIR / "test_voice.mp3"
    print("Testing VoiceEngine...")
    engine.generate_voiceover("Welcome to YouTube Shorts Automation!", test_out)
    print("Audio file exists:", test_out.exists())
