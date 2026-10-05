import cv2
import mediapipe as mp
import math
import time
from balls_game import create_sample_level

# ----- MediaPipe -----
try:
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
except AttributeError:
    from mediapipe.python.solutions import hands as mp_hands
    from mediapipe.python.solutions import drawing_utils as mp_draw

# ----- Settings -----
WINDOW_NAME = "Gesture Ball Sort"
WIDTH, HEIGHT = 1280, 720

PICK_DIST = 35      # isse kam ho to pick
RELEASE_DIST = 55   # isse zyada ho to drop
SMOOTH_ALPHA = 0.35

TUBE_GLASS_ALPHA = 0.02
TUBE_GLASS_ALPHA_HOVER = 0.03

COLOR_MAP = {
    "R": (40, 40, 255),
    "G": (40, 220, 40),
    "B": (255, 80, 40),
}

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (0, 255, 255)
PURPLE = (255, 0, 255)

# ----- Game / Camera -----
game = create_sample_level()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

if not cap.isOpened():
    print("Camera nahi chala.")
    raise SystemExit

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6,
)

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, WIDTH, HEIGHT)

# ----- State -----
smooth_x, smooth_y = None, None
picked_ball = None      # {"color": "R", "src_idx": 1}
status_text = ""
status_until = 0.0

spacing = tube_width = tube_top = tube_bottom = ball_radius = 0


def set_status(text, dur=1.0):
    global status_text, status_until
    status_text = text
    status_until = time.time() + dur


def draw_text_outline(img, text, org, scale, color, th=2, out_th=4):
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale,
                BLACK, out_th, cv2.LINE_AA)
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale,
                color, th, cv2.LINE_AA)


def compute_layout(w, h, tube_count):
    global spacing, tube_width, tube_top, tube_bottom, ball_radius
    spacing = w // (tube_count + 1)
    tube_width = max(74, int(w * 0.07))
    tube_height = int(h * 0.54)
    tube_bottom = int(h * 0.86)
    tube_top = tube_bottom - tube_height
    ball_radius = max(18, int(tube_width * 0.28))


def tube_rect(i):
    cx = spacing * (i + 1)
    x1 = cx - tube_width // 2
    x2 = cx + tube_width // 2
    return x1, tube_top, x2, tube_bottom


def point_in_tube(x, y, i):
    x1, y1, x2, y2 = tube_rect(i)
    return x1 <= x <= x2 and y1 <= y <= y2


