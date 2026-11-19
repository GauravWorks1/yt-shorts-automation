"""
Metadata & SEO Engine for YouTube Shorts Automation.
Generates viral titles, optimized descriptions with hashtags,
comprehensive tag clouds, and discussion-starting pinned comments.
"""

from typing import Dict, List


class MetadataEngine:
    """Creates metadata optimized for YouTube recommendation algorithm."""

    @staticmethod
    def generate_metadata(topic: Dict, script: Dict) -> Dict:
        raw_title = script.get("title") or topic.get("title", "Incredible True Story")
        
        # Clean title ensuring it has curiosity element and fits under 90 characters
        clean_title = raw_title.strip()
        if not ("#Shorts" in clean_title or "#shorts" in clean_title):
            if len(clean_title) + len(" #Shorts") <= 95:
                title = f"{clean_title} #Shorts"
            else:
                title = clean_title
        else:
            title = clean_title

        # Build Description
        hook = topic.get("hook", "")
        twist = topic.get("twist", "")
        niche = topic.get("niche", "Facts & Mysteries")
        
        description_lines = [
            f"{hook}",
            "",
            f"{twist}",
            "",
            "⏱️ TIMESTAMPS / BEATS:",
        ]
        
        elapsed = 0.0
        for s in script.get("scenes", []):
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            description_lines.append(f"{mins:02d}:{secs:02d} - {s.get('beat_name', 'Scene')}")
            elapsed += s.get("duration", 5.0)

        description_lines.extend([
            "",
            "🔔 Subscribe to the channel for daily mind-bending stories and animated shorts!",
            "👍 Like and share if you learned something unbelievable today.",
            "",
            f"Category: {niche}",
            "Style: Stickman Narrative 2D Animation",
            "",
            "#Shorts #YouTubeShorts #Viral #Storytelling #MindBlowingFacts #HistoryMysteries #DidYouKnow #TrendingShorts"
        ])

        description = "\n".join(description_lines)

        # Build Tags
        base_tags = [
            "shorts",
            "youtube shorts",
            "viral shorts",
            "animated story",
            "stickman animation",
            "mind blowing facts",
            "true story",
            "mystery",
            "interesting facts",
            "did you know",
            "hindi facts",
            "curious stories",
            "viral video",
            "trending",
            "educational animation"
        ]
        
        # Add niche specific keywords
        title_words = [w.lower().strip("?!.,#") for w in clean_title.split() if len(w) > 3]
        combined_tags = list(dict.fromkeys(base_tags + title_words))[:30]

        # Pinned comment
        pinned_comment = (
            f"💬 QUESTION: What would YOU do if you were in this situation? "
            f"Tell us in the comments! 👇 (Don't forget to subscribe for part 2!)"
        )

        return {
            "title": title,
            "description": description,
            "tags": combined_tags,
            "category_id": "27",  # Education (or '24' Entertainment)
            "pinned_comment": pinned_comment,
            "privacy": "public"
        }


if __name__ == "__main__":
    test_topic = {
        "title": "I Walked 1 Step and Traveled 3.5 Hours Back in Time?!",
        "hook": "What if you could travel 3.5 hours into the past by taking one single step?",
        "twist": "China enforces a single timezone across 5,000 km, creating a 3.5-hour official time jump.",
        "niche": "Geographical Anomalies"
    }
    test_script = {
        "title": test_topic["title"],
        "scenes": [
            {"beat_name": "The Impossible Border", "duration": 8.0},
            {"beat_name": "One Clock Rule", "duration": 10.0},
            {"beat_name": "Midnight Sun", "duration": 12.0},
            {"beat_name": "The Final Verdict", "duration": 10.0}
        ]
    }
    meta = MetadataEngine.generate_metadata(test_topic, test_script)
    print("Generated Title:", meta["title"])
    print("\nDescription Preview:\n", meta["description"][:200], "...")
    print("\nTags Count:", len(meta["tags"]))
