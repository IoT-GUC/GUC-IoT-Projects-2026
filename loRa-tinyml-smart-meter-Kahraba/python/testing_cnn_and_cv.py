import cv2
import numpy as np
import tensorflow as tf
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
MODEL_PATH = r"FOMO+CNN\digit_cnn\digit_cnn_int8.tflite"
IMAGE_PATH = r"FOMO+CNN\sd_pulls\final_crops\previous\22-6&7\lcd_crop_0010.jpg"

CLASS_NAMES = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "dot"]

# Image normalization height used before segmentation.
TARGET_H = 64

# Important: the CNN still expects 28x28.
# These are the SOURCE digit windows before they are centered and resized to 28x28.
PATCH_SOURCE_WIDTHS = [16, 18, 20]
PATCH_SOURCE_HEIGHT = 35

# If projection misses/splits badly, try fixed-slot fallback.
# Put the likely number of digits here. Use [4, 5] if unsure.
EXPECTED_DIGITS_OPTIONS = [6, 7, 8]
USE_FIXED_SLOT_FALLBACK = True
# Fixed-slot fallback is dangerous when the LCD crop has large empty/border areas.
# Use it only when projection clearly fails, not just because confidence is high.
FIXED_FALLBACK_ONLY_IF_PROJECTION_BAD = True
PROJECTION_GOOD_MIN_BOXES = 4
PROJECTION_GOOD_MIN_CONF = 0.65
MAX_REASONABLE_BOX_W = 32

# Meter digits should be one compact group. Big gaps usually mean LCD border/text artifact.
ENABLE_BIG_GAP_CUT = True
BIG_GAP_ABS = 32          # after resizing to TARGET_H=64; gaps bigger than this are almost always noise
BIG_GAP_MEDIAN_MULT = 3.0 # also cut if gap is much bigger than normal digit spacing

# If you know the number of meter digits, put it here, e.g. [7].
# If not sure, leave it empty and the script will only use gap/artifact filtering.
PREFERRED_READING_LENGTHS = []

# ------------------------------------------------------------
# Artifact rejection before CNN
# ------------------------------------------------------------
# The CNN has no background/reject class, so high confidence on garbage is expected.
# These rules decide whether a projection box is allowed to reach the CNN.
ENABLE_PRE_CNN_BOX_VALIDATION = True

# Boxes touching the LCD crop edge are usually screen borders, not digits.
# A real leading zero in your crops usually starts after this margin; keep this small.
EDGE_REJECT_MARGIN = 6

# Geometry after resizing LCD crop to TARGET_H=64.
MIN_REAL_DIGIT_H_RATIO = 0.32
MIN_INK_AREA = 18
MIN_BOX_W = 4
MAX_BOX_W = 34

# Remove isolated side artifacts by keeping the main compact digit group.
ENABLE_MAIN_GROUP_FILTER = True
MAIN_GROUP_MIN_BOXES = 3
GROUP_GAP_ABS = 24
GROUP_GAP_WIDTH_MULT = 1.8

# If a box is isolated at the far left/right and the rest contains a good group, drop it.
DROP_ISOLATED_EDGE_BOXES = True

# Extra cleanup for the exact failure cases we saw:
# 1) isolated LCD-border boxes before/after the real digit group
# 2) tiny projection fragments inside one digit
ENABLE_ISOLATED_SIDE_DROP = True
ISOLATED_SIDE_GAP_ABS = 22
ISOLATED_SIDE_GAP_MEDIAN_MULT = 1.8

ENABLE_FRAGMENT_MERGE = True
FRAGMENT_MAX_W = 8
FRAGMENT_MERGE_GAP = 5
FRAGMENT_MERGED_MAX_W = 34

# Debug control
DEBUG = True
DEBUG_ROOT = Path("debug_runs")
SAVE_PATCH_DEBUG = False       # per-digit slot/binary/canvas/patch images
SAVE_ONLY_SUMMARY = True       # set True when debug folders become too large

# ============================================================
# DEBUG WRITER
# ============================================================
class DebugWriter:
    def __init__(self, image_path, enabled=True):
        self.enabled = enabled
        if enabled:
            stem = Path(image_path).stem
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.dir = DEBUG_ROOT / f"{stem}_{ts}"
            self.dir.mkdir(parents=True, exist_ok=True)
        else:
            self.dir = None

    def save(self, name, img):
        if not self.enabled:
            return
        cv2.imwrite(str(self.dir / name), img)

    def path(self, name):
        if not self.enabled:
            return None
        return str(self.dir / name)

