from ursina import Text, color


class UIManager:
    def __init__(self, ui):
        self.ui = ui
        self.level_text = Text(text="Level: 1", position=(-0.75, 0.45), parent=self.ui)
        self.speed_text = Text(text="Speed: 1.0x", position=(-0.75, 0.4), parent=self.ui)
        self.score_text = Text(text="Score: 0", position=(-0.75, 0.35), parent=self.ui)
        self.ai_score_text = None
    
    def update(self, level, speed_multiplier, score, ai_score=None):
        self.level_text.text = f"Level: {level}"
        self.speed_text.text = f"Speed: {speed_multiplier:.1f}x"
        self.score_text.text = f"Your Score: {int(score)}"

        if ai_score is not None:
            if self.ai_score_text is None:
                self.ai_score_text = Text(text=f"AI Score: {int(ai_score)}", 
                                         position=(-0.75, 0.3), 
                                         color=color.red, 
                                         parent=self.ui)
            else:
                self.ai_score_text.text = f"AI Score: {int(ai_score)}"