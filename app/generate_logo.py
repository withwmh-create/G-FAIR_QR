import os
import math
from PIL import Image, ImageDraw, ImageFont

def generate():
    # Create a transparent logo canvas (500x120)
    width, height = 500, 120
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Abstract geometric icon: Hexagon with network nodes
    cx, cy = 70, 60
    r = 35
    points = []
    for i in range(6):
        # Rotate by 30 deg to point up
        angle = math.radians(i * 60 - 30)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))
    
    # 1. Draw outer glowing hexagon glow
    draw.polygon(points, outline=(99, 102, 241, 100), width=6) # Indigo glow
    draw.polygon(points, outline=(139, 92, 246, 255), width=3) # Violet crisp border
    
    # 2. Draw interior network connection lines
    for i in range(6):
        # Connect to every other node to form a web
        for j in range(i + 2, i + 5):
            target = j % 6
            draw.line([points[i], points[target]], fill=(59, 130, 246, 80), width=1) # Soft blue web
            
    # 3. Draw nodes at vertices
    for p in points:
        draw.ellipse([p[0]-4, p[1]-4, p[0]+4, p[1]+4], fill=(255, 255, 255, 255), outline=(139, 92, 246, 255), width=1)
        
    # 4. Draw central core node representing secure token center
    draw.ellipse([cx-8, cy-8, cx+8, cy+8], fill=(59, 130, 246, 255), outline=(255, 255, 255, 255), width=2)
    
    # 5. Load premium system font (Segoe UI or Arial)
    try:
        # Bold Segoe UI for brand name, Regular for subtitle
        font_title = ImageFont.truetype("msvcrt.dll", 36) # fallback check, but let's try direct names
        font_title = ImageFont.truetype("Segoe UI Semibold", 34)
        font_sub = ImageFont.truetype("Segoe UI", 14)
    except Exception:
        try:
            font_title = ImageFont.truetype("arialbd.ttf", 34)
            font_sub = ImageFont.truetype("arial.ttf", 14)
        except Exception:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()
            
    # 6. Render Typography with gradient look (vibrant purple-blue vibe)
    draw.text((135, 22), "G-FAIR KOREA", fill=(255, 255, 255, 255), font=font_title)
    draw.text((375, 22), "2026", fill=(99, 102, 241, 255), font=font_title) # Indigo accent
    draw.text((137, 70), "OFFICIAL BUYER VERIFICATION SYSTEM", fill=(156, 163, 175, 255), font=font_sub)
    
    # Save the generated PNG image
    os.makedirs("static/images", exist_ok=True)
    image.save("static/images/logo.png", "PNG")
    print("Logo successfully generated and saved to static/images/logo.png")

if __name__ == "__main__":
    generate()
