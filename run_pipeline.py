"""
Master Pipeline Runner for YouTube Shorts Automation.
Orchestrates end-to-end execution:
Topic -> Script -> Metadata -> Audio -> Subtitles -> Thumbnail -> Video Render -> Flow / YouTube Upload.
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
from integrations.google_flow_connector import GoogleFlowConnector
from integrations.flow_to_youtube_bridge import FlowToYouTubeBridge


def run_automation_pipeline(
    topic_seed: str = "auto",
    language: str = "hinglish",
    niche: str = None,
    upload: bool = False,
    privacy: str = "public",
    dispatch_flow: bool = False
):
    print("=" * 70)
    print("🎬 YOUTUBE SHORTS AUTOMATION PIPELINE INITIALIZED")
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
    print(f"📝 Script generated with {len(script.get('scenes', []))} scenes ({script.get('total_duration')}s)")

    # 3. Metadata Generation
    print("\n[3/7] Generating viral metadata (Title, Description, Tags, Pinned Comment)...")
    metadata = MetadataEngine.generate_metadata(topic, script)
    print(f"🏷️  Title: {metadata['title']}")
    print(f"🔑 Tags: {', '.join(metadata['tags'][:5])}...")

    # Save manifest
    job_slug = topic.get("id", "shorts_job")
    manifest_file = config.OUTPUT_DIR / f"{job_slug}_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump({"topic": topic, "script": script, "metadata": metadata}, f, indent=2)

    # 4. Voiceover Synthesis
    print("\n[4/7] Synthesizing high-retention voiceover audio...")
    voice_engine = VoiceEngine()
    audio_file = config.OUTPUT_DIR / f"{job_slug}_voiceover.mp3"
    voice_engine.generate_voiceover(
        text=script.get("full_voiceover_text", ""),
        output_path=audio_file
    )

    # 5. Subtitle Generation
    print("\n[5/7] Generating formatted ASS subtitles...")
    ass_file = config.OUTPUT_DIR / f"{job_slug}_subtitles.ass"
    SubtitlesGenerator.generate_ass(script, ass_file)

    # 6. Thumbnail Generation
    print("\n[6/7] Creating High-CTR dual-text thumbnail...")
    thumb_engine = ThumbnailEngine()
    thumb_file = config.OUTPUT_DIR / f"{job_slug}_thumbnail.jpg"
    first_scene = script["scenes"][0]
    last_scene = script["scenes"][-1]
    thumb_engine.generate_thumbnail(
        top_text=first_scene.get("top_text", topic.get("title")),
        bottom_text=last_scene.get("bottom_text", "WATCH TILL END!"),
        output_path=thumb_file,
        badge_text="OFFICIAL TRUTH"
    )

    # 7. Video Rendering or Google Flow Dispatch
    print("\n[7/7] Assembling final YouTube Short...")
    video_file = config.OUTPUT_DIR / f"{job_slug}_final.mp4"

    if dispatch_flow:
        print("[Pipeline] Dispatching video generation to Google Flow...")
        flow = GoogleFlowConnector()
        flow_job = flow.dispatch_flow_job(script)
        print(f"Google Flow status: {flow_job}")

    # Render local production video with Ken Burns and burned subtitles
    renderer = VideoRenderer()
    renderer.render_short(
        script=script,
        voiceover_audio=audio_file,
        subtitles_ass=ass_file,
        output_video=video_file
    )

    print("\n" + "=" * 70)
    print("✅ VIDEO PRODUCTION COMPLETED!")
    print(f"📹 Video: {video_file}")
    print(f"🖼️ Thumbnail: {thumb_file}")
    print(f"📄 Subtitles: {ass_file}")
    print(f"🎵 Audio: {audio_file}")
    print("=" * 70)

    # 8. Optional YouTube Upload
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
    parser.add_argument("--topic", type=str, default="auto", help="Topic seed, title prompt, or 'auto'")
    parser.add_argument("--language", type=str, default="hinglish", help="Language: hinglish, hindi, or english")
    parser.add_argument("--niche", type=str, default=None, help="Specific niche filter")
    parser.add_argument("--upload", action="store_true", help="Automatically upload to YouTube after rendering")
    parser.add_argument("--privacy", type=str, default="public", choices=["public", "unlisted", "private"])
    parser.add_argument("--flow", action="store_true", help="Dispatch prompts to Google Flow / Veo connector")

    args = parser.parse_args()
    run_automation_pipeline(
        topic_seed=args.topic,
        language=args.language,
        niche=args.niche,
        upload=args.upload,
        privacy=args.privacy,
        dispatch_flow=args.flow
    )


if __name__ == "__main__":
    main()
