import os
import math
from PIL import Image, ImageDraw, ImageFont

icons_dir = os.path.join("static", "icons")
os.makedirs(icons_dir, exist_ok=True)

def create_ecoguard_icon(size, is_maskable=False):
    # Create image with RGBA
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = size / 2, size / 2
    
    # For maskable icons, keep graphics within 80% safe zone
    scale = 0.82 if is_maskable else 0.94
    radius = (size / 2) * scale
    
    # 1. Background Rounded Circle / Squircle
    # If maskable, fill whole background with solid gradient color
    if is_maskable:
        # Full background
        for y in range(size):
            # Gradient from deep emerald to vibrant teal
            ratio = y / size
            r = int(6 + (4 - 6) * ratio)
            g = int(78 + (120 - 78) * ratio)
            b = int(59 + (87 - 59) * ratio)
            draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    else:
        # Radial / vertical gradient inside a rounded circle
        for r_step in range(int(radius), 0, -1):
            ratio = 1.0 - (r_step / radius)
            r = int(6 + 10 * ratio)
            g = int(78 + 72 * ratio)
            b = int(59 + 28 * ratio)
            draw.ellipse(
                [center_x - r_step, center_y - r_step, center_x + r_step, center_y + r_step],
                fill=(r, g, b, 255)
            )
        # Subtle outer ring
        draw.ellipse(
            [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
            outline=(110, 231, 183, 180),
            width=max(2, int(size * 0.015))
        )

    # 2. Draw Protective Shield & Leaf Motif
    # Coordinate system relative to center and size
    s = size * (0.68 if is_maskable else 0.76)
    cx, cy = center_x, center_y - (size * 0.02)
    
    # Shield Outline Polygon Points
    shield_pts = [
        (cx - s * 0.38, cy - s * 0.32),
        (cx + s * 0.38, cy - s * 0.32),
        (cx + s * 0.38, cy + s * 0.05),
        (cx, cy + s * 0.44),
        (cx - s * 0.38, cy + s * 0.05),
    ]
    # Draw Shield fill (translucent emerald white)
    draw.polygon(shield_pts, fill=(255, 255, 255, 35))
    draw.line(shield_pts + [shield_pts[0]], fill=(167, 243, 208, 220), width=max(2, int(size * 0.022)))

    # 3. Draw Stylized Eco Leaf in Center
    leaf_pts = []
    steps = 40
    # Left curve of leaf
    tip_y = cy - s * 0.22
    bottom_y = cy + s * 0.28
    
    for i in range(steps + 1):
        t = i / steps
        y = tip_y + (bottom_y - tip_y) * t
        # Curve out
        x_offset = math.sin(t * math.pi) * (s * 0.32)
        leaf_pts.append((cx - x_offset, y))
    
    # Right curve of leaf
    for i in range(steps, -1, -1):
        t = i / steps
        y = tip_y + (bottom_y - tip_y) * t
        x_offset = math.sin(t * math.pi) * (s * 0.24)
        leaf_pts.append((cx + x_offset, y))
        
    draw.polygon(leaf_pts, fill=(255, 255, 255, 245))
    
    # Leaf Center Vein / Neural Branch
    vein_width = max(2, int(size * 0.02))
    draw.line([(cx, tip_y), (cx, bottom_y)], fill=(5, 150, 105, 230), width=vein_width)
    
    # Diagonal side veins
    draw.line([(cx, cy - s*0.08), (cx - s*0.16, cy - s*0.16)], fill=(5, 150, 105, 200), width=max(1, vein_width - 1))
    draw.line([(cx, cy - s*0.02), (cx + s*0.14, cy - s*0.10)], fill=(5, 150, 105, 200), width=max(1, vein_width - 1))
    draw.line([(cx, cy + s*0.08), (cx - s*0.18, cy + s*0.00)], fill=(5, 150, 105, 200), width=max(1, vein_width - 1))
    draw.line([(cx, cy + s*0.14), (cx + s*0.14, cy + s*0.06)], fill=(5, 150, 105, 200), width=max(1, vein_width - 1))

    # 4. Neural Circuit Nodes (AI Sparkles)
    node_color = (250, 204, 21, 255) # Golden yellow AI spark
    nodes = [
        (cx - s * 0.16, cy - s * 0.16),
        (cx + s * 0.14, cy - s * 0.10),
        (cx - s * 0.18, cy + s * 0.00),
        (cx + s * 0.14, cy + s * 0.06),
        (cx, tip_y)
    ]
    node_r = max(2, int(size * 0.028))
    for nx, ny in nodes:
        draw.ellipse([nx - node_r, ny - node_r, nx + node_r, ny + node_r], fill=node_color, outline=(255, 255, 255, 240), width=1)

    return img

# Generate all required icon sizes
sizes = [
    ("icon-192x192.png", 192, False),
    ("icon-192x192-maskable.png", 192, True),
    ("icon-512x512.png", 512, False),
    ("icon-512x512-maskable.png", 512, True),
    ("apple-touch-icon.png", 180, False),
    ("favicon.png", 64, False),
]

for filename, size, maskable in sizes:
    icon_img = create_ecoguard_icon(size, is_maskable=maskable)
    save_path = os.path.join(icons_dir, filename)
    icon_img.save(save_path, "PNG")
    print(f"Generated {filename} ({size}x{size}, maskable={maskable}) -> {save_path}")

print("All ECOGUARD AI icons generated successfully!")
