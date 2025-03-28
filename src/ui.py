from ursina import Text, color

# TODO: Add a way to check screen size and adjust UI elements accordingly
class UIManager:
    def __init__(self, ui):
        self.ui = ui
        self.level_text = Text(text="Level: 1", position=(-0.75, 0.45), parent=self.ui)
        self.speed_text = Text(text="Speed: 1.0x", position=(-0.75, 0.4), parent=self.ui)
        self.score_text = Text(text="Score: 0", position=(-0.75, 0.35), parent=self.ui)
    
    def update(self, level, speed_multiplier, score, ai_score=None):
        self.level_text.text = f"Level: {level}"
        self.speed_text.text = f"Speed: {speed_multiplier:.1f}x"
        self.score_text.text = f"Your Score: {int(score)}"