# ============================================================
# MODEL
# ============================================================
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()[0]
output_details = interpreter.get_output_details()[0]

print("Model input:", input_details["shape"], input_details["dtype"], input_details.get("quantization"))
print("Model output:", output_details["shape"], output_details["dtype"], output_details.get("quantization"))


def run_cnn(patch_28):
    """patch_28: 28x28 uint8, white digit on black background."""
    input_shape = input_details["shape"]
    input_dtype = input_details["dtype"]

    arr = patch_28.reshape(input_shape)

    if input_dtype == np.float32:
        # Keep old behavior unless you know the model was trained on 0..1.
        arr = arr.astype(np.float32)
    elif input_dtype == np.uint8:
        arr = arr.astype(np.uint8)
    elif input_dtype == np.int8:
        scale, zero_point = input_details["quantization"]
        arr = arr.astype(np.float32)
        if scale and scale > 0:
            arr = arr / scale + zero_point
        arr = np.clip(arr, -128, 127).astype(np.int8)
    else:
        raise TypeError(f"Unsupported input dtype: {input_dtype}")

    interpreter.set_tensor(input_details["index"], arr)
    interpreter.invoke()

    scores = interpreter.get_tensor(output_details["index"])[0]

    if output_details["dtype"] in [np.uint8, np.int8]:
        scale, zero_point = output_details["quantization"]
        if scale and scale > 0:
            scores = scale * (scores.astype(np.float32) - zero_point)

    label = CLASS_NAMES[int(np.argmax(scores))]
    confidence = float(np.max(scores))
    return label, confidence, scores

# ============================================================
# PREPROCESSING
# ============================================================
def balance_lcd_image(gray):
    gray = gray.astype(np.uint8)
    bg = cv2.GaussianBlur(gray, (0, 0), sigmaX=15, sigmaY=15)
    bg = np.maximum(bg, 1)
    balanced = cv2.divide(gray, bg, scale=128)
    return cv2.normalize(balanced, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)


def apply_clahe(gray):
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(4, 4))
    return clahe.apply(gray)


def clean_for_segmentation(enhanced):
    blur = cv2.GaussianBlur(enhanced, (3, 3), 0)
    binary = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        21, 5
    )

    binary[:3, :] = 0
    binary[-3:, :] = 0
    binary[:, :3] = 0
    binary[:, -3:] = 0

    h, w = binary.shape

    # Remove long horizontal bands.
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(15, w // 3), 1))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
    binary = cv2.subtract(binary, horizontal_lines)

    row_sum = np.sum(binary > 0, axis=1)
    for y in range(h):
        if row_sum[y] > 0.45 * w:
            binary[y, :] = 0

    open_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, open_kernel, iterations=1)

    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, close_kernel, iterations=1)
    return binary

# ============================================================
# SEGMENTATION
# ============================================================
def projection_digit_boxes(binary, target_h, dbg=None):
    h, w = binary.shape
    y1 = int(target_h * 0.10)
    y2 = int(target_h * 0.90)
    roi = binary[y1:y2, :]
    col_sum = np.sum(roi > 0, axis=0)

    if col_sum.max() == 0:
        return []

    smooth = np.convolve(col_sum, np.ones(5) / 5, mode="same")
    threshold = max(1, int(0.12 * smooth.max()))
    active = smooth > threshold

    raw = []
    in_box = False
    start = 0
    for x, val in enumerate(active):
        if val and not in_box:
            start = x
            in_box = True
        elif not val and in_box:
            end = x
            if end - start >= 3:
                raw.append((start, 0, end - start, target_h))
            in_box = False
    if in_box:
        end = len(active)
        if end - start >= 3:
            raw.append((start, 0, end - start, target_h))

    # Merge tiny gaps only.
    merged = []
    for x, y, bw, bh in raw:
        if not merged:
            merged.append([x, y, bw, bh])
            continue
        px, py, pw, ph = merged[-1]
        gap = x - (px + pw)
        if gap <= 2:
            new_x2 = max(px + pw, x + bw)
            merged[-1] = [px, 0, new_x2 - px, target_h]
        else:
            merged.append([x, y, bw, bh])

    # Remove obvious noise and split very wide boxes.
    cleaned = []
    for x, y, bw, bh in merged:
        crop = binary[:, x:x + bw]
        ys, xs = np.where(crop > 0)
        if len(xs) == 0:
            continue
        real_h = ys.max() - ys.min() + 1
        area = len(xs)
        if real_h < target_h * 0.30 or area < 18:
            continue
        cleaned.append((x, 0, bw, target_h))

    widths = [bw for _, _, bw, _ in cleaned if 4 <= bw <= 32]
    estimated_w = int(np.median(widths)) if widths else 16

    final = []
    for x, y, bw, bh in cleaned:
        if bw <= estimated_w * 1.65:
            final.append((x, y, bw, bh))
        else:
            n = int(round(bw / estimated_w))
            n = max(2, min(6, n))
            part_w = bw / n
            for i in range(n):
                sx = int(round(x + i * part_w))
                ex = int(round(x + (i + 1) * part_w))
                if ex - sx >= 3:
                    final.append((sx, 0, ex - sx, target_h))

    final = sorted(final, key=lambda b: b[0])

    if dbg and dbg.enabled:
        profile_img = np.zeros((100, w), dtype=np.uint8)
        norm = smooth.astype(np.float32)
        if norm.max() > 0:
            norm /= norm.max()
        for xx in range(w):
            ph = int(norm[xx] * 90)
            cv2.line(profile_img, (xx, 99), (xx, 99 - ph), 255, 1)
        for x, y, bw, bh in final:
            cv2.line(profile_img, (x, 0), (x, 99), 150, 1)
            cv2.line(profile_img, (x + bw, 0), (x + bw, 99), 150, 1)
        dbg.save("05_projection_profile.png", profile_img)

    return final


