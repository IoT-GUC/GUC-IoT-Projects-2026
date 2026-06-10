from PIL import Image, ImageDraw
from pathlib import Path

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
BASE = Path(r"FOMO+CNN\sd_pulls")
OUT_DIR = BASE / "final_crops"
OUT_DIR.mkdir(exist_ok=True)

FOMO_INPUT_W = 96
FOMO_INPUT_H = 96


def read_fomo_box(coord_txt_path):
    coords = Path(coord_txt_path).read_text().strip()
    x, y, w, h = map(int, coords.split(","))
    return x, y, w, h


def fomo_center_to_full_image(fomo_box, full_w, full_h):
    x, y, w, h = fomo_box

    scale_x = full_w / FOMO_INPUT_W
    scale_y = full_h / FOMO_INPUT_H

    cx = int((x + w / 2) * scale_x)
    cy = int((y + h / 2) * scale_y)

    return cx, cy


def clamp_box(x1, y1, x2, y2, W, H):
    x1 = max(0, min(x1, W - 1))
    y1 = max(0, min(y1, H - 1))
    x2 = max(1, min(x2, W))
    y2 = max(1, min(y2, H))

    if x2 <= x1:
        x2 = min(W, x1 + 1)

    if y2 <= y1:
        y2 = min(H, y1 + 1)

    return x1, y1, x2, y2


def generic_lcd_crop(full_img_path, coord_txt_path, output_path, debug_path=None):
    img = Image.open(full_img_path).convert("RGB")
    W, H = img.size

    fomo_box = read_fomo_box(coord_txt_path)
    cx, cy = fomo_center_to_full_image(fomo_box, W, H)

    # --------------------------------------------------------
    # Generic safe crop
    # --------------------------------------------------------
    # Wide enough to keep all digits, including leading zeros.
    CROP_W = int(W * 0.55)

    # Tall enough to include the LCD digit band,
    # but not too tall to include too many buttons/text.
    CROP_H = int(H * 0.18)

    # FOMO often points near the left/top of the LCD,
    # so shift slightly right and slightly down.
    SHIFT_X = int(W * 0.07)
    SHIFT_Y = int(H * 0.01)

    center_x = cx + SHIFT_X
    center_y = cy + SHIFT_Y

    x1 = center_x - CROP_W // 2
    y1 = center_y - CROP_H // 2
    x2 = x1 + CROP_W
    y2 = y1 + CROP_H

    x1, y1, x2, y2 = clamp_box(x1, y1, x2, y2, W, H)

    crop = img.crop((x1, y1, x2, y2))
    crop.save(output_path)

    print(f"Image: {Path(full_img_path).name}")
    print(f"FOMO box: {fomo_box}")
    print(f"FOMO center full image: cx={cx}, cy={cy}")
    print(f"Crop: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
    print(f"Saved: {output_path}")

    if debug_path is not None:
        debug = img.copy()
        draw = ImageDraw.Draw(debug)

        # Draw FOMO centroid
        r = 5
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline="blue", width=3)
        draw.text((cx + 6, cy + 6), "FOMO center", fill="blue")

        # Draw final crop
        draw.rectangle((x1, y1, x2, y2), outline="red", width=3)
        draw.text((x1 + 5, y1 + 5), "generic LCD crop", fill="red")

        debug.save(debug_path)
        print(f"Saved debug: {debug_path}")

    return crop


# ------------------------------------------------------------
# RUN ON ALL AVAILABLE CAPTURES
# ------------------------------------------------------------
for idx in range(1, 28):
    full_img = BASE / f"full_{idx:04d}.jpg"
    coord_txt = BASE / f"crop_{idx:04d}.txt"

    if full_img.exists() and coord_txt.exists():
        generic_lcd_crop(
            full_img_path=full_img,
            coord_txt_path=coord_txt,
            output_path=OUT_DIR / f"lcd_crop_{idx:04d}.jpg",
            debug_path=OUT_DIR / f"debug_lcd_crop_{idx:04d}.jpg"
        )