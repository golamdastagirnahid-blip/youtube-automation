"""
Thumbnail Generator
Creates unique thumbnails for each video
"""

import os
import time
import random
from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageFilter,
    ImageEnhance
)


THUMBNAILS_DIR   = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "thumbnails"
)
BACKGROUND_IMAGE = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "assets",
    "background.jpg"
)

os.makedirs(THUMBNAILS_DIR, exist_ok=True)


class ThumbnailGenerator:

    def __init__(self):
        self.themes = [
            {
                "name"  : "midnight",
                "bg"    : (10,  10,  40),
                "accent": (100, 149, 237),
                "text"  : (255, 255, 255),
                "glow"  : (70,  130, 180),
            },
            {
                "name"  : "forest",
                "bg"    : (10,  40,  20),
                "accent": (50,  205, 50),
                "text"  : (255, 255, 255),
                "glow"  : (34,  139, 34),
            },
            {
                "name"  : "ocean",
                "bg"    : (0,   20,  60),
                "accent": (0,   191, 255),
                "text"  : (255, 255, 255),
                "glow"  : (0,   150, 200),
            },
            {
                "name"  : "purple",
                "bg"    : (30,  0,   60),
                "accent": (186, 85,  211),
                "text"  : (255, 255, 255),
                "glow"  : (148, 0,   211),
            },
            {
                "name"  : "sunset",
                "bg"    : (40,  10,  10),
                "accent": (255, 140, 0),
                "text"  : (255, 255, 255),
                "glow"  : (255, 69,  0),
            },
            {
                "name"  : "aurora",
                "bg"    : (5,   20,  40),
                "accent": (0,   255, 200),
                "text"  : (255, 255, 255),
                "glow"  : (0,   200, 150),
            },
        ]

    def generate(
        self,
        title    = "Deep Sleep Music",
        part_num = None,
        duration = None
    ):
        pnum = part_num if part_num else 1
        print(f"   Generating thumbnail...")

        unique_id   = int(time.time())
        output_path = os.path.join(
            THUMBNAILS_DIR,
            f"thumb_{unique_id}_p{pnum}.jpg"
        )

        theme = random.choice(self.themes)
        img   = Image.new("RGB", (1280, 720), theme["bg"])
        draw  = ImageDraw.Draw(img)

        self._add_gradient(img, draw, theme)
        self._add_blurred_bg(img, theme)
        self._add_circles(draw, theme)
        self._add_particles(draw, theme)
        self._add_text(draw, theme, title, part_num, duration)

        img = ImageEnhance.Contrast(img).enhance(1.1)
        img = ImageEnhance.Brightness(img).enhance(1.05)
        img.save(output_path, "JPEG", quality=95)

        print(f"   Thumbnail: {output_path}")
        return output_path

    def _add_gradient(self, img, draw, theme):
        w, h = img.size
        for y in range(h):
            a = y / h
            r = int(theme["bg"][0] * (1 - a * 0.3))
            g = int(theme["bg"][1] * (1 - a * 0.3))
            b = int(theme["bg"][2] * (1 - a * 0.3))
            draw.line([(0, y), (w, y)], fill=(r, g, b))

    def _add_blurred_bg(self, img, theme):
        try:
            if os.path.exists(BACKGROUND_IMAGE):
                bg = Image.open(
                    BACKGROUND_IMAGE
                ).convert("RGB")
                bg = bg.resize((1280, 720))
                bg = bg.filter(
                    ImageFilter.GaussianBlur(radius=15)
                )
                bg = ImageEnhance.Brightness(bg).enhance(0.3)
                img.paste(bg, (0, 0))
        except Exception:
            pass

    def _add_circles(self, draw, theme):
        draw.ellipse(
            [440, 160, 840, 560],
            outline=theme["glow"], width=2
        )
        draw.ellipse(
            [500, 200, 780, 520],
            outline=theme["accent"], width=1
        )
        draw.ellipse(
            [580, 260, 700, 460],
            outline=theme["accent"], width=3
        )
        draw.rectangle(
            [0, 0, 1280, 8],
            fill=theme["accent"]
        )
        draw.rectangle(
            [0, 712, 1280, 720],
            fill=theme["accent"]
        )

    def _add_particles(self, draw, theme):
        for _ in range(80):
            x    = random.randint(0, 1280)
            y    = random.randint(0, 720)
            size = random.randint(1, 3)
            draw.ellipse(
                [x-size, y-size, x+size, y+size],
                fill=theme["text"]
            )

    def _add_text(
        self, draw, theme,
        title    = "Deep Sleep",
        part_num = None,
        duration = None
    ):
        # Clean title
        clean = title.strip()
        for p in ["No Ads ", "🔴 ", "🎵 ", "✨ ", "⚡ "]:
            clean = clean.replace(p, "")

        words = clean.split()
        if len(words) <= 3:
            line1 = clean
            line2 = ""
        elif len(words) <= 6:
            mid   = len(words) // 2
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])
        else:
            line1 = " ".join(words[:3])
            line2 = " ".join(words[3:6])

        if len(line1) > 20:
            line1 = line1[:18] + "..."
        if len(line2) > 20:
            line2 = line2[:18] + "..."

        part_text = f"Part {part_num}" if part_num else "Full Version"
        dur_text  = f"⏱ {duration}"   if duration  else ""

        # Load fonts
        font_large  = None
        font_medium = None
        font_small  = None

        for fp in [
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\verdanab.ttf",
            "C:\\Windows\\Fonts\\calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]:
            if os.path.exists(fp):
                try:
                    font_large  = ImageFont.truetype(fp, 90)
                    font_medium = ImageFont.truetype(fp, 58)
                    font_small  = ImageFont.truetype(fp, 38)
                    break
                except Exception:
                    continue

        if not font_large:
            font_large  = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small  = ImageFont.load_default()

        # Line 1
        draw.text(
            (643, 153), line1,
            font=font_large, fill=(0, 0, 0), anchor="mm"
        )
        draw.text(
            (640, 150), line1,
            font=font_large, fill=theme["text"], anchor="mm"
        )

        # Line 2
        if line2:
            draw.text(
                (643, 263), line2,
                font=font_large, fill=(0, 0, 0), anchor="mm"
            )
            draw.text(
                (640, 260), line2,
                font=font_large, fill=theme["accent"], anchor="mm"
            )
            base = 280
        else:
            base = 180

        # Part text
        draw.text(
            (640, base + 120), part_text,
            font=font_medium, fill=theme["text"], anchor="mm"
        )

        # Duration
        if dur_text:
            draw.text(
                (640, base + 190), dur_text,
                font=font_small, fill=theme["accent"], anchor="mm"
            )

        # Branding
        draw.text(
            (640, 660),
            "🌙  Sleep  •  Relax  •  Meditate  🌙",
            font=font_small, fill=theme["glow"], anchor="mm"
        )
