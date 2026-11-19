"""
Dynamic Video Renderer for YouTube Shorts Automation.
Assembles animated scenes, executes smooth Ken Burns zoom/pan,
mixes narration voiceover with ducked BGM, and burns subtitles via FFmpeg.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import config


class VideoRenderer:
    """Assembles final YouTube Shorts (1080x1920, 30fps) using OpenCV & FFmpeg."""

    def __init__(self, width: int = 1080, height: int = 1920, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.ffmpeg = config.FFMPEG_EXE

    def render_short(
        self,
        script: Dict,
        voiceover_audio: Path,
        subtitles_ass: Optional[Path],
        output_video: Path,
        scene_images: Optional[List[Path]] = None,
        bgm_audio: Optional[Path] = None
    ) -> Path:
        """
        Renders complete video with visuals, voiceover, BGM, and burned subtitles.
        """
        output_video = Path(output_video)
        output_video.parent.mkdir(parents=True, exist_ok=True)
        raw_video_path = output_video.parent / f"raw_{output_video.name}"

        # 1. Prepare Scene Images (generate procedural stickman backdrops if not provided)
        scenes = script.get("scenes", [])
        prepared_images = []
        for i, sc in enumerate(scenes):
            if scene_images and i < len(scene_images) and os.path.exists(scene_images[i]):
                prepared_images.append(scene_images[i])
            else:
                img_path = output_video.parent / f"auto_scene_{i + 1}.png"
                self._generate_procedural_scene(sc, img_path)
                prepared_images.append(img_path)

        # 2. Render Raw Video with Ken Burns Animation
        print(f"[VideoRenderer] Rendering visual frames ({len(scenes)} scenes at {self.fps} FPS)...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(raw_video_path), fourcc, self.fps, (self.width, self.height))

        for idx, (sc, img_p) in enumerate(zip(scenes, prepared_images)):
            dur = sc.get("duration", 6.0)
            total_frames = int(round(dur * self.fps))
            img = cv2.imread(str(img_p))
            if img is None:
                img = np.zeros((self.height, self.width, 3), dtype=np.uint8)

            ih, iw = img.shape[:2]
            target_aspect = self.width / float(self.height)
            img_aspect = iw / float(ih)

            if img_aspect > target_aspect:
                base_h = ih
                base_w = int(ih * target_aspect)
            else:
                base_w = iw
                base_h = int(iw / target_aspect)

            bx0 = (iw - base_w) // 2
            by0 = (ih - base_h) // 2

            for f in range(total_frames):
                prog = f / max(total_frames - 1, 1)
                # Subtle zoom in 1.0 -> 1.06
                zoom = 1.0 + 0.06 * prog
                cw = int(base_w / zoom)
                ch = int(base_h / zoom)
                cx = bx0 + (base_w - cw) // 2
                cy = by0 + (base_h - ch) // 2

                crop = img[cy:cy + ch, cx:cx + cw]
                frame = cv2.resize(crop, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
                writer.write(frame)

        writer.release()
        print("[VideoRenderer] Visual frames rendered successfully.")

        # 3. Final Audio & Subtitle Composite via FFmpeg
        self._composite_final_video(
            raw_video=raw_video_path,
            voiceover_audio=voiceover_audio,
            subtitles_ass=subtitles_ass,
            bgm_audio=bgm_audio,
            output_video=output_video
        )

        # Clean up temporary raw video
        if raw_video_path.exists():
            try:
                raw_video_path.unlink()
            except Exception:
                pass

        print(f"[VideoRenderer] Final short successfully produced at: {output_video}")
        return output_video

    def _generate_procedural_scene(self, scene_dict: Dict, output_path: Path):
        """Draws a clean, aesthetic narrative backdrop with stick figure & headline."""
        W, H = self.width, self.height
        im = Image.new("RGB", (W, H), (15, 18, 28))
        draw = ImageDraw.Draw(im)

        # Gradient glow
        for r in range(500, 0, -25):
            alpha = int(40 * (1.0 - r / 500.0))
            draw.ellipse(
                [(W // 2 - r, H // 2 - r - 100), (W // 2 + r, H // 2 + r - 100)],
                fill=(30, 60, 110)
            )

        # Minimalist stick figure in center
        head_radius = 55
        cx, cy = W // 2, H // 2 - 50
        # Head
        draw.ellipse([cx - head_radius, cy - head_radius, cx + head_radius, cy + head_radius], outline=(255, 255, 255), width=8)
        # Body
        draw.line([(cx, cy + head_radius), (cx, cy + head_radius + 180)], fill=(255, 255, 255), width=8)
        # Arms
        draw.line([(cx, cy + head_radius + 40), (cx - 100, cy + head_radius + 120)], fill=(255, 255, 255), width=8)
        draw.line([(cx, cy + head_radius + 40), (cx + 100, cy + head_radius + 120)], fill=(255, 255, 255), width=8)
        # Legs
        draw.line([(cx, cy + head_radius + 180), (cx - 70, cy + head_radius + 330)], fill=(255, 255, 255), width=8)
        draw.line([(cx, cy + head_radius + 180), (cx + 70, cy + head_radius + 330)], fill=(255, 255, 255), width=8)

        # Top Banner Text
        top_text = scene_dict.get("top_text", "")
        if top_text and os.path.exists(config.FONT_TITLE):
            font = ImageFont.truetype(config.FONT_TITLE, 56)
            bbox = draw.textbbox((0, 0), top_text, font=font)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            draw.text((tx, 140), top_text, font=font, fill=(255, 215, 0), stroke_width=6, stroke_fill=(0, 0, 0))

        im.save(output_path, "PNG")

    def _composite_final_video(
        self,
        raw_video: Path,
        voiceover_audio: Path,
        subtitles_ass: Optional[Path],
        bgm_audio: Optional[Path],
        output_video: Path
    ):
        """Combines raw video, voiceover, optional ducked BGM, and burns subtitles."""
        inputs = ["-i", str(raw_video), "-i", str(voiceover_audio)]
        filter_complex = []

        if bgm_audio and os.path.exists(bgm_audio):
            inputs.extend(["-i", str(bgm_audio)])
            # Mix voiceover with ducked BGM (volume=0.14)
            audio_filter = "[2:a]volume=0.14[bgm];[1:a][bgm]amix=inputs=2:duration=first[aout]"
        else:
            audio_filter = "[1:a]volume=1.0[aout]"

        # Video Filter for Subtitles (properly escaping backslashes for FFmpeg)
        if subtitles_ass and os.path.exists(subtitles_ass):
            ass_escaped = str(subtitles_ass).replace("\\", "/").replace(":", "\\:")
            vf = f"subtitles='{ass_escaped}'"
        else:
            vf = "null"

        cmd = [
            self.ffmpeg, "-y",
            *inputs,
            "-filter_complex", audio_filter,
            "-map", "0:v",
            "-map", "[aout]",
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_video)
        ]

        print(f"[VideoRenderer] Assembling final MP4 via FFmpeg...")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[VideoRenderer] FFmpeg failed with error:\n{res.stderr[-500:]}")
            # Fallback without subtitles if filter failed
            cmd_fallback = [
                self.ffmpeg, "-y",
                "-i", str(raw_video),
                "-i", str(voiceover_audio),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                str(output_video)
            ]
            subprocess.run(cmd_fallback, check=True)
