"""
Script Engine for YouTube Shorts Automation.
Implements the 5-Stage High-Completion Heartbeat Engine:
1. Golden Hook (0-3s)
2. Disrupting Assumptions (3-12s)
3. Unveiling Insider Secrets (12-28s)
4. Ultimate Truth Revelation (28-42s)
5. Elevation & High-Engagement Discussion (42-50s)
"""

import json
import urllib.request
from typing import Dict, List, Optional
import config


class ScriptEngine:
    """Generates viral, retention-engineered scripts for YouTube Shorts."""

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.api_key = gemini_api_key or config.GEMINI_API_KEY

    def generate_script(self, topic: Dict) -> Dict:
        """
        Creates a structured script with timing, narration, visual descriptions,
        SFX cues, and scene breakdowns.
        """
        if self.api_key:
            try:
                return self._generate_ai_script(topic)
            except Exception as e:
                print(f"[ScriptEngine] AI generation failed ({e}). Using algorithmic generator.")

        return self._generate_algorithmic_script(topic)

    def _generate_ai_script(self, topic: Dict) -> Dict:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        
        prompt = f"""
You are a viral YouTube Shorts scriptwriter. Write an addictive 45-50 second script following the 5-Stage High-Completion formula.
Topic: {topic.get('title')}
Paradox/Hook: {topic.get('hook')}
Fact/Twist: {topic.get('twist')}
Language: {topic.get('language', 'hinglish')} (If hinglish, use conversational Roman Hindi/English or Devanagari Hindi as appropriate for TTS).

Format your response STRICTLY as valid JSON with this exact structure:
{{
  "title": "{topic.get('title')}",
  "total_duration": 48,
  "language": "{topic.get('language', 'hinglish')}",
  "scenes": [
    {{
      "scene_num": 1,
      "beat_name": "Golden Hook",
      "duration": 8.0,
      "narration": "Narration text for scene 1...",
      "visual_prompt": "Minimalist stick figure staring at giant split clock on border line, dramatic 2D animation.",
      "sfx": "clock_tick_whoosh",
      "top_text": "HOOK HEADLINE?!",
      "bottom_text": "Sub text"
    }},
    {{
      "scene_num": 2,
      "beat_name": "Disrupting Assumptions",
      "duration": 9.0,
      "narration": "Narration text...",
      "visual_prompt": "Map of country showing 5 timezones being erased by government hand.",
      "sfx": "paper_tear",
      "top_text": "ONE CLOCK ONLY?!",
      "bottom_text": "Sub text"
    }},
    {{
      "scene_num": 3,
      "beat_name": "Unveiling Insider Secrets",
      "duration": 11.0,
      "narration": "Narration text...",
      "visual_prompt": "Stickman in dark school with lantern while Beijing clock shows 8:30 AM.",
      "sfx": "school_bell",
      "top_text": "SCHOOL IN THE DARK?!",
      "bottom_text": "Sub text"
    }},
    {{
      "scene_num": 4,
      "beat_name": "Ultimate Truth Revelation",
      "duration": 12.0,
      "narration": "Narration text...",
      "visual_prompt": "Stickman stepping across border line into snow mountain, time jump effect.",
      "sfx": "magic_warp",
      "top_text": "3.5 HOUR TIME JUMP!",
      "bottom_text": "Sub text"
    }},
    {{
      "scene_num": 5,
      "beat_name": "Elevation & Discussion",
      "duration": 8.0,
      "narration": "Narration text with strong comment prompt...",
      "visual_prompt": "Stickman pointing directly at camera with question mark bubble above head.",
      "sfx": "ding_accent",
      "top_text": "WOULD YOU DO IT?!",
      "bottom_text": "Comment Below!"
    }}
  ],
  "full_voiceover_text": "Combined full text for text-to-speech audio generation..."
}}
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "response_mime_type": "application/json"}
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            content = res["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(content)

    def _generate_algorithmic_script(self, topic: Dict) -> Dict:
        """Fallback rule-based script synthesizer tailored for high retention."""
        lang = topic.get("language", "hinglish")
        topic_id = topic.get("id", "border_time_jump")

        if "border" in topic_id or "time" in topic_id:
            scenes = [
                {
                    "scene_num": 1,
                    "beat_name": "Golden Hook",
                    "duration": 8.5,
                    "narration": "Agar main aapse kahun... ki aap sirf ek kadam chalkar time travel kar sakte hain... toh kya aap vishwas karenge?!",
                    "visual_prompt": "Minimalist stick figure looking shocked at a mysterious border line with two glowing clocks.",
                    "sfx": "whoosh_tick",
                    "top_text": "TIME TRAVEL IN 1 STEP?!",
                    "bottom_text": "Sach ya Sapna?"
                },
                {
                    "scene_num": 2,
                    "beat_name": "Disrupting Assumptions",
                    "duration": 9.5,
                    "narration": "Yeh koi sci-fi film nahi hai! Yeh sach me hota hai China aur Afghanistan ke border par, jahan sabse khatarnak barfeeli pahadiyan hain!",
                    "visual_prompt": "Stickman standing on icy mountain ridge on the border with directional signs.",
                    "sfx": "wind_howl",
                    "top_text": "CHINA - AFGHAN BORDER",
                    "bottom_text": "Duniya Ka Sabse Bada Jump!"
                },
                {
                    "scene_num": 3,
                    "beat_name": "Unveiling Secrets",
                    "duration": 10.0,
                    "narration": "China pure desh me sirf ek hi ghadi maanta hai—Beijing time! Yani jab yahan dopahar ke baarah bajte hain, toh border ke theek uss paar subah ke sirf sade aath baj rahe hote hain!",
                    "visual_prompt": "Giant map comparing Beijing noon sunshine vs western dark mountains with clock overlay.",
                    "sfx": "clock_gong",
                    "top_text": "1 COUNTRY, 1 CLOCK?!",
                    "bottom_text": "3.5 Hours Difference!"
                },
                {
                    "scene_num": 4,
                    "beat_name": "Ultimate Truth Revelation",
                    "duration": 11.5,
                    "narration": "Matlab... agar aap China se sirf ek kadam uthakar Afghanistan me rakh dein, toh ek hi second me aap sade teen ghante past me chale jayenge! Yeh poori dharti ka sabse bada official time jump hai!",
                    "visual_prompt": "Stickman stepping over line with lightning portal trail, time rewinding visibly.",
                    "sfx": "warp_jump",
                    "top_text": "OFFICIAL TIME JUMP!",
                    "bottom_text": "-3.5 Hours Instantly!"
                },
                {
                    "scene_num": 5,
                    "beat_name": "Elevation & Discussion",
                    "duration": 8.5,
                    "narration": "Lekin wahan raat ke 10 baje dhoop kyon chamakti hai? Kya aap aise timezone me reh sakte hain? Comment karke zaroor batao aur subscribe karna mat bhoolna!",
                    "visual_prompt": "Stickman under midnight sun eating dinner, pointing at subscribe button.",
                    "sfx": "bell_ding",
                    "top_text": "WOULD YOU LIVE HERE?",
                    "bottom_text": "Comment & Subscribe!"
                }
            ]
        else:
            # Universal mystery / thriller format
            scenes = [
                {
                    "scene_num": 1,
                    "beat_name": "Golden Hook",
                    "duration": 8.0,
                    "narration": f"Here is the bizarre true story of {topic.get('title')} that history tried to forget!",
                    "visual_prompt": "Dramatic mystery character silhouette with glowing yellow question mark.",
                    "sfx": "dramatic_boom",
                    "top_text": "SECRET REVEALED!",
                    "bottom_text": "True Story"
                },
                {
                    "scene_num": 2,
                    "beat_name": "Disrupting Assumptions",
                    "duration": 9.5,
                    "narration": f"{topic.get('hook')} Everyone believed it was impossible, but the reality was terrifyingly simple.",
                    "visual_prompt": "Stickman uncovering hidden blueprint document under magnifying glass.",
                    "sfx": "paper_rustle",
                    "top_text": "NOBODY SUSPECTED!",
                    "bottom_text": "The Hidden Secret"
                },
                {
                    "scene_num": 3,
                    "beat_name": "Unveiling Secrets",
                    "duration": 10.5,
                    "narration": f"{topic.get('paradox')} Watch closely how this played out in broad daylight.",
                    "visual_prompt": "Visual sequence showing step-by-step master plan unfolding.",
                    "sfx": "footsteps_fast",
                    "top_text": "STEP BY STEP!",
                    "bottom_text": "Unbelievable Plan"
                },
                {
                    "scene_num": 4,
                    "beat_name": "Ultimate Revelation",
                    "duration": 11.0,
                    "narration": f"{topic.get('twist')}",
                    "visual_prompt": "Stickman staring in absolute shock as the puzzle pieces lock together.",
                    "sfx": "mind_blow",
                    "top_text": "THE SHOCKING TWIST!",
                    "bottom_text": "How It Ended"
                },
                {
                    "scene_num": 5,
                    "beat_name": "Elevation & CTA",
                    "duration": 8.0,
                    "narration": "What would YOU have done in this exact situation? Drop your honest thought below and hit follow!",
                    "visual_prompt": "Stickman pointing at screen with animated comment bubble and heart.",
                    "sfx": "chime_bell",
                    "top_text": "WHAT WOULD YOU DO?",
                    "bottom_text": "Comment Below!"
                }
            ]

        full_vo = " ".join([s["narration"] for s in scenes])
        return {
            "title": topic.get("title", "Untitled Shorts"),
            "total_duration": sum([s["duration"] for s in scenes]),
            "language": lang,
            "scenes": scenes,
            "full_voiceover_text": full_vo
        }


if __name__ == "__main__":
    from topic_engine import TopicEngine
    topic = TopicEngine().get_random_topic()
    script = ScriptEngine().generate_script(topic)
    print(f"Generated Script: {script['title']}")
    print(f"Total Duration: {script['total_duration']}s")
    for s in script["scenes"]:
        print(f"[{s['scene_num']}] {s['beat_name']} ({s['duration']}s): {s['narration'][:50]}...")
