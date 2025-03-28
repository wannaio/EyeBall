from ursina import Entity, Sky, color, camera


class GameEnv:
    def __init__(self):
        self.sky = Sky(texture='sky_default')
        
        # floating platform
        self.platform = Entity(
            model='cube',
            scale=(10, 1, 3000),
            color=color.light_gray,
            texture='white_cube',
            texture_scale=(50, 150),
            collider='box',
            position=(0, -1, 0)
        )

        lanes = [-2, 0, 2] 
        for lane in lanes:
            # indicate where lanes are
            for z in range(0, 30, 20):
                support = Entity(
                    model='diamond',
                    scale=(1, 1, 1),
                    color=color.white,
                    position=(lane, 0, z),
                    texture='white_cube'
                )