def fixed_slot_boxes_from_activity(binary, target_h, expected_digits):
    """
    Fallback: find the main compact active digit span and split it into N equal slots.
    This is intentionally conservative. It should NOT use the whole LCD width,
    because screen borders and empty areas make huge wrong slots.
    """
    h, w = binary.shape
    roi = binary[int(0.12 * target_h):int(0.88 * target_h), :]
    col_sum = np.sum(roi > 0, axis=0)
    if col_sum.max() == 0:
        return []

    # Smooth and find active runs.
    smooth = np.convolve(col_sum, np.ones(5) / 5, mode="same")
    active = smooth > max(1, int(0.10 * smooth.max()))

    runs = []
    in_run = False
    st = 0
    for i, v in enumerate(active):
        if v and not in_run:
            st = i
            in_run = True
        elif not v and in_run:
            if i - st >= 3:
                runs.append((st, i))
            in_run = False
    if in_run and len(active) - st >= 3:
        runs.append((st, len(active)))

    if not runs:
        return []

    # Merge runs into groups, but break at huge gaps. Keep the group with most runs.
    groups = []
    cur = [runs[0]]
    for r in runs[1:]:
        gap = r[0] - cur[-1][1]
        # Digit-to-digit gaps are usually small. Borders are usually far away.
        if gap > BIG_GAP_ABS:
            groups.append(cur)
            cur = [r]
        else:
            cur.append(r)
    groups.append(cur)

    def score_group(g):
        span = g[-1][1] - g[0][0]
        return (len(g), -span)  # most active runs, then more compact

    group = max(groups, key=score_group)
    x1 = max(0, group[0][0] - 2)
    x2 = min(w, group[-1][1] + 3)
    span = x2 - x1

    # Reject if slots would be ridiculously wide for TARGET_H=64.
    slot_w = span / max(1, expected_digits)
    if slot_w > MAX_REASONABLE_BOX_W:
        return []

    boxes = []
    for i in range(expected_digits):
        sx = int(round(x1 + i * span / expected_digits))
        ex = int(round(x1 + (i + 1) * span / expected_digits))
        boxes.append((sx, 0, max(3, ex - sx), target_h))
    return boxes


def remove_far_gap_artifacts(boxes):
    """
    Remove boxes separated from the main digit row by a very large gap.
    This specifically removes LCD borders / side labels that projection may treat as digits.
    """
    boxes = sorted(boxes, key=lambda b: b[0])
    if not ENABLE_BIG_GAP_CUT or len(boxes) <= 2:
        return boxes

    gaps = []
    for i in range(len(boxes) - 1):
        x, y, w, h = boxes[i]
        nx, ny, nw, nh = boxes[i + 1]
        gaps.append(nx - (x + w))

    positive_gaps = [g for g in gaps if g > 0]
    if not positive_gaps:
        return boxes

    median_gap = float(np.median(positive_gaps))
    cut_threshold = max(BIG_GAP_ABS, median_gap * BIG_GAP_MEDIAN_MULT)

    # Split into groups at huge gaps.
    groups = []
    current = [boxes[0]]
    for i, gap in enumerate(gaps):
        if gap > cut_threshold:
            groups.append(current)
            current = [boxes[i + 1]]
        else:
            current.append(boxes[i + 1])
    groups.append(current)

    # Keep the group with the most boxes. If tied, keep the leftmost wider group.
    def group_score(g):
        span = (g[-1][0] + g[-1][2]) - g[0][0]
        return (len(g), span)

    best_group = max(groups, key=group_score)
    return best_group


