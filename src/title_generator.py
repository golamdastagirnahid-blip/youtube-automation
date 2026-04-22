import random
from datetime import datetime
from src.config import TITLE_PREFIX, TITLE_SUFFIX

class TitleGenerator:
    def generate_title(self, original_title):
        if not original_title:
            return "Untitled Video"
        
        title = original_title.strip()
        if TITLE_PREFIX:
            title = f"{TITLE_PREFIX} {title}"
        if TITLE_SUFFIX:
            title = f"{title} {TITLE_SUFFIX}"
        
        emojis = ["🔥", "✨", "🎯", "💯", "⚡"]
        if random.random() > 0.5:
            title = f"{random.choice(emojis)} {title}"
            
        return title[:95]

    def generate_description(self, original_desc=""):
        lines = [
            "Enjoy this video!",
            "",
            original_desc[:400],
            "",
            "👍 Like | 🔔 Subscribe for more",
            f"Uploaded on {datetime.now().strftime('%Y-%m-%d')}"
        ]
        return "\n".join(lines)