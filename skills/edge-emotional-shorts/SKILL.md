---
name: edge-emotional-shorts
description: Autonomous generation of viral YouTube Shorts with Microsoft Edge Emotional TTS (hi-IN-MadhurNeural, hi-IN-SwaraNeural), line-by-line rate and pitch modulation, scene-synchronized cuts, dynamic Ken Burns camera motion, and burned ASS subtitles.
---

# Edge Emotional Shorts: Autonomous Viral Video Generation

Generate 1080x1920 (9:16 vertical) viral YouTube Shorts using **Microsoft Edge Emotional TTS** (zero-cost, high-retention narration with per-line pitch and rate modulation) and the **Signature Multi-Cut Ken Burns Video Assembly Engine**.

---

## 🎭 1. The Voice Modulation Engine (Edge-TTS)

Instead of flat, monotonous robotic text-to-speech, every spoken beat is dynamically modulated using tailored `rate` and `pitch` offsets matching the story's emotional arc:

| Emotion Beat | Edge-TTS Voice | Rate Offset | Pitch Offset | Story Stage & Acting Intent |
| :--- | :--- | :--- | :--- | :--- |
| **Curious Hook** | `hi-IN-MadhurNeural` | `+7%` | `+0Hz` | Engaging opener; creates curiosity gap |
| **Comedic Twist** | `hi-IN-MadhurNeural` | `+10%` | `+2Hz` | Punchy inflection; ironic comedic reaction |
| **Angry / Shout** | `hi-IN-MadhurNeural` | `+16%` | `+15Hz` | High urgency, character shouting / panic |
| **Dark Suspense** | `hi-IN-MadhurNeural` | `+5%` | `-3Hz` | Low, tense, mysterious, slow build |
| **Snitch / Playful** | `hi-IN-MadhurNeural` | `+18%` | `+14Hz` | Fast, naughty, secret-spilling cadence |
| **Grumpy / Tapori** | `hi-IN-MadhurNeural` | `+4%` | `-14Hz` | Heavy bass, authoritative, desi bhai persona |
| **Revelation** | `hi-IN-MadhurNeural` | `+8%` | `+3Hz` | Shocking cognitive payoff, mind-blown beat |
| **Outro / CTA** | `hi-IN-MadhurNeural` | `+9%` | `+1Hz` | Urgent comment prompt & subscribe trigger |

*Female Voice Alternative:* `hi-IN-SwaraNeural` (same rate/pitch offsets apply).
*English Voice Alternative:* `en-IN-PrabhatNeural` or `en-IN-NeerjaNeural`.

---

## 🎬 2. The Signature Video Generation Workflow

1. **Audio-Driven Scene Timing**:
   Never enforce static 5-second or 10-second cuts. Each scene's audio line is synthesized and measured individually (`dur`). The visual cut duration matches the speech beat down to the exact millisecond (`round(dur * 30)` frames).

2. **Dynamic Ken Burns Camera Motion**:
   Every cut uses a specialized FFmpeg `zoompan` filter with custom zoom speeds and vertical focal points:
   ```bash
   scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.00055,1.09)':d=FRAMES:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)+40':s=1080x1920:fps=30,format=yuv420p
   ```
   Alternating focus points:
   - Scene 1: Centered `ih/2-(ih/zoom/2)`
   - Scene 2: Lower third focus `ih/2-(ih/zoom/2)+40`
   - Scene 3: Upper character face focus `ih/2-(ih/zoom/2)-50`

3. **Burned ASS Subtitles**:
   - Header banner at top (`HeaderStyle`, yellow/cyan `&H0000D7FF`)
   - Dialogue subtitles at bottom (`SubStyle`, clean white `&H00FFFFFF` with black outline and soft shadow)
   - Fast reading cadence (5–8 words per subtitle cue).

4. **Audio Ducking**:
   - Background music sits at `-16dB` to `-18dB` (`volume=0.14`) under the narration.
   - Narration sits at `1.0` (normalized).

---

## 🚀 3. Quick Commands

### Run Automation with Edge Emotional Voice:
```powershell
python run_pipeline.py --topic "auto" --voice "hi-IN-MadhurNeural"
```

### Connect Google Flow Video Renders to YouTube Upload:
```powershell
python connect_flow_and_upload.py --video "output/flow_render.mp4" --privacy "public"
```

### Run Background Daemon Watcher:
```powershell
python connect_flow_and_upload.py --watch
```