def trim_boxes_to_preferred_length(boxes):
    """
    Optional: if the meter length is known, remove low-confidence-like side artifacts before classification.
    Since confidence is not available here, trim by keeping the most compact central/left digit group.
    """
    boxes = sorted(boxes, key=lambda b: b[0])
    if not PREFERRED_READING_LENGTHS or not boxes:
        return boxes

    target = min(PREFERRED_READING_LENGTHS, key=lambda n: abs(n - len(boxes)))
    if len(boxes) <= target:
        return boxes

    # Prefer removing isolated boxes on the far right/left. For meter crops, right border noise is common.
    while len(boxes) > target:
        if len(boxes) <= 1:
            break
        left_gap = boxes[1][0] - (boxes[0][0] + boxes[0][2])
        right_gap = boxes[-1][0] - (boxes[-2][0] + boxes[-2][2])
        if right_gap >= left_gap:
            boxes = boxes[:-1]
        else:
            boxes = boxes[1:]
    return boxes


def box_ink_stats(binary, box):
    """Return useful measurements for deciding if a box is actually digit-like."""
    x, y, w, h = box
    crop = binary[:, max(0, x):min(binary.shape[1], x + w)]
    ys, xs = np.where(crop > 0)

    if len(xs) == 0:
        return {
            "real_h": 0,
            "real_w": 0,
            "area": 0,
            "density": 0.0,
            "cy": 0.0,
        }

    real_h = int(ys.max() - ys.min() + 1)
    real_w = int(xs.max() - xs.min() + 1)
    area = int(len(xs))
    density = float(area / max(1, real_h * real_w))
    cy = float((ys.min() + ys.max()) / 2.0)

    return {
        "real_h": real_h,
        "real_w": real_w,
        "area": area,
        "density": density,
        "cy": cy,
    }


def validate_box_before_cnn(binary, box):
    """
    Decide if a projection box is allowed to go into the CNN.

    Important: CNN confidence is NOT used here, because the CNN has no
    background/reject class and can be overconfident on borders/noise.
    """
    if not ENABLE_PRE_CNN_BOX_VALIDATION:
        return True, "ok"

    h, img_w = binary.shape
    x, y, w, bh = box
    stats = box_ink_stats(binary, box)

    # Hard reject boxes touching the LCD crop edge. These are usually vertical borders.
    # Keep margin small so true leading zeros are not removed.
    if x <= EDGE_REJECT_MARGIN:
        return False, "touch_left_edge"
    if x + w >= img_w - EDGE_REJECT_MARGIN:
        return False, "touch_right_edge"

    if w < MIN_BOX_W:
        return False, "too_narrow"
    if w > MAX_BOX_W:
        return False, "too_wide"

    if stats["area"] < MIN_INK_AREA:
        return False, "low_area"

    if stats["real_h"] < TARGET_H * MIN_REAL_DIGIT_H_RATIO:
        return False, "short_ink"

    # Reject blobs mostly stuck at top/bottom, but keep this loose for seven-segment digits.
    if stats["cy"] < TARGET_H * 0.15 or stats["cy"] > TARGET_H * 0.92:
        return False, "bad_vertical_position"

    return True, "ok"


def filter_boxes_before_cnn(binary, boxes):
    """Apply non-CNN rejection rules and return kept boxes + rejected diagnostics."""
    kept = []
    rejected = []

    for box in sorted(boxes, key=lambda b: b[0]):
        ok, reason = validate_box_before_cnn(binary, box)
        if ok:
            kept.append(box)
        else:
            rejected.append({"box": box, "reason": reason})

    return kept, rejected


def split_boxes_into_gap_groups(boxes):
    """Split boxes into groups when a huge horizontal gap appears."""
    boxes = sorted(boxes, key=lambda b: b[0])
    if len(boxes) <= 1:
        return [boxes] if boxes else []

    widths = [b[2] for b in boxes]
    med_w = float(np.median(widths)) if widths else 16.0
    gap_thr = max(GROUP_GAP_ABS, med_w * GROUP_GAP_WIDTH_MULT)

    groups = []
    cur = [boxes[0]]

    for i in range(len(boxes) - 1):
        x, y, w, h = boxes[i]
        nx, ny, nw, nh = boxes[i + 1]
        gap = nx - (x + w)

        if gap > gap_thr:
            groups.append(cur)
            cur = [boxes[i + 1]]
        else:
            cur.append(boxes[i + 1])

    groups.append(cur)
    return groups


