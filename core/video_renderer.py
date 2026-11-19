"""
Signature Stickman Video Renderer for YouTube Shorts Automation.
Implements the exact style from production:
- Scene-by-scene cut synchronization driven by audio line durations
- Dynamic Ken Burns zoompan with alternating zoom rates (0.00045 - 0.00075) and focal points (focus_y)
- Individual cut compilation & FFmpeg concat demuxer assembly
- Master audio mux with ducked BGM and hardcoded ASS subtitle burning
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import config


class VideoRenderer:
    """Renders synchronized stickman/explainer shorts matching the signature production style."""

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
        Renders complete video using the signature cut-by-cut Ken Burns pipeline.
        """
        output_video = Path(output_video)
        output_video.parent.mkdir(parents=True, exist_ok=True)
        cuts_dir = output_video.parent / "cuts"
        cuts_dir.mkdir(parents=True, exist_ok=True)

        scenes = script.get("scenes", [])
        total_scenes = len(scenes)
        print(f"[VideoRenderer] Rendering {total_scenes} signature scene cuts at {self.width}x{self.height} (30 fps)...")

        # 1. Prepare Scene Visuals (procedural stickman / explainer backdrops if none provided)
        prepared_images = []
        for i, sc in enumerate(scenes):
            if scene_images and i < len(scene_images) and os.path.exists(scene_images[i]):
                prepared_images.append(scene_images[i])
            else:
                img_path = output_video.parent / f"scene_{i + 1:02d}_art.png"
                self._generate_signature_scene_art(sc, img_path, idx=i)
                prepared_images.append(img_path)

        # 2. Render each cut with custom focal points and alternating zoompan rates
        # Signature zoom rates & focus points from production:
        zoom_configs = [
            {"rate": "0.00045", "focus_y": "ih/2-(ih/zoom/2)"},
            {"rate": "0.00055", "focus_y": "ih/2-(ih/zoom/2)+40"},
            {"rate": "0.00040", "focus_y": "ih/2-(ih/zoom/2)-50"},
            {"rate": "0.00065", "focus_y": "ih/2-(ih/zoom/2)+30"},
            {"rate": "0.00050", "focus_y": "ih/2-(ih/zoom/2)"},
        ]

        cut_paths = []
        for idx, (sc, img_p) in enumerate(zip(scenes, prepared_images)):
            dur = sc.get("dur", sc.get("duration", 5.0))
            frames = int(round(dur * self.fps))
            out_clip = cuts_dir / f"cut_{idx + 1:02d}.mp4"
            cut_paths.append(out_clip)

            cfg = zoom_configs[idx % len(zoom_configs)]
            zoom_rate = cfg["rate"]
            focus_y = cfg["focus_y"]

            # Signature FFmpeg zoompan filter
            vf = (
                f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,"
                f"crop={self.width}:{self.height},"
                f"zoompan=z='min(zoom+{zoom_rate},1.09)':d={frames}:"
                f"x='iw/2-(iw/zoom/2)':y='{focus_y}':s={self.width}x{self.height}:fps={self.fps},format=yuv420p"
            )

            cmd = [
                self.ffmpeg, "-y",
                "-loop", "1",
                "-i", str(img_p),
                "-vf", vf,
                "-t", f"{dur:.2f}",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",
                str(out_clip)
            ]

            print(f"  [{idx + 1}/{total_scenes}] Cut {idx + 1:02d}: {dur:.2f}s ({frames} frames, zoom={zoom_rate})...")
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                print(f"  Warning on cut {idx + 1}: {res.stderr[-200:]}")

        # 3. Concatenate all scene cuts
        concat_txt = output_video.parent / "concat_cuts_list.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for p in cut_paths:
                norm_p = str(p).replace('\\', '/')
                f.write(f"file '{norm_p}'\n")

        temp_concat = output_video.parent / "temp_concat_video.mp4"
        cmd_concat = [
            self.ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(temp_concat)
        ]
        subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[VideoRenderer] Scene cuts concatenated successfully.")

        # 4. Final Audio Muxing & Subtitle Burning
        inputs = ["-i", str(temp_concat), "-i", str(voiceover_audio)]
        filter_complex = []

        if bgm_audio and os.path.exists(bgm_audio):
            inputs.extend(["-i", str(bgm_audio)])
            audio_filter = "[2:a]volume=0.14[bgm];[1:a][bgm]amix=inputs=2:duration=first[aout]"
        else:
            audio_filter = "[1:a]volume=1.0[aout]"

        if subtitles_ass and os.path.exists(subtitles_ass):
            ass_escaped = str(subtitles_ass).replace("\\", "/").replace(":", "\\:")
            vf_sub = f"subtitles='{ass_escaped}'"
        else:
            vf_sub = "null"

        cmd_final = [
            self.ffmpeg, "-y",
            *inputs,
            "-filter_complex", audio_filter,
            "-map", "0:v",
            "-map", "[aout]",
            "-vf", vf_sub,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_video)
        ]

        print(f"[VideoRenderer] Assembling final master short with burned subtitles...")
        res = subprocess.run(cmd_final, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[VideoRenderer] Subtitle burning error: {res.stderr[-300:]}")
            # Fallback direct mux
            cmd_fb = [
                self.ffmpeg, "-y",
                "-i", str(temp_concat),
                "-i", str(voiceover_audio),
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(output_video)
            ]
            subprocess.run(cmd_fb, check=True)

        # Cleanup temp concat
        if temp_concat.exists():
            try:
                temp_concat.unlink()
            except Exception:
                pass

        print(f"[VideoRenderer] 🎬 Master Short Produced: {output_video}")
        return output_video

    def _generate_signature_scene_art(self, scene: Dict, output_path: Path, idx: int = 0):
        """Generates dynamic 2D stickman explainer artwork with custom pose & headline."""
        W, H = self.width, self.height
        # Dark studio backdrop with radial vignette
        im = Image.new("RGB", (W, H), (14, 17, 26))
        draw = ImageDraw.Draw(im)

        # Ambient lighting gradient
        glow_colors = [(35, 65, 120), (25, 80, 100), (90, 40, 110), (110, 60, 30), (30, 90, 60)]
        glow_color = glow_colors[idx % len(glow_colors)]
        for r in range(550, 0, -30):
            alpha = int(45 * (1.0 - r / 550.0))
            draw.ellipse(
                [(W // 2 - r, H // 2 - r - 80), (W // 2 + r, H // 2 + r - 80)],
                fill=glow_color
            )

        # Floor horizon line
        draw.line([(0, H // 2 + 360), (W, H // 2 + 360)], fill=(45, 55, 75), width=3)

        # Draw expressive stickman based on scene index (varying gestures)
        cx, cy = W // 2, H // 2 - 20
        head_r = 60
        # White filled hollow head
        draw.ellipse([cx - head_r, cy - head_r, cx + head_r, cy + head_r], outline=(255, 255, 255), width=9)
        # Spine
        draw.line([(cx, cy + head_r), (cx, cy + head_r + 200)], fill=(255, 255, 255), width=9)

        if idx % 3 == 0:
            # Gesture: Shock / Question (Hands on head)
            draw.line([(cx, cy + head_r + 50), (cx - 90, cy)], fill=(255, 255, 255), width=8)
            draw.line([(cx - 90, cy), (cx - 50, cy - head_r + 10)], fill=(255, 255, 255), width=8)
            draw.line([(cx, cy + head_r + 50), (cx + 90, cy)], fill=(255, 255, 255), width=8)
            draw.line([(cx + 90, cy), (cx + 50, cy - head_r + 10)], fill=(255, 255, 255), width=8)
        elif idx % 3 == 1:
            # Gesture: Pointing urgently forward
            draw.line([(cx, cy + head_r + 50), (cx - 80, cy + head_r + 130)], fill=(255, 255, 255), width=8)
            draw.line([(cx, cy + head_r + 50), (cx + 160, cy + head_r + 40)], fill=(255, 255, 255), width=8)
        else:
            # Gesture: Running / Stepping
            draw.line([(cx, cy + head_r + 50), (cx - 110, cy + head_r + 100)], fill=(255, 255, 255), width=8)
            draw.line([(cx, cy + head_r + 50), (cx + 110, cy + head_r + 80)], fill=(255, 255, 255), width=8)

        # Legs
        draw.line([(cx, cy + head_r + 200), (cx - 80, cy + head_r + 370)], fill=(255, 255, 255), width=9)
        draw.line([(cx, cy + head_r + 200), (cx + 80, cy + head_r + 370)], fill=(255, 255, 255), width=9)

        # Top Banner Text with Shadow
        top_text = scene.get("top_text", "")
        if top_text and os.path.exists(config.FONT_TITLE):
            font = ImageFont.truetype(config.FONT_TITLE, 58)
            bbox = draw.textbbox((0, 0), top_text, font=font)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            # Stroke + Glow
            draw.text((tx, 140), top_text, font=font, fill=(255, 220, 0), stroke_width=7, stroke_fill=(0, 0, 0))

        im.save(output_path, "PNG")
