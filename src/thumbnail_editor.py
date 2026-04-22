import os
import random
from PIL import Image, ImageEnhance
from src.config import THUMBNAILS_DIR

class ThumbnailEditor:
    def modify_thumbnail(self, input_path):
        if not input_path or not os.path.exists(input_path):
            return input_path

        try:
            img = Image.open(input_path).convert("RGB")
            img = ImageEnhance.Brightness(img).enhance(random.uniform(0.95, 1.08))
            img = ImageEnhance.Contrast(img).enhance(random.uniform(0.95, 1.12))
            
            output_path = os.path.join(THUMBNAILS_DIR, "thumb_modified.jpg")
            img.save(output_path, quality=random.randint(85, 95))
            return output_path
        except:
            return input_path