def group_ink_area(binary, group):
    total = 0
    for box in group:
        total += box_ink_stats(binary, box)["area"]
    return total


def keep_main_digit_group(binary, boxes):
    """
    Keep the main compact row of digits and remove isolated side/border artifacts.

    This is the key fix for cases where the CNN confidently classifies LCD borders
    as '1' or '5'.
    """
    if not ENABLE_MAIN_GROUP_FILTER or len(boxes) <= 2:
        return boxes, []

    groups = split_boxes_into_gap_groups(boxes)
    if len(groups) <= 1:
        return boxes, []

    # Prefer groups with enough boxes. If none has enough boxes, do not destroy the result.
    valid_groups = [g for g in groups if len(g) >= MAIN_GROUP_MIN_BOXES]
    if not valid_groups:
        return boxes, []

    def score_group(g):
        span = (g[-1][0] + g[-1][2]) - g[0][0]
        area = group_ink_area(binary, g)
        # Most boxes is strongest, then ink area, then compactness.
        return (len(g), area, -span)

    main = max(valid_groups, key=score_group)
    main_set = set(main)

    rejected = []
    for b in boxes:
        if b not in main_set:
            rejected.append({"box": b, "reason": "not_main_digit_group"})

    return sorted(main, key=lambda b: b[0]), rejected



def drop_isolated_side_boxes(boxes):
    """
    Remove isolated boxes at the left/right side of the digit row.

    This is aimed at LCD screen borders that projection detects as tall narrow digits.
    We do NOT use CNN confidence here, because the CNN can be overconfident on borders.
    """
    boxes = sorted(boxes, key=lambda b: b[0])
    rejected = []

    if not ENABLE_ISOLATED_SIDE_DROP or len(boxes) <= 2:
        return boxes, rejected

    def gaps_of(bs):
        return [bs[i + 1][0] - (bs[i][0] + bs[i][2]) for i in range(len(bs) - 1)]

    changed = True
    while changed and len(boxes) > 2:
        changed = False
        gaps = gaps_of(boxes)
        pos_gaps = [g for g in gaps if g > 0]
        if not pos_gaps:
            break

        # Use inner gaps as the normal spacing estimate when possible.
        inner = pos_gaps[1:-1] if len(pos_gaps) > 2 else pos_gaps
        med_gap = float(np.median(inner)) if inner else float(np.median(pos_gaps))
        thr = max(ISOLATED_SIDE_GAP_ABS, med_gap * ISOLATED_SIDE_GAP_MEDIAN_MULT)

        # Left isolated box: huge gap after first box.
        if len(gaps) > 0 and gaps[0] > thr:
            rejected.append({"box": boxes[0], "reason": "isolated_left_gap"})
            boxes = boxes[1:]
            changed = True
            continue

        # Right isolated box: huge gap before last box.
        if len(gaps) > 0 and gaps[-1] > thr:
            rejected.append({"box": boxes[-1], "reason": "isolated_right_gap"})
            boxes = boxes[:-1]
            changed = True
            continue

    return boxes, rejected


def merge_small_fragments(boxes):
    """
    Merge tiny projection fragments into a neighboring digit box.

    This targets cases where one digit is split into two vertical pieces.
    It avoids merging normal neighboring digits by requiring one side to be narrow
    and the gap to be very small.
    """
    boxes = sorted(boxes, key=lambda b: b[0])
    rejected = []

    if not ENABLE_FRAGMENT_MERGE or len(boxes) <= 1:
        return boxes, rejected

    changed = True
    while changed:
        changed = False
        if len(boxes) <= 1:
            break

        best_i = None
        best_gap = None

        for i in range(len(boxes) - 1):
            x, y, w, h = boxes[i]
            nx, ny, nw, nh = boxes[i + 1]
            gap = nx - (x + w)

            if gap < 0 or gap > FRAGMENT_MERGE_GAP:
                continue

            one_is_fragment = (w <= FRAGMENT_MAX_W or nw <= FRAGMENT_MAX_W)
            merged_w = max(x + w, nx + nw) - min(x, nx)

            if one_is_fragment and merged_w <= FRAGMENT_MERGED_MAX_W:
                if best_gap is None or gap < best_gap:
                    best_i = i
                    best_gap = gap

        if best_i is not None:
            i = best_i
            x, y, w, h = boxes[i]
            nx, ny, nw, nh = boxes[i + 1]
            x1 = min(x, nx)
            x2 = max(x + w, nx + nw)
            merged = (x1, 0, x2 - x1, h)
            rejected.append({"box": boxes[i], "reason": "merged_fragment_part"})
            rejected.append({"box": boxes[i + 1], "reason": "merged_fragment_part"})
            boxes = boxes[:i] + [merged] + boxes[i + 2:]
            changed = True

    return boxes, rejected

