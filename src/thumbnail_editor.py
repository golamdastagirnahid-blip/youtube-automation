"""
Thumbnail Generator
Creates unique engaging thumbnails for each video part
Using Pillow - no external API needed
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
from src.config import THUMBNAILS_DIR, BACKGROUND_IMAGE


class ThumbnailGenerator:

    def __init__(self):
        os.makedirs(THUMBNAILS_DIR, exist_ok=True)

        # ── Color themes ──────────────────────────
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
            {
                "name"  : "rose",
                "bg"    : (40,  5,   20),
                "accent": (255, 105, 180),
                "text"  : (255, 255, 255),
                "glow"  : (220, 20,  60),
            },
        ]

    # ─────────────────────────────────────────────
    # Main Generate Function
    # ─────────────────────────────────────────────
    def generate(
        self,
        title    = "Deep Sleep Music",
        part_num = None,
        duration = None
    ):
        """
        Generate unique thumbnail
        Args:
            title    : Video title string
            part_num : Part number (None if single part)
            duration : Duration string like "4h 0m"
        Returns:
            path to saved thumbnail
        """
        pnum = part_num if part_num else 1

        print(f"   🎨 Generating thumbnail (Part {pnum})...")

        # Unique filename using timestamp
        unique_id   = int(time.time())
        output_path = os.path.join(
            THUMBNAILS_DIR,
            f"thumb_{unique_id}_p{pnum}.jpg"
        )

        # Pick random theme
        theme = random.choice(self.themes)

        # Create base image 1280x720
        img  = Image.new("RGB", (1280, 720), theme["bg"])
        draw = ImageDraw.Draw(img)

        # Add layers
        self._add_gradient(img, draw, theme)
        self._add_blurred_bg(img, theme)
        self._add_circles(draw, theme)
        self._add_particles(draw, theme)
        self._add_text(
            draw, theme, title, part_num, duration
        )

        # Final enhancement
        img = ImageEnhance.Contrast(img).enhance(1.1)
        img = ImageEnhance.Brightness(img).enhance(1.05)

        # Save high quality
        img.save(output_path, "JPEG", quality=95)
        print(f"   ✅ Thumbnail saved: {output_path}")
        return output_path

    # ─────────────────────────────────────────────
    # Add Gradient Background
    # ─────────────────────────────────────────────
    def _add_gradient(self, img, draw, theme):
        width, height = img.size
        for y in range(height):
            alpha = y / height
            r = int(theme["bg"][0] * (1 - alpha * 0.3))
            g = int(theme["bg"][1] * (1 - alpha * 0.3))
            b = int(theme["bg"][2] * (1 - alpha * 0.3))
            draw.line(
                [(0, y), (width, y)],
                fill=(r, g, b)
            )

    # ─────────────────────────────────────────────
    # Add Blurred Background Image
    # ─────────────────────────────────────────────
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

    # ─────────────────────────────────────────────
    # Add Decorative Circles
    # ─────────────────────────────────────────────
    def _add_circles(self, draw, theme):
        # Large outer circle
        draw.ellipse(
            [440, 160, 840, 560],
            outline = theme["glow"],
            width   = 2
        )
        # Medium circle
        draw.ellipse(
            [500, 200, 780, 520],
            outline = theme["accent"],
            width   = 1
        )
        # Small inner circle
        draw.ellipse(
            [580, 260, 700, 460],
            outline = theme["accent"],
            width   = 3
        )
        # Corner accents
        draw.ellipse(
            [20, 20, 80, 80],
            outline = theme["accent"],
            width   = 2
        )
        draw.ellipse(
            [1200, 20, 1260, 80],
            outline = theme["accent"],
            width   = 2
        )
        draw.ellipse(
            [20, 640, 80, 700],
            outline = theme["glow"],
            width   = 2
        )
        draw.ellipse(
            [1200, 640, 1260, 700],
            outline = theme["glow"],
            width   = 2
        )

    # ─────────────────────────────────────────────
    # Add Star Particles
    # ─────────────────────────────────────────────
    def _add_particles(self, draw, theme):
        for _ in range(80):
            x    = random.randint(0, 1280)
            y    = random.randint(0, 720)
            size = random.randint(1, 3)
            draw.ellipse(
                [x-size, y-size, x+size, y+size],
                fill=theme["text"]
            )

    # ─────────────────────────────────────────────
    # Add Text
    # ─────────────────────────────────────────────
    def _add_text(
        self,
        draw,
        theme,
        title    = "Deep Sleep",
        part_num = None,
        duration = None
    ):
        """Add all text elements to thumbnail"""

        # ── Prepare title text ─────────────────────
        # Clean and shorten title
        clean_title = title.strip()

        # Remove common prefixes that are too long
        for prefix in [
            "No Ads ", "🔴 ", "🎵 ", "✨ ",
            "⚡ ", "🔥 ", "💯 "
        ]:
            clean_title = clean_title.replace(prefix, "")

        # Split into max 2 lines
        words = clean_title.split()
        if len(words) <= 3:
            line1 = clean_title
            line2 = ""
        elif len(words) <= 6:
            mid   = len(words) // 2
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])
        else:
            # Take first 3 words for line 1
            # next 3 for line 2
            line1 = " ".join(words[:3])
            line2 = " ".join(words[3:6])

        # Truncate if still too long
        if len(line1) > 20:
            line1 = line1[:18] + "..."
        if len(line2) > 20:
            line2 = line2[:18] + "..."

        # ── Part and duration text ─────────────────
        if part_num:
            part_text = f"Part {part_num}"
        else:
            part_text = "Full Version"

        dur_text = f"⏱ {duration}" if duration else ""

        # ── Load fonts ─────────────────────────────
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/"
            "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/"
            "LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/"
            "FreeSansBold.ttf",
        ]

        font_large  = None
        font_medium = None
        font_small  = None

        for fp in font_paths:
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

        # ── Draw line 1 ────────────────────────────
        # Shadow
        draw.text(
            (643, 153), line1,
            font   = font_large,
            fill   = (0, 0, 0),
            anchor = "mm"
        )
        # Main
        draw.text(
            (640, 150), line1,
            font   = font_large,
            fill   = theme["text"],
            anchor = "mm"
        )

        # ── Draw line 2 ────────────────────────────
        if line2:
            # Shadow
            draw.text(
                (643, 263), line2,
                font   = font_large,
                fill   = (0, 0, 0),
                anchor = "mm"
            )
            # Main
            draw.text(
                (640, 260), line2,
                font   = font_large,
                fill   = theme["accent"],
                anchor = "mm"
            )
            text_bottom = 280
        else:
            text_bottom = 180

        # ── Draw part text ─────────────────────────
        draw.text(
            (640, text_bottom + 120),
            part_text,
            font   = font_medium,
            fill   = theme["text"],
            anchor = "mm"
        )

        # ── Draw duration ──────────────────────────
        if dur_text:
            draw.text(
                (640, text_bottom + 190),
                dur_text,
                font   = font_small,
                fill   = theme["accent"],
                anchor = "mm"
            )

        # ── Bottom branding ────────────────────────
        draw.text(
            (640, 660),
            "🌙  Sleep  •  Relax  •  Meditate  🌙",
            font   = font_small,
            fill   = theme["glow"],
            anchor = "mm"
        )

        # ── Top accent line ────────────────────────
        draw.rectangle(
            [0, 0, 1280, 8],
            fill=theme["accent"]
        )
        # Bottom accent line
        draw.rectangle(
            [0, 712, 1280, 720],
            fill=theme["accent"]
        )