def draw_ball(frame, center, color, radius, scale=1.0):
    x, y = center
    r = int(radius * scale)
    cv2.circle(frame, (x + 2, y + 2), r + 2, (0, 0, 0), -1)
    cv2.circle(frame, (x, y), r, color, -1)
    cv2.circle(frame, (x - r // 3, y - r // 3),
               max(4, r // 3), (255, 255, 255), -1)
    cv2.circle(frame, (x, y), r, BLACK, 2)


def draw_tube(frame, center_x, tube, hover=False):
    x1 = center_x - tube_width // 2
    x2 = center_x + tube_width // 2
    y1 = tube_top
    y2 = tube_bottom

    h, w = frame.shape[:2]
    x1c, y1c = max(0, x1), max(0, y1)
    x2c, y2c = min(w, x2), min(h, y2)
    if x2c <= x1c or y2c <= y1c:
        return

    alpha = TUBE_GLASS_ALPHA_HOVER if hover else TUBE_GLASS_ALPHA
    roi = frame[y1c:y2c, x1c:x2c]
    overlay = roi.copy()
    overlay[:] = (255, 255, 255)
    cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0, roi)

    cv2.rectangle(frame, (x1c, y1c), (x2c, y2c), WHITE, 3)
    cv2.line(frame, (x1c + 8, y1c + 10), (x1c + 8, y2c - 10), (255, 255, 255), 1)
    cv2.ellipse(frame, (center_x, y1c),
                (tube_width // 2 - 4, 10), 0, 0, 180, WHITE, 2)

    itop = y1c + ball_radius + 12
    ibot = y2c - ball_radius - 12
    gap = (ibot - itop) / (tube.capacity - 1) if tube.capacity > 1 else 0

    for level, col in enumerate(tube.balls):
        by = int(ibot - level * gap)
        draw_ball(frame, (center_x, by), COLOR_MAP[col], ball_radius)


# --------- Main Loop -----------
while True:
    ok, frame = cap.read()
    if not ok:
        break

    frame = cv2.resize(frame, (WIDTH, HEIGHT))
    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]

    # light dim
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    frame = cv2.addWeighted(frame, 0.96, overlay, 0.04, 0)

    game_done = game.is_completed()

    # Layout
    tube_count = len(game.tubes)
    compute_layout(w, h, tube_count)

    # Hand
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    hand = None
    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(
            frame, hand, mp_hands.HAND_CONNECTIONS,
            mp_draw.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=2),
            mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2),
        )
        idx = hand.landmark[8]
        thb = hand.landmark[4]

        cx, cy = int(idx.x * w), int(idx.y * h)
        tx, ty = int(thb.x * w), int(thb.y * h)

        if smooth_x is None or smooth_y is None:
            smooth_x, smooth_y = cx, cy
        else:
            smooth_x = int((1 - SMOOTH_ALPHA) * smooth_x + SMOOTH_ALPHA * cx)
            smooth_y = int((1 - SMOOTH_ALPHA) * smooth_y + SMOOTH_ALPHA * cy)

        dist = math.hypot(smooth_x - tx, smooth_y - ty)
        cv2.circle(frame, (smooth_x, smooth_y), 14,
                   YELLOW if dist < PICK_DIST else PURPLE, 2)
        cv2.circle(frame, (smooth_x, smooth_y), 5,
                   YELLOW if dist < PICK_DIST else PURPLE, -1)
    else:
        smooth_x = smooth_y = None

    # Hover tube
    hover_idx = None
    if smooth_x is not None and smooth_y is not None:
        for i in range(tube_count):
            if point_in_tube(smooth_x, smooth_y, i):
                hover_idx = i
                break

    # ----- PICK / DROP -----
    if hand is not None and not game_done and smooth_x is not None and smooth_y is not None:
        idx = hand.landmark[8]
        thb = hand.landmark[4]
        dist = math.hypot(
            int(idx.x * w) - int(thb.x * w),
            int(idx.y * h) - int(thb.y * h),
        )

        # PICK: distance < PICK_DIST and no ball in hand
        if dist < PICK_DIST and picked_ball is None and hover_idx is not None:
            src_tube = game.tubes[hover_idx]
            if len(src_tube.balls) > 0:
                color = src_tube.pop()
                picked_ball = {"color": color, "src_idx": hover_idx}
                set_status("Ball picked", 0.5)

        # DROP: distance > RELEASE_DIST and ball in hand
        if dist > RELEASE_DIST and picked_ball is not None:
            if hover_idx is not None:
                dst_tube = game.tubes[hover_idx]
                if len(dst_tube.balls) < dst_tube.capacity:
                    dst_tube.push(picked_ball["color"])
                    game.moves += 1
                    set_status("Ball dropped", 0.6)
                else:
                    game.tubes[picked_ball["src_idx"]].push(picked_ball["color"])
                    set_status("Tube full! Ball returned.", 0.8)
            else:
                game.tubes[picked_ball["src_idx"]].push(picked_ball["color"])
                set_status("No tube. Ball returned.", 0.8)

            picked_ball = None

    # Draw tubes
    for i, tube in enumerate(game.tubes):
        cx = spacing * (i + 1)
        draw_tube(frame, cx, tube, hover=(i == hover_idx))

    # Draw picked ball following finger
    if picked_ball is not None and smooth_x is not None and smooth_y is not None:
        draw_ball(
            frame,
            (smooth_x, smooth_y - 10),
            COLOR_MAP[picked_ball["color"]],
            ball_radius,
            scale=1.2,
        )

    # Header / Footer
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 78), (15, 15, 15), -1)
    frame = cv2.addWeighted(overlay, 0.45, frame, 0.55, 0)

    draw_text_outline(frame, f"LEVEL: 1", (25, 46), 1.0, WHITE, 2, 4)
    draw_text_outline(frame, f"MOVES: {game.moves}", (215, 46), 1.0, WHITE, 2, 4)
    draw_text_outline(frame, "R: Restart", (w - 210, 32), 0.7, WHITE, 2, 3)
    draw_text_outline(frame, "Q: Quit", (w - 210, 60), 0.7, WHITE, 2, 3)

    draw_text_outline(
        frame,
        "FREE MODE: Pinch TOP ball to PICK, open hand to DROP.",
        (25, h - 38),
        0.6,
        WHITE,
        1,
        3,
    )
    draw_text_outline(
        frame,
        "Goal: Har tube me same colour. 1 move = 1 TOP ball.",
        (25, h - 14),
        0.6,
        YELLOW,
        1,
        3,
    )

    if time.time() < status_until and status_text:
        draw_text_outline(
            frame, status_text, (w // 2 - 200, h - 65), 0.8, WHITE, 2, 4
        )

    if game_done:
        banner = frame.copy()
        bx1, by1 = w // 2 - 250, 90
        bx2, by2 = w // 2 + 250, 170
        cv2.rectangle(banner, (bx1, by1), (bx2, by2), (0, 0, 0), -1)
        frame = cv2.addWeighted(banner, 0.35, frame, 0.65, 0)
        draw_text_outline(frame, "LEVEL COMPLETE!", (w // 2 - 190, 145),
                          1.2, YELLOW, 3, 5)

    cv2.imshow(WINDOW_NAME, frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord("r"):
        game = create_sample_level()
        picked_ball = None
        smooth_x = smooth_y = None
        status_text = ""
        status_until = 0.0
        set_status("Restarted", 0.8)

cap.release()
cv2.destroyAllWindows()