def refine_digit_boxes(boxes, binary=None):
    """
    Full pre-CNN refinement:
    1. remove obvious edge/noise/too-wide boxes,
    2. keep the main compact digit group,
    3. optional known-length trim.
    """
    boxes = sorted(boxes, key=lambda b: b[0])
    rejected = []

    # Old big-gap cut is still useful, but now it is not the only protection.
    boxes = remove_far_gap_artifacts(boxes)

    # New: drop isolated LCD-border boxes using only geometry/gaps.
    boxes, rej0 = drop_isolated_side_boxes(boxes)
    rejected.extend(rej0)

    # New: merge tiny split fragments before validation/classification.
    boxes, rej_frag = merge_small_fragments(boxes)
    rejected.extend(rej_frag)

    if binary is not None:
        boxes, rej1 = filter_boxes_before_cnn(binary, boxes)
        rejected.extend(rej1)

        boxes, rej2 = keep_main_digit_group(binary, boxes)
        rejected.extend(rej2)

    boxes = trim_boxes_to_preferred_length(boxes)
    return sorted(boxes, key=lambda b: b[0]), rejected


def candidate_score(reading, avg_conf, boxes):
    """
    Score candidate readings. Confidence matters, but extra/missing boxes should be penalized.
    """
    score = avg_conf

    if '?' in reading or 'dot' in reading:
        score -= 0.25

    if PREFERRED_READING_LENGTHS:
        best_len_dist = min(abs(len(reading) - n) for n in PREFERRED_READING_LENGTHS)
        score -= 0.08 * best_len_dist

    # Penalize suspicious huge gaps inside the chosen boxes.
    if len(boxes) > 1:
        gaps = [boxes[i+1][0] - (boxes[i][0] + boxes[i][2]) for i in range(len(boxes)-1)]
        pos = [g for g in gaps if g > 0]
        if pos:
            med = np.median(pos)
            huge = [g for g in pos if g > max(BIG_GAP_ABS, med * BIG_GAP_MEDIAN_MULT)]
            score -= 0.15 * len(huge)

    # Penalize source boxes that are far too wide for a single digit.
    # This prevents fixed-slot fallback from winning just because the CNN is overconfident.
    if boxes:
        widths = [b[2] for b in boxes]
        too_wide = [bw for bw in widths if bw > MAX_REASONABLE_BOX_W]
        score -= 0.10 * len(too_wide)
        if len(widths) > 0 and float(np.mean(widths)) > MAX_REASONABLE_BOX_W:
            score -= 0.25

    return score

