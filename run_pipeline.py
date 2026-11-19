"""
Master Pipeline Runner for YouTube Shorts Automation.
Supports both styles:
1. --style stickman : Minimalist 2D stickman explainer with Edge Emotional TTS & Ken Burns zoom
2. --style cartoon  : /cartoon-audio-short 2D bean-head characters in colourful world with 50% ducked music bed & SFX
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from core.topic_engine import TopicEngine
from core.script_engine import ScriptEngine
from core.metadata_engine import MetadataEngine
from core.voice_engine import VoiceEngine
from core.thumbnail_engine import ThumbnailEngine
from core.subtitles_generator import SubtitlesGenerator
from core.video_renderer import VideoRenderer
from core.cartoon_audio_engine import CartoonAudioEngine
from core.cartoon_renderer import CartoonRenderer
from integrations.google_flow_connector import GoogleFlowConnector
from integrations.flow_to_youtube_bridge import FlowToYouTubeBridge


def run_automation_pipeline(
    topic_seed: str = "auto",
    language: str = "hinglish",
    style: str = "cartoon",
    niche: str = None,
    upload: bool = False,
    privacy: str = "public",
    dispatch_flow: bool = False,
    voice: str = "hi-IN-MadhurNeural"
):
    print("=" * 70)
    print(f"🎬 YOUTUBE SHORTS AUTOMATION PIPELINE (STYLE: {style.upper()})")
    print("=" * 70)

    # 1. Topic Generation
    topic_engine = TopicEngine()
    if topic_seed and topic_seed != "auto":
        print(f"\n[1/7] Generating topic from seed: '{topic_seed}'...")
        topic = topic_engine.generate_ai_topic(prompt_seed=topic_seed, language=language)
    else:
        print("\n[1/7] Picking viral topic from curated high-CTR bank...")
        topic = topic_engine.get_random_topic(niche=niche, language=language)

    print(f"📌 Selected Topic: {topic.get('title')}")
    print(f"🎯 Paradox/Hook: {topic.get('hook')}")

    # 2. Script Generation
    print("\n[2/7] Generating 5-Stage High-Completion Script...")
    script_engine = ScriptEngine()
    script = script_engine.generate_script(topic)
    print(f"📝 Script generated with {len(script.get('scenes', []))} scenes")

    job_slug = f"{topic.get('id', 'short')}_{style}"
    job_dir = config.OUTPUT_DIR / job_slug
    job_dir.mkdir(parents=True, exist_ok=True)

    # 3. Voiceover Synthesis (measures exact per-scene durations)
    print(f"\n[3/7] Synthesizing Edge Emotional TTS ({voice})...")
    voice_engine = VoiceEngine(default_voice=voice)
    voice_audio, updated_scenes = voice_engine.generate_scene_voiceovers(
        script=script,
        output_dir=job_dir
    )
    script["scenes"] = updated_scenes
    total_audio_dur = sum(s["dur"] for s in updated_scenes)
    script["total_duration"] = total_audio_dur

    # 4. Metadata Generation
    print("\n[4/7] Generating viral metadata (Title, Description, Tags, Pinned Comment)...")
    metadata = MetadataEngine.generate_metadata(topic, script)
    print(f"🏷️  Title: {metadata['title']}")
    print(f"🔑 Tags: {', '.join(metadata['tags'][:5])}...")

    manifest_file = job_dir / f"{job_slug}_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump({"topic": topic, "script": script, "metadata": metadata}, f, indent=2)

    # 5. Subtitles & Thumbnail Generation
    print("\n[5/7] Generating formatted ASS subtitles & High-CTR Thumbnail...")
    ass_file = job_dir / f"{job_slug}_subtitles.ass"
    SubtitlesGenerator.generate_ass(script, ass_file)

    thumb_engine = ThumbnailEngine()
    thumb_file = job_dir / f"{job_slug}_thumbnail.jpg"
    first_scene = script["scenes"][0]
    last_scene = script["scenes"][-1]
    thumb_engine.generate_thumbnail(
        top_text=first_scene.get("top_text", topic.get("title")),
        bottom_text=last_scene.get("bottom_text", "WATCH TILL END!"),
        output_path=thumb_file,
        badge_text="VIRAL CARTOON" if style == "cartoon" else "TRUE MYSTERY"
    )

    # 6. Audio Mixing (Cartoon Audio Short Sound Engine)
    if style == "cartoon":
        print("\n[6/7] Synthesizing Cartoon Music Bed + Causal SFX (Strict -6dB RMS rule)...")
        cartoon_audio_engine = CartoonAudioEngine()
        mixed_audio_file = job_dir / "cartoon_master_mix.wav"
        master_audio = cartoon_audio_engine.generate_and_mix_cartoon_audio(
            voiceover_file=voice_audio,
            script=script,
            output_file=mixed_audio_file
        )
    else:
        master_audio = voice_audio

    # 7. Video Rendering
    video_file = job_dir / f"{job_slug}_final.mp4"
    if style == "cartoon":
        print(f"\n[7/7] Assembling 2D Bean-Head Cartoon Short ({total_audio_dur:.2f}s)...")
        c_renderer = CartoonRenderer()
        c_renderer.render_cartoon_short(
            script=script,
            master_audio=master_audio,
            output_video=video_file
        )
    else:
        print(f"\n[7/7] Assembling Stickman Ken Burns Short ({total_audio_dur:.2f}s)...")
        renderer = VideoRenderer()
        renderer.render_short(
            script=script,
            voiceover_audio=master_audio,
            subtitles_ass=ass_file,
            output_video=video_file
        )

    print("\n" + "=" * 70)
    print("✅ VIDEO PRODUCTION COMPLETED!")
    print(f"🎨 Style: {style.upper()}")
    print(f"📹 Master Video: {video_file}")
    print(f"🖼️ Thumbnail: {thumb_file}")
    print(f"📄 Subtitles: {ass_file}")
    print(f"🎵 Master Audio: {master_audio}")
    print("=" * 70)

    # 8. Optional YouTube Upload / Flow
    if dispatch_flow:
        print("[Pipeline] Dispatching prompts to Google Flow connector...")
        flow = GoogleFlowConnector()
        flow.dispatch_flow_job(script)

    if upload:
        print("\n🚀 Initiating YouTube Upload Automation...")
        bridge = FlowToYouTubeBridge()
        upload_res = bridge.process_and_upload(
            video_file=video_file,
            topic_info=topic,
            script_info=script,
            thumbnail_file=thumb_file,
            privacy=privacy
        )
        return upload_res

    return {
        "video": str(video_file),
        "thumbnail": str(thumb_file),
        "metadata": metadata
    }


def main():
    parser = argparse.ArgumentParser(description="Autonomous YouTube Shorts Generator & Uploader")
    parser.add_argument("--style", type=str, default="cartoon", choices=["cartoon", "stickman"], help="Visual style: 'cartoon' (/cartoon-audio-short) or 'stickman'")
    parser.add_argument("--topic", type=str, default="auto", help="Topic seed, title prompt, or 'auto'")
    parser.add_argument("--language", type=str, default="hinglish", help="Language: hinglish, hindi, or english")
    parser.add_argument("--voice", type=str, default="hi-IN-MadhurNeural", help="Edge TTS Voice (hi-IN-MadhurNeural, hi-IN-SwaraNeural, en-IN-PrabhatNeural)")
    parser.add_argument("--niche", type=str, default=None, help="Specific niche filter")
    parser.add_argument("--upload", action="store_true", help="Automatically upload to YouTube after rendering")
    parser.add_argument("--privacy", type=str, default="public", choices=["public", "unlisted", "private"])
    parser.add_argument("--flow", action="store_true", help="Dispatch prompts to Google Flow / Veo connector")

    args = parser.parse_args()
    run_automation_pipeline(
        topic_seed=args.topic,
        language=args.language,
        style=args.style,
        voice=args.voice,
        niche=args.niche,
        upload=args.upload,
        privacy=args.privacy,
        dispatch_flow=args.flow
    )


if __name__ == "__main__":
    main()
