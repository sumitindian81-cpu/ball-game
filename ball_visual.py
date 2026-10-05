import cv2
import numpy as np
from balls_game import Game, Tube, create_sample_level  

# --- Colors (BGR for OpenCV) ---
COLOR_MAP = {
    "R": (0, 0, 255),
    "G": (0, 255, 0),
    "B": (255, 0, 0),
}

BG_COLOR = (50, 50, 50)       # background grey
TUBE_COLOR = (200, 200, 200)  # tube outline
TEXT_COLOR = (255, 255, 255)

WIDTH, HEIGHT = 800, 600


def draw_game(frame, game: Game):
    frame[:] = BG_COLOR  # clear background

    n = len(game.tubes)
    tube_width = 60
    tube_height = 300
    space = WIDTH // (n + 1)

    base_y = HEIGHT - 80  # bottom of tubes

    # Draw tubes and balls
    for i, tube in enumerate(game.tubes):
        center_x = space * (i + 1)

        # Tube rectangle coordinates
        x1 = center_x - tube_width // 2
        x2 = center_x + tube_width // 2
        y1 = base_y - tube_height
        y2 = base_y

        # Tube outline
        cv2.rectangle(frame, (x1, y1), (x2, y2), TUBE_COLOR, 2)

        # Draw balls (bottom to top)
        for level, color in enumerate(tube.balls):
            # bottom ball = level 0
            cy = y2 - 20 - level * (tube_height // tube.capacity)
            radius = 20
            cv2.circle(frame, (center_x, cy), radius, COLOR_MAP[color], -1)
            cv2.circle(frame, (center_x, cy), radius, (0, 0, 0), 2)

        # Tube index
        cv2.putText(
            frame,
            str(i),
            (center_x - 10, base_y + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            TEXT_COLOR,
            2,
            cv2.LINE_AA,
        )

    # Moves text
    cv2.putText(
        frame,
        f"Moves: {game.moves}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        TEXT_COLOR,
        2,
        cv2.LINE_AA,
    )

    if game.is_completed():
        cv2.putText(
            frame,
            "LEVEL COMPLETE!",
            (200, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.1,
            (0, 255, 255),
            3,
            cv2.LINE_AA,
        )


def main():
    game = create_sample_level()

    src_idx = None  # first selected tube

    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    print("Controls:")
    print("  Press number keys 0-9 to select a tube.")
    print("  First key = source tube, second key = destination.")
    print("  Press 'r' to restart, 'q' to quit.")

    while True:
        draw_game(frame, game)

        if src_idx is not None:
            cv2.putText(
                frame,
                f"Source: {src_idx}",
                (WIDTH - 200, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

        cv2.imshow("Ball Sort Game", frame)

        # X button se band karne ke liye
        if cv2.getWindowProperty("Ball Sort Game", cv2.WND_PROP_VISIBLE) < 1:
            break

        key = cv2.waitKey(30) & 0xFF

        if key == ord("q"):
            break
        if key == ord("r"):
            game = create_sample_level()
            src_idx = None
            continue

        if ord("0") <= key <= ord("9"):
            idx = key - ord("0")
            if 0 <= idx < len(game.tubes):
                if src_idx is None:
                    src_idx = idx
                else:
                    dst_idx = idx
                    moved = game.move(src_idx, dst_idx)
                    if not moved:
                        print("Move not allowed.")
                    src_idx = None

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()