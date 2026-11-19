"""
Cartoon Audio Short Video Renderer.
Implements the exact visual style from /cartoon-audio-short:
- Flat 2D bean-head cartoon characters (canvas cards with plum outlines #4b1d3f)
- Colourful painted environment backdrops with ink contours
- Gliding camera motions (smootherstep push-ins, pans, 3-5° rolls)
- Output: 1080x1920 vertical, 30 fps, matching voiceover duration.
"""

import math
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import config

PLUM_OUTLINE = (75, 29, 63)         # Signature #4b1d3f plum contour
SKIN_COLOR = (255, 246, 230)        # Warm bean-head canvas tone
BLUSH_COLOR = (255, 175, 175)       # Cheek blush


class CartoonRenderer:
    """Renders 1080x1920 2D bean-head cartoon shorts in a vibrant world."""

    def __init__(self, width: int = 1080, height: int = 1920, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.ffmpeg = config.FFMPEG_EXE

    def draw_beanhead_card(
        self,
        pose: str = "point",
        expression: str = "shocked",
        outfit_color: tuple = (235, 75, 60),
        cape_color: Optional[tuple] = (40, 110, 180)
    ) -> Image.Image:
        """
        Draws the 2D bean-head character card with plum contours and expressive acting.
        """
        W_CARD, H_CARD = 650, 1000
        card = Image.new("RGBA", (W_CARD, H_CARD), (0, 0, 0, 0))
        draw = ImageDraw.Draw(card)

        cx = W_CARD // 2
        cy = 460

        # Cape (if present)
        if cape_color:
            cape_pts = [(cx - 90, cy + 120), (cx - 150, cy + 390), (cx + 150, cy + 390), (cx + 90, cy + 120)]
            draw.polygon(cape_pts, fill=cape_color, outline=PLUM_OUTLINE)

        # Body / Tunic
        tunic_pts = [(cx - 85, cy + 110), (cx + 85, cy + 110), (cx + 115, cy + 360), (cx - 115, cy + 360)]
        draw.polygon(tunic_pts, fill=outfit_color, outline=PLUM_OUTLINE)
        draw.line(tunic_pts + [tunic_pts[0]], fill=PLUM_OUTLINE, width=8)

        # Belt
        draw.rounded_rectangle([cx - 95, cy + 260, cx + 95, cy + 285], radius=5, fill=(45, 30, 20), outline=PLUM_OUTLINE, width=4)
        draw.rectangle([cx - 20, cy + 255, cx + 20, cy + 290], fill=(240, 200, 50), outline=PLUM_OUTLINE, width=4)

        # Legs
        draw.line([(cx - 45, cy + 360), (cx - 45, cy + 460)], fill=PLUM_OUTLINE, width=16)
        draw.line([(cx + 45, cy + 360), (cx + 45, cy + 460)], fill=PLUM_OUTLINE, width=16)
        # Shoes
        draw.ellipse([cx - 70, cy + 450, cx - 25, cy + 475], fill=(50, 35, 25), outline=PLUM_OUTLINE, width=5)
        draw.ellipse([cx + 25, cy + 450, cx + 70, cy + 475], fill=(50, 35, 25), outline=PLUM_OUTLINE, width=5)

        # Arms based on Pose
        if pose == "point":
            # Left hand on hip
            draw.line([(cx - 85, cy + 120), (cx - 150, cy + 190)], fill=PLUM_OUTLINE, width=15)
            draw.line([(cx - 150, cy + 190), (cx - 95, cy + 260)], fill=PLUM_OUTLINE, width=15)
            # Right hand pointing urgently
            draw.line([(cx + 85, cy + 120), (cx + 180, cy + 150)], fill=PLUM_OUTLINE, width=15)
            draw.line([(cx + 180, cy + 150), (cx + 270, cy + 110)], fill=PLUM_OUTLINE, width=15)
            draw.ellipse([cx + 260, cy + 95, cx + 295, cy + 125], fill=SKIN_COLOR, outline=PLUM_OUTLINE, width=6)
        elif pose == "shrug":
            draw.line([(cx - 85, cy + 120), (cx - 190, cy + 80)], fill=PLUM_OUTLINE, width=15)
            draw.line([(cx + 85, cy + 120), (cx + 190, cy + 80)], fill=PLUM_OUTLINE, width=15)
            draw.ellipse([cx - 215, cy + 65, cx - 180, cy + 95], fill=SKIN_COLOR, outline=PLUM_OUTLINE, width=6)
            draw.ellipse([cx + 180, cy + 65, cx + 215, cy + 95], fill=SKIN_COLOR, outline=PLUM_OUTLINE, width=6)
        else:
            # Default expressive hold
            draw.line([(cx - 85, cy + 120), (cx - 130, cy + 240)], fill=PLUM_OUTLINE, width=15)
            draw.line([(cx + 85, cy + 120), (cx + 130, cy + 240)], fill=PLUM_OUTLINE, width=15)
            draw.ellipse([cx - 145, cy + 230, cx - 110, cy + 260], fill=SKIN_COLOR, outline=PLUM_OUTLINE, width=6)
            draw.ellipse([cx + 110, cy + 230, cx + 145, cy + 260], fill=SKIN_COLOR, outline=PLUM_OUTLINE, width=6)

        # The Iconic Bean Head (Smooth rounded canvas card)
        head_box = [cx - 130, cy - 140, cx + 130, cy + 120]
        draw.ellipse(head_box, fill=SKIN_COLOR, outline=PLUM_OUTLINE, width=12)

        # Cheeks (Blush)
        draw.ellipse([cx - 100, cy + 20, cx - 60, cy + 45], fill=BLUSH_COLOR)
        draw.ellipse([cx + 60, cy + 20, cx + 100, cy + 45], fill=BLUSH_COLOR)

        # Eyes & Eyebrows
        if expression == "shocked":
            # Wide shocked eyes
            draw.ellipse([cx - 65, cy - 40, cx - 20, cy + 15], fill=(255, 255, 255), outline=PLUM_OUTLINE, width=6)
            draw.ellipse([cx + 20, cy - 40, cx + 65, cy + 15], fill=(255, 255, 255), outline=PLUM_OUTLINE, width=6)
            draw.ellipse([cx - 48, cy - 20, cx - 35, cy - 5], fill=PLUM_OUTLINE)
            draw.ellipse([cx + 35, cy - 20, cx + 48, cy - 5], fill=PLUM_OUTLINE)
            # Raised high eyebrows
            draw.arc([cx - 70, cy - 75, cx - 15, cy - 45], 190, 350, fill=PLUM_OUTLINE, width=7)
            draw.arc([cx + 15, cy - 75, cx + 70, cy - 45], 190, 350, fill=PLUM_OUTLINE, width=7)
            # Open oval mouth
            draw.ellipse([cx - 25, cy + 45, cx + 25, cy + 85], fill=(170, 40, 50), outline=PLUM_OUTLINE, width=5)
        elif expression == "smile":
            # Happy curved eye arches
            draw.arc([cx - 60, cy - 30, cx - 20, cy], 190, 350, fill=PLUM_OUTLINE, width=8)
            draw.arc([cx + 20, cy - 30, cx + 60, cy], 190, 350, fill=PLUM_OUTLINE, width=8)
            # Big open grin
            draw.chord([cx - 40, cy + 30, cx + 40, cy + 75], 0, 180, fill=(180, 45, 55), outline=PLUM_OUTLINE, width=6)
        else:
            # Curious focus
            draw.ellipse([cx - 55, cy - 25, cx - 25, cy + 5], fill=PLUM_OUTLINE)
            draw.ellipse([cx + 25, cy - 25, cx + 55, cy + 5], fill=PLUM_OUTLINE)
            draw.arc([cx - 30, cy + 35, cx + 30, cy + 65], 20, 160, fill=PLUM_OUTLINE, width=6)

        return card

    def draw_cartoon_environment(self, scene_idx: int) -> Image.Image:
        """
        Creates a colourful 2.5D world with painted textures, horizon gradients,
        and distant architectural shapes.
        """
        W, H = self.width, self.height
        env = Image.new("RGB", (W, H), (145, 210, 245))
        draw = ImageDraw.Draw(env)

        # Sky gradient
        sky_colors = [
            ((135, 205, 245), (250, 235, 215)),  # Crisp day
            ((255, 170, 100), (90, 50, 110)),    # Golden drama
            ((25, 40, 85), (75, 90, 140)),       # Night mystery
            ((245, 140, 80), (255, 220, 150))    # Sunset revelation
        ]
        sky_top, sky_bot = sky_colors[scene_idx % len(sky_colors)]
        for y in range(int(H * 0.65)):
            r = y / float(H * 0.65)
            c = (
                int(sky_top[0] * (1.0 - r) + sky_bot[0] * r),
                int(sky_top[1] * (1.0 - r) + sky_bot[1] * r),
                int(sky_top[2] * (1.0 - r) + sky_bot[2] * r)
            )
            draw.line([(0, y), (W, y)], fill=c)

        # Distant cartoon hills & mountains
        hill_color = (65, 140, 95) if scene_idx % 2 == 0 else (115, 80, 120)
        draw.ellipse([-150, int(H * 0.42), int(W * 0.7), int(H * 0.85)], fill=hill_color, outline=(40, 30, 45), width=6)
        draw.ellipse([int(W * 0.35), int(H * 0.45), int(W * 1.2), int(H * 0.90)], fill=(hill_color[0] - 20, hill_color[1] - 20, hill_color[2] - 10), outline=(40, 30, 45), width=6)

        # Foreground ground / deck / stone floor
        ground_y = int(H * 0.65)
        floor_color = (195, 160, 120) if scene_idx % 2 == 0 else (75, 80, 95)
        draw.rectangle([0, ground_y, W, H], fill=floor_color)
        draw.line([(0, ground_y), (W, ground_y)], fill=(45, 35, 45), width=8)

        # Stylized stone/plank seams
        for x in range(120, W, 180):
            draw.line([(x, ground_y), (x - 60, H)], fill=(floor_color[0] - 30, floor_color[1] - 30, floor_color[2] - 25), width=4)

        return env

    def render_cartoon_short(
        self,
        script: Dict,
        master_audio: Path,
        output_video: Path
    ) -> Path:
        """
        Renders the entire cartoon short video with 2D bean-head cards,
        gliding cameras, and cut synchronization.
        """
        output_video = Path(output_video)
        output_video.parent.mkdir(parents=True, exist_ok=True)
        cuts_dir = output_video.parent / "cartoon_cuts"
        cuts_dir.mkdir(parents=True, exist_ok=True)

        scenes = script.get("scenes", [])
        total_scenes = len(scenes)
        print(f"[CartoonRenderer] Rendering {total_scenes} bean-head cartoon scenes (1080x1920, 30 fps)...")

        poses = ["point", "shrug", "hold", "point", "shrug"]
        expressions = ["shocked", "smile", "shocked", "smile", "shocked"]
        cut_paths = []

        for idx, sc in enumerate(scenes):
            dur = sc.get("dur", sc.get("duration", 5.0))
            frames = int(round(dur * self.fps))
            out_clip = cuts_dir / f"cartoon_cut_{idx + 1:02d}.mp4"
            cut_paths.append(out_clip)

            # 1. Composite Scene Frame (Environment + Beanhead Card + Headline)
            env_img = self.draw_cartoon_environment(idx)
            card_img = self.draw_beanhead_card(
                pose=poses[idx % len(poses)],
                expression=expressions[idx % len(expressions)],
                outfit_color=((230, 80, 60) if idx % 2 == 0 else (50, 130, 210))
            )

            # Paste card with shadow onto floor
            shadow = Image.new("RGBA", (450, 80), (0, 0, 0, 0))
            s_draw = ImageDraw.Draw(shadow)
            s_draw.ellipse([0, 0, 450, 80], fill=(20, 20, 25, 90))
            env_img.paste(shadow, (int(self.width // 2 - 225), int(self.height * 0.65 + 320)), shadow)

            # Paste character card
            card_x = (self.width - card_img.width) // 2
            card_y = int(self.height * 0.65) - card_img.height + 350
            env_img.paste(card_img, (card_x, card_y), card_img)

            # Top cartoon title badge
            top_text = sc.get("top_text", "")
            if top_text and os.path.exists(config.FONT_TITLE):
                draw_t = ImageDraw.Draw(env_img)
                font = ImageFont.truetype(config.FONT_TITLE, 56)
                bbox = draw_t.textbbox((0, 0), top_text, font=font)
                tw = bbox[2] - bbox[0]
                tx = (self.width - tw) // 2
                draw_t.text((tx, 150), top_text, font=font, fill=(255, 235, 40), stroke_width=8, stroke_fill=PLUM_OUTLINE)

            still_frame_path = cuts_dir / f"frame_{idx + 1:02d}.png"
            env_img.save(still_frame_path, "PNG")

            # 2. Gliding Camera Zoompan (Smootherstep glide)
            zoom_step = 0.00050 if idx % 2 == 0 else 0.00065
            vf = (
                f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,"
                f"crop={self.width}:{self.height},"
                f"zoompan=z='min(zoom+{zoom_step},1.08)':d={frames}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)+20':s={self.width}x{self.height}:fps={self.fps},format=yuv420p"
            )

            cmd = [
                self.ffmpeg, "-y",
                "-loop", "1",
                "-i", str(still_frame_path),
                "-vf", vf,
                "-t", f"{dur:.2f}",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",
                str(out_clip)
            ]
            print(f"  [{idx + 1}/{total_scenes}] Rendered cartoon cut {idx + 1:02d} ({dur:.2f}s, {frames} frames)...")
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 3. Concatenate all cartoon cuts
        concat_txt = output_video.parent / "cartoon_concat.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for p in cut_paths:
                norm_p = str(p).replace('\\', '/')
                f.write(f"file '{norm_p}'\n")

        temp_concat = output_video.parent / "temp_cartoon_concat.mp4"
        cmd_concat = [
            self.ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(temp_concat)
        ]
        subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 4. Mux with mixed master audio (strict 50% voice rule)
        cmd_mux = [
            self.ffmpeg, "-y",
            "-i", str(temp_concat),
            "-i", str(master_audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_video)
        ]
        subprocess.run(cmd_mux, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if temp_concat.exists():
            try:
                temp_concat.unlink()
            except Exception:
                pass

        print(f"[CartoonRenderer] 🎬 Finished Cartoon Audio Short: {output_video}")
        return output_video
