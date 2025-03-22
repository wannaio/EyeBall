import cv2
import mediapipe as mp
import numpy as np


mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# landmark indices for eyes and iris
LEFT_EYE = [33, 133]
RIGHT_EYE = [362, 263]
LEFT_IRIS = 468
RIGHT_IRIS = 473

# settings
COLOR_TOP = (50, 50, 50)
COLOR_BOTTOM = (80, 80, 80)
CONTOUR_COLOR = (220, 220, 230)
IRIS_COLOR = (180, 229, 255)
PUPIL_COLOR = (0, 0, 0)
HIGHLIGHT_COLOR = (255, 255, 255)
ARROW_ACTIVE = (150, 255, 150)
ARROW_INACTIVE = (70, 70, 70)
BALL_COLOR = (255, 255, 255)
GAZE_TEXT_COLOR = (150, 190, 230)

cap = cv2.VideoCapture(0)


def create_gradient_background(h, w, top_color, bottom_color):
    """Create a vertical gradient background."""
    bg = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        alpha = y / h
        color = (np.array(top_color) * (1 - alpha) + np.array(bottom_color) * alpha).astype(np.uint8)
        bg[y, :] = color
    return bg


def draw_arrow(img, side, active):
    """Draw left or right arrow indicating gaze direction."""
    h, w = img.shape[:2]
    size = 60
    y = h - 100
    color = ARROW_ACTIVE if active else ARROW_INACTIVE
    if side == "left":
        pts = np.array([[100, y], [100 + size, y - size // 2], [100 + size, y + size // 2]])
    else:
        pts = np.array([[w - 100, y], [w - 100 - size, y - size // 2], [w - 100 - size, y + size // 2]])
    cv2.fillPoly(img, [pts.astype(np.int32)], color)


def draw_ball(img):
    """Draw a central ball indicator."""
    h, w = img.shape[:2]
    center = (w // 2, h - 100)
    cv2.circle(img, center, 12, BALL_COLOR, -1)


def get_gaze(landmarks):
    """Determine gaze direction based on iris positions."""
    def ratio(indices, iris_idx):
        eye = [landmarks[i] for i in indices]
        iris = landmarks[iris_idx]
        x_min = min(p.x for p in eye)
        x_max = max(p.x for p in eye)
        return (iris.x - x_min) / (x_max - x_min + 1e-6)
    left = ratio(LEFT_EYE, LEFT_IRIS)
    right = ratio(RIGHT_EYE, RIGHT_IRIS)
    avg = (left + right) / 2
    if avg < 0.4:
        return "left"
    elif avg > 0.6:
        return "right"
    return "center"


def draw_eye_details(bg, center, iris_radius=10, pupil_radius=4):
    """Draw the eye with a soft iris, central pupil, and highlight."""
    cv2.circle(bg, center, iris_radius, IRIS_COLOR, -1)
    cv2.circle(bg, center, pupil_radius, PUPIL_COLOR, -1)
    highlight_center = (center[0] - iris_radius // 2, center[1] - iris_radius // 2)
    cv2.circle(bg, highlight_center, 2, HIGHLIGHT_COLOR, -1)


def main():
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        bg = create_gradient_background(h, w, COLOR_TOP, COLOR_BOTTOM)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        direction = "center"

        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark
            direction = get_gaze(lm)

            for conn in mp_face_mesh.FACEMESH_TESSELATION:
                p1 = lm[conn[0]]
                p2 = lm[conn[1]]
                x1, y1 = int(p1.x * w), int(p1.y * h)
                x2, y2 = int(p2.x * w), int(p2.y * h)
                cv2.line(bg, (x1, y1), (x2, y2), CONTOUR_COLOR, 1)

            for iris_idx in [LEFT_IRIS, RIGHT_IRIS]:
                cx, cy = int(lm[iris_idx].x * w), int(lm[iris_idx].y * h)
                draw_eye_details(bg, (cx, cy))

        # UI elements
        draw_arrow(bg, "left", direction == "left")
        draw_arrow(bg, "right", direction == "right")
        draw_ball(bg)

        cv2.putText(bg, "Testing testing...", (w // 2 - 160, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (240, 240, 240), 3, cv2.LINE_AA)
        cv2.putText(bg, f"Gaze: {direction}", (w // 2 - 110, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, GAZE_TEXT_COLOR, 2)

        cv2.imshow("Gaze Visualizer", bg)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()