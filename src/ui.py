from ursina import Text


class UIManager:
    def __init__(self, camera_ui):
        self.score_text = Text(
            text="0", position=(-0.75, 0.45), scale=2, parent=camera_ui)

    def update(self, current_level, speed_multiplier, score):
        self.score_text.text = f"Level: {current_level} | Score: {int(score)}"
