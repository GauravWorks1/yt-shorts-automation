"""
Subtitles Generator for YouTube Shorts Automation.
Produces dynamic ASS (Advanced SubStation Alpha) and SRT subtitles
with custom fonts, outlines, drop shadows, and position formatting.
"""

from pathlib import Path
from typing import Dict, List, Optional
import config


class SubtitlesGenerator:
    """Creates stylized animated subtitles for Shorts."""

    @staticmethod
    def format_timestamp_ass(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    @staticmethod
    def generate_ass(
        script: Dict,
        output_path: Path,
        play_res_x: int = 1080,
        play_res_y: int = 1920
    ) -> Path:
        """
        Builds an ASS subtitle file formatted for 9:16 Shorts with
        HeaderStyle and HighlightSub styles.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        header = f"""[Script Info]
Title: Automated YouTube Shorts Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: HeaderStyle,Arial,58,&H0000D7FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5.0,2.0,8,40,40,60,1
Style: SubStyle,Nirmala UI,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5.0,2.0,2,50,50,220,1
Style: HighlightSub,Nirmala UI,50,&H0030EAFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5.5,2.0,2,50,50,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        elapsed = 0.0

        for scene in script.get("scenes", []):
            duration = scene.get("duration", 6.0)
            start_t = elapsed
            end_t = elapsed + duration
            elapsed = end_t

            start_str = SubtitlesGenerator.format_timestamp_ass(start_t)
            end_str = SubtitlesGenerator.format_timestamp_ass(end_t)

            # Top Header banner
            top_text = scene.get("top_text", "")
            if top_text:
                events.append(f"Dialogue: 1,{start_str},{end_str},HeaderStyle,,0,0,0,,{top_text}")

            # Dialogue lines (chunked into natural phrases)
            narration = scene.get("narration", "")
            words = narration.split()
            if not words:
                continue

            # Break into 5-8 word chunks for quick reading in Shorts
            chunk_size = 7
            sub_chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
            chunk_duration = duration / max(len(sub_chunks), 1)

            c_start = start_t
            for i, chunk in enumerate(sub_chunks):
                c_end = c_start + chunk_duration
                c_start_str = SubtitlesGenerator.format_timestamp_ass(c_start)
                c_end_str = SubtitlesGenerator.format_timestamp_ass(c_end)
                phrase = " ".join(chunk)

                # Alternate highlight style for rhythmic cadence
                style_name = "HighlightSub" if i % 2 == 1 else "SubStyle"
                events.append(f"Dialogue: 0,{c_start_str},{c_end_str},{style_name},,0,0,0,,{phrase}")
                c_start = c_end

        content = header + "\n".join(events) + "\n"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[SubtitlesGenerator] Subtitles saved to {output_path}")
        return output_path


if __name__ == "__main__":
    from script_engine import ScriptEngine
    from topic_engine import TopicEngine
    t = TopicEngine().get_random_topic()
    s = ScriptEngine().generate_script(t)
    ass_file = config.OUTPUT_DIR / "sample.ass"
    SubtitlesGenerator.generate_ass(s, ass_file)
    print("ASS file generated successfully:", ass_file.exists())
