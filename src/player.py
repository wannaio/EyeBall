from ursina import Entity, color, curve
from math import degrees


class Player(Entity):
    def __init__(self, lanes, **kwargs):
        super().__init__(
            model='sphere',
            color=color.azure,
            scale=0.5,
            position=(lanes[1], 1, 0),
            collider='sphere',
            texture='white_cube',
            **kwargs
        )
        self.lanes = lanes         # lanes which ball cal roll on
        self.lane_index = 1        # start in the center lane
        self.rotation_speed = 180  # degrees per second
        self.y_velocity = 0

    def update_position(self, dt, speed, ball_radius):
        # simulate rollong
        self.z += speed * dt
        distance_moved = speed * dt
        self.rotation_x += degrees(distance_moved / ball_radius)

    def switch_lane(self, target_index, duration=0.2):
        self.lane_index = target_index
        self.animate_x(self.lanes[target_index],
                       duration=duration, curve=curve.out_expo)
