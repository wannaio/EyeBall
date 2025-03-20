from ursina import Text, destroy, color


class LevelManager:
    def __init__(self, level_length, max_level, level_speed_dict, current_level=1):
        self.level_length = level_length
        self.max_level = max_level
        self.level_speed = level_speed_dict
        self.current_level = current_level
        self.next_level_z = level_length

    def check_progression(self, ball_z, camera_ui):
        if ball_z >= self.next_level_z and self.current_level < self.max_level:
            self.current_level += 1
            self.next_level_z += self.level_length
            level_text = Text(
                text=f"Level {self.current_level}!\nSpeed: +{int((self.level_speed[self.current_level]-1)*100)}%",
                origin=(0, 0),
                scale=2.5,
                color=color.yellow,
                parent=camera_ui
            )
            destroy(level_text, delay=2)