# ============================================================
# PATCH CREATION
# ============================================================
def make_patch_fixed_source(gray_for_patch, box, target_h, source_w, source_h, dbg=None, debug_prefix=None):
    """
    Crop a narrow source window like 18x35 around the digit center, then create the 28x28 CNN input.
    This solves the problem where a wide projection box includes parts of two digits.
    """
    x, y, w, h = box
    img_h, img_w = gray_for_patch.shape

    cx = int(round(x + w / 2))

    # Use active ink within the box to estimate vertical center; otherwise use screen center.
    y_top = int(target_h * 0.12)
    y_bot = int(target_h * 0.88)
    cy = (y_top + y_bot) // 2

    x1 = max(0, cx - source_w // 2)
    x2 = min(img_w, x1 + source_w)
    x1 = max(0, x2 - source_w)

    y1 = max(0, cy - source_h // 2)
    y2 = min(img_h, y1 + source_h)
    y1 = max(0, y2 - source_h)

    slot = gray_for_patch[y1:y2, x1:x2]
    if slot.size == 0:
        return None, None

    slot_norm = cv2.normalize(slot, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    inv = 255 - slot_norm
    inv = cv2.GaussianBlur(inv, (3, 3), 0)

    _, bin_img = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Prevent Otsu from selecting the whole noisy window too tightly.
    ys, xs = np.where(bin_img > 0)
    if len(xs) > 0:
        bx1, bx2 = xs.min(), xs.max()
        by1, by2 = ys.min(), ys.max()
        selected_w = bx2 - bx1 + 1
        selected_h = by2 - by1 + 1
        if selected_w < bin_img.shape[1] * 0.92 and selected_h < bin_img.shape[0] * 0.92:
            pad = 2
            bx1 = max(0, bx1 - pad)
            bx2 = min(bin_img.shape[1] - 1, bx2 + pad)
            by1 = max(0, by1 - pad)
            by2 = min(bin_img.shape[0] - 1, by2 + pad)
            digit = bin_img[by1:by2 + 1, bx1:bx2 + 1]
        else:
            digit = bin_img
    else:
        digit = bin_img

    ph, pw = digit.shape
    size = max(ph, pw) + 10
    canvas = np.zeros((size, size), dtype=np.uint8)
    yoff = (size - ph) // 2
    xoff = (size - pw) // 2
    canvas[yoff:yoff + ph, xoff:xoff + pw] = digit
    patch_28 = cv2.resize(canvas, (28, 28), interpolation=cv2.INTER_AREA)

    if dbg and dbg.enabled and debug_prefix and SAVE_PATCH_DEBUG and not SAVE_ONLY_SUMMARY:
        dbg.save(f"{debug_prefix}_w{source_w}_01_slot.png", slot)
        dbg.save(f"{debug_prefix}_w{source_w}_02_inv.png", inv)
        dbg.save(f"{debug_prefix}_w{source_w}_03_binary.png", bin_img)
        dbg.save(f"{debug_prefix}_w{source_w}_04_canvas.png", canvas)
        dbg.save(f"{debug_prefix}_w{source_w}_05_patch28.png", patch_28)

    return patch_28, canvas


def classify_box_with_width_sweep(gray_for_patch, box, target_h, dbg=None, idx=0):
    candidates = []
    for sw in PATCH_SOURCE_WIDTHS:
        patch_28, _ = make_patch_fixed_source(
            gray_for_patch, box, target_h,
            source_w=sw,
            source_h=PATCH_SOURCE_HEIGHT,
            dbg=dbg,
            debug_prefix=f"digit_{idx:02d}"
        )
        if patch_28 is None:
            continue
        label, conf, scores = run_cnn(patch_28)
        candidates.append((label, conf, sw, patch_28, scores))

    if not candidates:
        return "?", 0.0, None, None

    # Prefer non-dot labels for digit boxes unless dot is extremely dominant.
    non_dot = [c for c in candidates if c[0] != "dot"]
    chosen = max(non_dot if non_dot else candidates, key=lambda c: c[1])
    return chosen[0], chosen[1], chosen[2], chosen[3]

# ============================================================
# MAIN PIPELINE
# ============================================================
def draw_boxes(gray, boxes, title_text=None):
    out = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    for i, (x, y, w, h) in enumerate(boxes):
        cv2.rectangle(out, (x, 0), (x + w, gray.shape[0] - 1), (0, 0, 255), 1)
        cv2.putText(out, str(i), (x, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    if title_text:
        cv2.putText(out, title_text, (5, gray.shape[0] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
    return out


def draw_rejected_boxes(gray, kept_boxes, rejected_boxes):
    """Green = kept, Red = rejected. Reason text is printed near each rejected box."""
    out = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    for i, (x, y, w, h) in enumerate(kept_boxes):
        cv2.rectangle(out, (x, 0), (x + w, gray.shape[0] - 1), (0, 255, 0), 1)
        cv2.putText(out, f"K{i}", (x, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)

    for r in rejected_boxes:
        x, y, w, h = r["box"]
        reason = r["reason"]
        cv2.rectangle(out, (x, 0), (x + w, gray.shape[0] - 1), (0, 0, 255), 1)
        cv2.putText(out, reason[:10], (x, gray.shape[0] - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.28, (0, 0, 255), 1)

    cv2.putText(out, "green=kept red=rejected", (5, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
    return out


def read_with_boxes(gray_for_patch, boxes, target_h, dbg=None, label="projection"):
    results = []
    reading = ""
    confs = []

    print(f"\n--- Classifying using {label} boxes: {len(boxes)} boxes ---")
    for i, box in enumerate(boxes):
        x, y, w, h = box
        pred, conf, used_w, patch = classify_box_with_width_sweep(gray_for_patch, box, target_h, dbg=dbg, idx=i)
        print(f"Digit {i}: box x={x:3d} w={w:3d} src_w={used_w} -> {pred} ({conf*100:.1f}%)")
        if pred == "dot":
            pred = "?"
        reading += pred
        confs.append(conf)
        results.append({"label": pred, "confidence": conf, "box": box, "used_source_w": used_w})

    avg_conf = float(np.mean(confs)) if confs else 0.0
    return reading, avg_conf, results


def segment_and_read(image_path, debug=False):
    dbg = DebugWriter(image_path, enabled=debug)

    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    gray_original = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    scale = TARGET_H / gray_original.shape[0]
    new_w = int(gray_original.shape[1] * scale)
    gray = cv2.resize(gray_original, (new_w, TARGET_H), interpolation=cv2.INTER_AREA)

    balanced = balance_lcd_image(gray)
    clahe_img = apply_clahe(balanced)
    binary = clean_for_segmentation(clahe_img)

    if debug:
        dbg.save("01_gray.png", gray)
        dbg.save("02_balanced.png", balanced)
        dbg.save("03_clahe.png", clahe_img)
        dbg.save("04_binary_clean.png", binary)

    boxes_raw = projection_digit_boxes(binary, TARGET_H, dbg=dbg)
    boxes, rejected_boxes = refine_digit_boxes(boxes_raw, binary=binary)
    if debug:
        dbg.save("06a_boxes_projection_raw_gray.png", draw_boxes(gray, boxes_raw, "projection raw"))
        dbg.save("06_boxes_projection_gray.png", draw_boxes(gray, boxes, "projection filtered"))
        dbg.save("07_boxes_projection_binary.png", draw_boxes(binary, boxes, "projection filtered"))
        if rejected_boxes:
            dbg.save("06b_rejected_boxes_gray.png", draw_rejected_boxes(gray, boxes, rejected_boxes))

    reading, avg_conf, results = read_with_boxes(clahe_img, boxes, TARGET_H, dbg=dbg, label="projection")

    best = (reading, avg_conf, results, boxes, "projection", candidate_score(reading, avg_conf, boxes))

    # Optional fallback: try fixed equal slots ONLY when projection is clearly bad.
    projection_is_good = (
        len(boxes) >= PROJECTION_GOOD_MIN_BOXES
        and avg_conf >= PROJECTION_GOOD_MIN_CONF
        and '?' not in reading
    )

    if USE_FIXED_SLOT_FALLBACK and not (FIXED_FALLBACK_ONLY_IF_PROJECTION_BAD and projection_is_good):
        for n_digits in EXPECTED_DIGITS_OPTIONS:
            slot_boxes = fixed_slot_boxes_from_activity(binary, TARGET_H, n_digits)
            if not slot_boxes:
                continue
            if debug:
                dbg.save(f"08_boxes_fixed_{n_digits}_gray.png", draw_boxes(gray, slot_boxes, f"fixed {n_digits}"))
            r2, c2, res2 = read_with_boxes(clahe_img, slot_boxes, TARGET_H, dbg=None if SAVE_ONLY_SUMMARY else dbg, label=f"fixed_{n_digits}")
            score2 = candidate_score(r2, c2, slot_boxes)
            if (len(boxes) == 0) or (score2 > best[5] + 0.05):
                best = (r2, c2, res2, slot_boxes, f"fixed_{n_digits}", score2)

    final_reading, final_conf, final_results, final_boxes, method, final_score = best

    if debug:
        summary = draw_boxes(gray, final_boxes, f"chosen: {method} {final_reading} {final_conf:.2f}")
        dbg.save("99_CHOSEN_SUMMARY.png", summary)
        with open(dbg.dir / "summary.txt", "w", encoding="utf-8") as f:
            f.write(f"image={image_path}\n")
            f.write(f"chosen_method={method}\n")
            f.write(f"reading={final_reading}\n")
            f.write(f"avg_conf={final_conf:.4f}\n")
            f.write(f"candidate_score={final_score:.4f}\n")
            f.write(f"boxes={final_boxes}\n")
            f.write(f"rejected_boxes={rejected_boxes}\n")
            f.write("\nresults:\n")
            for r in final_results:
                f.write(str(r) + "\n")
        print(f"\nDebug saved to: {dbg.dir}")

    print("\nChosen method:", method)
    print("Final reading:", final_reading)
    print("Average confidence:", f"{final_conf*100:.1f}%")
    return final_reading, final_conf, final_results


if __name__ == "__main__":
    print(f"Testing: {Path(IMAGE_PATH).name}")
    print("=" * 60)
    segment_and_read(IMAGE_PATH, debug=DEBUG)
