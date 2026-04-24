"""
Thumbnail Generator
Creates unique engaging thumbnails for each video part
Using Pillow - no external API needed
"""

import os
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

        # Color themes for different moods
        self.themes = [
            {
                "name"      : "midnight",
                "bg"        : (10,  10,  40),
                "accent"    : (100, 149, 237),
                "text"      : (255, 255, 255),
                "glow"      : (70,  130, 180),
            },
            {
                "name"      : "forest",
                "bg"        : (10,  40,  20),
                "accent"    : (50,  205, 50),
                "text"      : (255, 255, 255),
                "glow"      : (34,  139, 34),
            },
            {
                "name"      : "ocean",
                "bg"        : (0,   20,  60),
                "accent"    : (0,   191, 255),
                "text"      : (255, 255, 255),
                "glow"      : (0,   150, 200),
            },
            {
                "name"      : "purple",
                "bg"        : (30,  0,   60),
                "accent"    : (186, 85,  211),
                "text"      : (255, 255, 255),
                "glow"      : (148, 0,   211),
            },
            {
                "name"      : "sunset",
                "bg"        : (40,  10,  10),
                "accent"    : (255, 140, 0),
                "text"      : (255, 255, 255),
                "glow"      : (255, 69,  0),
            },
        ]

        # Decorative elements
        self.moon_phases = ["🌙", "🌛", "🌜", "🌚"]
        self.nature      = ["🌿", "🍃", "🌊", "⭐", "✨", "💫"]
        self.sleep_icons = ["💤", "😴", "🌙", "⭐", "🌟"]

    # ─────────────────────────────────────────────
    # Generate Thumbnail
    # ─────────────────────────────────────────────
    def generate(self, video_id, part_num=1, total_parts=1):
        """Generate unique thumbnail for each video part"""
        print(f"   🎨 Generating thumbnail for part {part_num}...")

        output_path = os.path.join(
            THUMBNAILS_DIR,
            f"{video_id}_part{part_num}_thumb.jpg"
        )

        # Pick random theme
        theme = random.choice(self.themes)

        # Create base image
        img    = Image.new("RGB", (1280, 720), theme["bg"])
        draw   = ImageDraw.Draw(img)

        # Add gradient overlay
        self._add_gradient(img, draw, theme)

        # Add background image if exists (blurred)
        self._add_blurred_bg(img, theme)

        # Add decorative circles
        self._add_circles(draw, theme)

        # Add main text
        self._add_text(draw, theme, part_num, total_parts)

        # Add stars/particles
        self._add_particles(draw, theme)

        # Final enhancement
        img = ImageEnhance.Contrast(img).enhance(1.1)
        img = ImageEnhance.Brightness(img).enhance(1.05)

        # Save
        img.save(output_path, "JPEG", quality=95)
        print(f"   ✅ Thumbnail saved: {output_path}")
        return output_path

    # ─────────────────────────────────────────────
    # Add Gradient
    # ─────────────────────────────────────────────
    def _add_gradient(self, img, draw, theme):
        """Add subtle gradient to background"""
        width, height = img.size
        for y in range(height):
            alpha = y / height
            r = int(theme["bg"][0] * (1 - alpha * 0.3))
            g = int(theme["bg"][1] * (1 - alpha * 0.3))
            b = int(theme["bg"][2] * (1 - alpha * 0.3))
            draw.line([(0, y), (width, y)], fill=(r, g, b))

    # ─────────────────────────────────────────────
    # Add Blurred Background
    # ─────────────────────────────────────────────
    def _add_blurred_bg(self, img, theme):
        """Add blurred version of background image"""
        if os.path.exists(BACKGROUND_IMAGE):
            try:
                bg = Image.open(BACKGROUND_IMAGE).convert("RGB")
                bg = bg.resize((1280, 720))
                bg = bg.filter(ImageFilter.GaussianBlur(radius=15))
                bg = ImageEnhance.Brightness(bg).enhance(0.3)
                img.paste(bg, (0, 0))
            except Exception:
                pass

    # ─────────────────────────────────────────────
    # Add Decorative Circles
    # ─────────────────────────────────────────────
    def _add_circles(self, draw, theme):
        """Add glowing circles for visual interest"""
        # Large background circle
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
        # Small accent circle
        draw.ellipse(
            [580, 260, 700, 460],
            outline = theme["accent"],
            width   = 3
        )

    # ─────────────────────────────────────────────
    # Add Text
    # ─────────────────────────────────────────────
    def _add_text(self, draw, theme, part_num, total_parts):
        """Add title and part text"""

        # Main title - Line 1
        title_line1 = "Heavy Rain"
        # Main title - Line 2
        title_line2 = "Deep Sleep"

        # Part info
        if total_parts > 1:
            part_text = f"Part {part_num} of {total_parts}"
        else:
            part_text = "Full Version"

        # Hours text
        hours_text  = f"{4 if part_num < total_parts else 'Extended'} Hours"

        try:
            # Try to load a font
            font_large  = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                90
            )
            font_medium = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                60
            )
            font_small  = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                40
            )
        except Exception:
            font_large  = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small  = ImageFont.load_default()

        # Draw text with shadow effect
        # Shadow
        draw.text(
            (642, 152),
            title_line1,
            font  = font_large,
            fill  = (0, 0, 0),
            anchor = "mm"
        )
        # Main text
        draw.text(
            (640, 150),
            title_line1,
            font   = font_large,
            fill   = theme["text"],
            anchor = "mm"
        )

        # Line 2
        draw.text(
            (642, 252),
            title_line2,
            font   = font_large,
            fill   = (0, 0, 0),
            anchor = "mm"
        )
        draw.text(
            (640, 250),
            title_line2,
            font   = font_large,
            fill   = theme["accent"],
            anchor = "mm"
        )

        # Part text
        draw.text(
            (640, 380),
            part_text,
            font   = font_medium,
            fill   = theme["text"],
            anchor = "mm"
        )

        # Hours text
        draw.text(
            (640, 460),
            hours_text,
            font   = font_small,
            fill   = theme["accent"],
            anchor = "mm"
        )

        # Bottom text
        draw.text(
            (640, 650),
            "🌙 Sleep • Relax • Meditate 🌙",
            font   = font_small,
            fill   = theme["glow"],
            anchor = "mm"
        )

    # ─────────────────────────────────────────────
    # Add Particles/Stars
    # ─────────────────────────────────────────────
    def _add_particles(self, draw, theme):
        """Add star particles for atmosphere"""
        import random
        for _ in range(50):
            x    = random.randint(0, 1280)
            y    = random.randint(0, 720)
            size = random.randint(1, 3)
            draw.ellipse(
                [x-size, y-size, x+size, y+size],
                fill = theme["text"]
            )
