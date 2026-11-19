"""
Topic & Viral Idea Engine for YouTube Shorts Automation.
Generates curiosity-driven topics with paradox hooks and high-retention narrative angles.
Supports AI generation (Gemini) and curated algorithmic templates.
"""

import json
import random
import urllib.request
from typing import Dict, List, Optional
import config

# Built-in High-CTR Curated Viral Topic Bank (Multi-niche)
BUILTIN_TOPICS = [
    {
        "id": "border_time_jump",
        "niche": "Geographical Anomalies",
        "title": "I Walked 1 Step and Traveled 3.5 Hours Back in Time?!",
        "hook": "What if I told you that by taking just one single step... you could travel three and a half hours into the past?",
        "paradox": "China enforces a single timezone across 5,000 km, creating a 3.5-hour official time jump at the Afghanistan border.",
        "twist": "In Western China, people eat dinner under the blazing sun at 10 PM because Beijing commands the clocks!",
        "style": "b1_minimal_handdrawn",
        "language": "hinglish"
    },
    {
        "id": "eiffel_tower_scam",
        "niche": "Historic Heists & Dark Psychology",
        "title": "The Man Who Sold the Eiffel Tower... TWICE!",
        "hook": "In 1925, a con artist sold Paris's most famous landmark for scrap metal... and then he did it AGAIN.",
        "paradox": "He rented a luxury hotel suite, posed as a government director, and forged official Paris city letterheads.",
        "twist": "The victim was so embarrassed he never reported it to the police, allowing Victor Lustig to do the exact same scam a month later!",
        "style": "b4_survival_thriller",
        "language": "english"
    },
    {
        "id": "mary_celeste_ghost_ship",
        "niche": "Unsolved Marine Mysteries",
        "title": "The Ghost Ship With Warm Food and Zero Souls On Board",
        "hook": "In 1872, sailors boarded an abandoned ship in the Atlantic Ocean. The sails were set, breakfast was still warm, but everyone was gone.",
        "paradox": "Not a single drop of blood, no signs of struggle, and six months of fresh water and food completely untouched.",
        "twist": "The secret lay inside 1,700 barrels of industrial alcohol that leaked vapor, causing the captain to abandon ship fearing an explosion that never happened.",
        "style": "b4_survival_thriller",
        "language": "english"
    },
    {
        "id": "sleep_deprivation_record",
        "niche": "Dark Human Psychology",
        "title": "What Happens When You Don't Sleep For 11 Days Straight?",
        "hook": "On day 4, he hallucinated he was a famous football player. On day 8, he lost all short-term memory.",
        "paradox": "In 1964, Randy Gardner stayed awake for 264 hours to break a Guinness World Record.",
        "twist": "After sleeping for 14 hours straight, he woke up completely refreshed—but decades later suffered unbearable insomnia.",
        "style": "b1_minimal_handdrawn",
        "language": "hinglish"
    },
    {
        "id": "taj_mahal_sold_natwarlal",
        "niche": "Great Indian Con Artists",
        "title": "The Conman Who Sold The Taj Mahal 3 Times!",
        "hook": "Mr. Natwarlal sold the Taj Mahal three times, the Red Fort twice, and the Indian Parliament—along with all its 545 politicians!",
        "paradox": "He never used a gun, never used violence—only forged signatures of President Rajendra Prasad.",
        "twist": "Even when caught, he escaped from high-security Indian prisons 8 times, vanishing for good in 1996 at age 84!",
        "style": "b1_minimal_handdrawn",
        "language": "hinglish"
    }
]


class TopicEngine:
    """Manages topic discovery, AI-driven brainstorming, and angle selection."""

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.api_key = gemini_api_key or config.GEMINI_API_KEY

    def get_random_topic(self, niche: Optional[str] = None, language: str = "hinglish") -> Dict:
        """Picks a verified viral topic from the curated bank."""
        filtered = [t for t in BUILTIN_TOPICS if (not niche or t["niche"].lower() == niche.lower())]
        if not filtered:
            filtered = BUILTIN_TOPICS
        topic = random.choice(filtered).copy()
        topic["language"] = language
        return topic

    def generate_ai_topic(self, prompt_seed: str, language: str = "hinglish") -> Dict:
        """
        Uses Gemini API to brainstorm an original viral Shorts idea
        based on the 5-Stage Heartbeat Engine formula.
        Falls back to the curated topic bank if API is unavailable.
        """
        if not self.api_key:
            print("[TopicEngine] No GEMINI_API_KEY detected. Using curated high-CTR topic bank.")
            topic = self.get_random_topic(language=language)
            topic["prompt_seed"] = prompt_seed
            return topic

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        
        system_instruction = (
            "You are a master YouTube Shorts director and retention engineer. "
            "Generate ONE highly viral, addictive YouTube Shorts topic concept. "
            "It must center around a counter-intuitive paradox, bizarre historic event, or unbelievable true mystery. "
            "Return STRICT JSON only matching this schema:\n"
            "{\n"
            '  "id": "short_unique_slug",\n'
            '  "niche": "Category Name",\n'
            '  "title": "Ultra Clicky Title with Emoji under 60 chars",\n'
            '  "hook": "Opening paradox question in 15 words or less",\n'
            '  "paradox": "The cognitive conflict / unbelievable fact",\n'
            '  "twist": "The shocking truth or punchline revealed at the end",\n'
            '  "style": "b1_minimal_handdrawn or b4_survival_thriller",\n'
            '  "language": "hinglish or english"\n'
            "}"
        )

        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_instruction}\nTopic Seed/Idea: {prompt_seed}\nTarget Language: {language}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.8,
                "response_mime_type": "application/json"
            }
        }

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                data = json.loads(text)
                return data
        except Exception as e:
            print(f"[TopicEngine] Gemini API generation error: {e}. Falling back to curated bank.")
            return self.get_random_topic(language=language)


if __name__ == "__main__":
    engine = TopicEngine()
    topic = engine.get_random_topic()
    print("Selected Topic:")
    print(json.dumps(topic, indent=2))
