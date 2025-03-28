from ursina import Entity, color, curve
from math import degrees


class Player(Entity):
    def __init__(self, lanes, color=color.azure, **kwargs):
        super().__init__(
            model='sphere',
            color=color,
            scale=0.5,
            position=(lanes[1], 0, 0),
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

    def update_y(self, dt, gravity):
        self.y_velocity += gravity * dt
        self.y -= self.y_velocity * dt
        if self.y < 0:
            self.y = 0
            self.y_velocity = 0

    def reset(self):
        """Reset player to starting position"""
        self.x = self.lanes[1]  # Center lane
        self.z = 0              # Start position
        self.y = 0              # Ground level
        self.y_velocity = 0     # No vertical movement
        self.lane_index = 1     # Center lane index
