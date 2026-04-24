import requests
import os
import json

class AIGenerator:
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def generate_metadata(self, original_title):
        if not self.api_key:
            print("⚠️ No AI Key found, using original title.")
            return original_title, "Relaxing sounds for deep sleep and focus."

        prompt = f"Create a viral, SEO-friendly YouTube title and a short 2-line description for a relaxing video originally titled: '{original_title}'. Return ONLY JSON format: {{\"title\": \"...\", \"description\": \"...\"}}"

        try:
            response = requests.post(
                url=self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": "google/gemini-2.0-flash-exp:free",
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            data = response.json()
            content = data['choices'][0]['message']['content']
            # Parse the JSON from AI
            metadata = json.loads(content)
            return metadata.get("title"), metadata.get("description")
        except Exception as e:
            print(f"⚠️ AI Error: {e}")
            return f"Beautiful {original_title}", "Relaxing music for you."
