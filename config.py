"""
Global Configuration for YouTube Shorts Automation & Google Flow Integration.
Loads settings from .env file or environment variables.
"""

import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Directories & Paths
# ---------------------------------------------------------------------------
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
TEMPLATES_DIR = BASE_DIR / "templates"
SKILLS_DIR = BASE_DIR / "skills"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(ASSETS_DIR / "bgm").mkdir(parents=True, exist_ok=True)
(ASSETS_DIR / "sfx").mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Binary Executables (FFmpeg, FFprobe)
# ---------------------------------------------------------------------------
def _find_ffmpeg():
    # 1. System PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    # 2. Common Windows user binary location
    user_bin_ffmpeg = Path(os.path.expanduser("~")) / "bin" / "ffmpeg.exe"
    if user_bin_ffmpeg.exists():
        return str(user_bin_ffmpeg)
    # 3. Default fallback
    return "ffmpeg"

FFMPEG_EXE = os.getenv("FFMPEG_PATH", _find_ffmpeg())

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
# Default system fonts for titles, thumbnails, and subtitles
FONT_TITLE = os.getenv("FONT_TITLE", r"C:\Windows\Fonts\Arialbd.ttf")
FONT_HINDI = os.getenv("FONT_HINDI", r"C:\Windows\Fonts\NirmalaB.ttf")
FONT_STYLISH = str(SKILLS_DIR / "directing-stickman-videos" / "assets" / "fonts" / "Caveat.ttf")
FONT_CLEAN = str(SKILLS_DIR / "directing-stickman-videos" / "assets" / "fonts" / "NotoSans.ttf")

# ---------------------------------------------------------------------------
# API Keys & Endpoints
# ---------------------------------------------------------------------------
# Google Gemini / Vertex / Flow
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_FLOW_ENDPOINT = os.getenv("GOOGLE_FLOW_ENDPOINT", "")
GOOGLE_FLOW_API_KEY = os.getenv("GOOGLE_FLOW_API_KEY", "")

# ElevenLabs Voiceover
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
# Preset high-retention ElevenLabs voices
ELEVENLABS_DEFAULT_VOICE = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Adam
ELEVENLABS_VOICES = {
    "adam": "pNInz6obpgDQGcFmaJgB",      # Energetic, deep, storytelling narrator
    "brian": "nPczCjzI2devNBz1zQrb",     # Deep, dramatic documentary narrator
    "george": "JBFqnCBsd6RMkjVDRZzb",    # Warm, curious, engaging explainer
    "rachel": "21m00Tcm4TlvDq8ikWAM",    # Calm, natural female voice
}

# YouTube Data API Credentials
YOUTUBE_CLIENT_SECRETS_FILE = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", str(BASE_DIR / "client_secrets.json"))
YOUTUBE_TOKEN_PICKLE_FILE = os.getenv("YOUTUBE_TOKEN_PICKLE_FILE", str(BASE_DIR / "token.pickle"))
YOUTUBE_DEFAULT_PRIVACY = os.getenv("YOUTUBE_DEFAULT_PRIVACY", "public")  # 'public', 'private', 'unlisted'

# ---------------------------------------------------------------------------
# Video Production Standards (YouTube Shorts 9:16)
# ---------------------------------------------------------------------------
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
BGM_VOLUME = 0.15          # 15% volume (-16dB to -18dB) under narration
VOICEOVER_RMS = -6.0       # Standard gated RMS target for clear narration
DEFAULT_DURATION = 50      # Target shorts duration in seconds (divisible by scene beats)
