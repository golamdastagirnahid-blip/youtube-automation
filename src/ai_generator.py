"""
AI Generator
Uses OpenRouter free API to generate
unique titles and descriptions
"""

import os
import json
import requests


class AIGenerator:

    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.url     = "https://openrouter.ai/api/v1/chat/completions"
        self.model   = "google/gemini-2.0-flash-exp:free"

    def generate_metadata(self, original_title, part_num=1, total_parts=1):
        if not self.api_key:
            print("   No OpenRouter API key - using default title")
            return self._default_metadata(
                original_title, part_num, total_parts
            )

        if total_parts > 1:
            part_info = f"Part {part_num} of {total_parts}"
        else:
            part_info = "Full Version"

        prompt = f"""
You are a YouTube SEO expert for sleep and relaxation content.

Create an engaging YouTube title and description for a sleep/relaxation video.

Original title: "{original_title}"
Part info: "{part_info}"
Theme: "Heavy Rain Deep Sleep"

Requirements for TITLE:
- Maximum 80 characters
- Include sleep/relax keywords
- Include part number if applicable
- Make it engaging and clickable
- Include hours duration

Requirements for DESCRIPTION:
- 150-200 words
- Include sleep benefits
- Include relevant hashtags
- Professional and calming tone

Return ONLY valid JSON:
{{
  "title": "your title here",
  "description": "your description here"
}}
"""

        try:
            print("   Generating AI metadata...")
            response = requests.post(
                url     = self.url,
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type" : "application/json",
                    "HTTP-Referer" : "https://github.com",
                },
                data    = json.dumps({
                    "model"   : self.model,
                    "messages": [{
                        "role"   : "user",
                        "content": prompt
                    }],
                    "max_tokens": 500,
                }),
                timeout = 30
            )

            data    = response.json()
            content = data["choices"][0]["message"]["content"]

            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            metadata = json.loads(content.strip())
            title    = metadata.get("title", "")
            desc     = metadata.get("description", "")

            if title:
                print(f"   AI Title: {title}")
                return title[:80], desc
            else:
                return self._default_metadata(
                    original_title, part_num, total_parts
                )

        except Exception as e:
            print(f"   AI error: {e}")
            return self._default_metadata(
                original_title, part_num, total_parts
            )

    def _default_metadata(
        self,
        original_title,
        part_num=1,
        total_parts=1
    ):
        import random

        templates = [
            "Heavy Rain Deep Sleep | {hours} Hours | Part {part}",
            "Deep Sleep Rain Sounds | {hours} Hours White Noise | Part {part}",
            "Heavy Rain for Sleep | {hours} Hours | Part {part}",
            "Sleep Instantly with Rain | {hours} Hours | Part {part}",
            "Relaxing Rain Sounds | Deep Sleep {hours} Hours | Part {part}",
        ]

        hours = 4
        title = random.choice(templates).format(
            hours = hours,
            part  = f"{part_num}/{total_parts}"
        )

        desc = f"""Heavy Rain Deep Sleep - Part {part_num} of {total_parts}

Fall asleep fast with the soothing sounds of heavy rain.
This {hours}-hour sleep session is perfect for:

- Deep sleep and relaxation
- Stress and anxiety relief
- Study and focus sessions
- Meditation and mindfulness
- White noise for better sleep

Subscribe for daily sleep content!
Like if this helped you sleep better!

#DeepSleep #RainSounds #SleepMusic #Relaxation
#WhiteNoise #SleepAid #HeavyRain #Meditation
"""
        return title, desc
