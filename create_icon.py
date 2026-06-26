"""
create_icon.py - Correctly saves multi-size ICO.
Pillow ICO format: create ONE large image, pass sizes= to auto-resize.
"""
from PIL import Image, ImageDraw
import os

BLUE   = (0,   83, 226)
YELLOW = (255, 194,  32)
WHITE  = (255, 255, 255)


def make_frame(s: int) -> Image.Image:
    """Build a single RGBA icon frame at size s×s."""
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    r = max(3, s // 7)

    # Blue rounded background
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=BLUE)

    # Yellow top bar
    bar_h = max(4, s // 7)
    d.rounded_rectangle([0, 0, s - 1, bar_h + r - 1], radius=r, fill=YELLOW)
    if bar_h + r < s:
        d.rectangle([0, r, s - 1, bar_h + r - 1], fill=YELLOW)

    # Bold white W polygon
    pw  = s * 0.68
    lx  = (s - pw) / 2
    rx  = lx + pw
    top = bar_h + (s - bar_h) * 0.08
    bot = s * 0.83
    mid = top + (bot - top) * 0.52

    pts = [
        (lx,            top),
        (lx + pw*0.23,  bot),
        (lx + pw*0.38,  mid),
        (s / 2,         bot * 0.95),
        (lx + pw*0.62,  mid),
        (rx - pw*0.23,  bot),
        (rx,            top),
        (rx - pw*0.13,  top),
        (lx + pw*0.62,  mid - s*0.02),
        (s / 2,         bot * 0.87),
        (lx + pw*0.38,  mid - s*0.02),
        (lx + pw*0.13,  top),
    ]
    d.polygon(pts, fill=WHITE)

    # Yellow road dashes (48px+)
    if s >= 48:
        ry = int(s * 0.90)
        lw = max(1, s // 30)
        dl = max(2, s // 18)
        for xc in [int(s * 0.28), int(s * 0.50), int(s * 0.72)]:
            d.line([(xc - dl, ry), (xc + dl, ry)], fill=YELLOW, width=lw)

    return img


# Create the base image at 256×256
base = make_frame(256)

out = (
    r"C:\Users\V0M06TT\OneDrive - Walmart Inc\Shared Documents - CareOps_Centralized_Report"
    r"\999. GCP\28.Transportation_Roster_Project\transport_roster.ico"
)

# Pillow ICO: pass sizes= list, it auto-resamples from the base image
base.save(
    out,
    format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)

sz = os.path.getsize(out)
print(f"Saved: {out}")
print(f"Size:  {sz:,} bytes  ({sz//1024} KB)")

# Quick validation
with open(out, "rb") as f:
    hdr = f.read(6)
n_images = int.from_bytes(hdr[4:6], "little")
print(f"ICO images in file: {n_images}")
