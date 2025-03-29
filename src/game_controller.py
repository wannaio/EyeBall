from ursina import destroy, time
from obstacle import spawn_obstacle_at
from utils import apply_gravity
import random


class GameController:
    def __init__(self, lanes, base_speed, gravity, ball_radius, obstacle_min_spacing):
        # settings
        self.lanes = lanes
        self.base_speed = base_speed
        self.gravity = gravity
        self.ball_radius = ball_radius
        self.obstacle_min_spacing = obstacle_min_spacing

        # state
        self.game_active = True
        self.score = 0
        self.ai_score = 0
        self.obstacles = []
        self.last_obstacle_z = 0
        self.lane_switch_cooldown = 0
        self.jumping = False
        self.ai_jumping = False
        self.eye_command_processed = True
        self.last_eye_direction = "center"

    def reset_game(self, player, ai_player):
        for obstacle in self.obstacles[:]:
            destroy(obstacle)
        self.obstacles.clear()

        self.game_active = True
        self.score = 0
        self.last_obstacle_z = 0
        self.ai_score = 0
        self.jumping = False
        self.ai_jumping = False

        player.reset()
        ai_player.reset()

    def handle_jumping(self, player, jump_key_pressed):
        is_grounded = player.y <= 0.01

        if jump_key_pressed and is_grounded and not self.jumping:
            self.jumping = True
            player.y_velocity = 4  # jump_speed

        if self.jumping:
            player.y += player.y_velocity * time.dt
            player.y_velocity = apply_gravity(
                player.y_velocity, self.gravity, time.dt)
            if player.y <= 0 and player.y_velocity < 0:
                player.y = 0
                player.y_velocity = 0
                self.jumping = False
        if player.y < 0:
            player.y = 0

    def handle_ai_jumping(self, ai_player, ai_action):
        if ai_action == 3 and ai_player.y <= 0.01 and not self.ai_jumping:
            self.ai_jumping = True
            ai_player.y_velocity = 4

        if self.ai_jumping:
            ai_player.y += ai_player.y_velocity * time.dt
            ai_player.y_velocity = apply_gravity(
                ai_player.y_velocity, self.gravity, time.dt)
            if ai_player.y <= 0 and ai_player.y_velocity < 0:
                ai_player.y = 0
                ai_player.y_velocity = 0
                self.ai_jumping = False
        if ai_player.y < 0:
            ai_player.y = 0

    def handle_lane_movement(self, player, eye_tracker, use_eye_tracking, held_keys):
        if self.lane_switch_cooldown > 0:
            self.lane_switch_cooldown -= time.dt
            return

        # get direction from eye tracker
        if use_eye_tracking:
            current_direction = eye_tracker.get_direction()

            if current_direction != self.last_eye_direction:
                self.eye_command_processed = False
                self.last_eye_direction = current_direction

            if not self.eye_command_processed and current_direction != "center":
                if current_direction == "left" and player.lane_index > 0:
                    player.switch_lane(player.lane_index - 1)
                    self.lane_switch_cooldown = 0.3
                    self.eye_command_processed = True
                elif current_direction == "right" and player.lane_index < len(self.lanes) - 1:
                    player.switch_lane(player.lane_index + 1)
                    self.lane_switch_cooldown = 0.3
                    self.eye_command_processed = True

            if current_direction == "center":
                self.eye_command_processed = False
        else:
            if held_keys['a'] or held_keys['left']:
                if player.lane_index > 0:
                    player.switch_lane(player.lane_index - 1)
                    self.lane_switch_cooldown = 0.3
            if held_keys['d'] or held_keys['right']:
                if player.lane_index < len(self.lanes) - 1:
                    player.switch_lane(player.lane_index + 1)
                    self.lane_switch_cooldown = 0.3

    def ensure_obstacles_ahead(self, player, level_manager):
        """Spawn obstacles ahead of player with an offset."""
        spawn_horizon = 60
        fixed_offset = 40

        if not self.obstacles or (self.last_obstacle_z < player.z + spawn_horizon):
            # ensure offset from last/player
            next_spawn_z = max(player.z + fixed_offset, self.last_obstacle_z +
                               self.obstacle_min_spacing + random.randint(0, self.obstacle_min_spacing))
            spawn_obstacle_at(next_spawn_z, self.lanes,
                              level_manager.current_level, self.obstacles)

            if random.random() < 0.1:
                extra_spawn_z = next_spawn_z + self.obstacle_min_spacing + \
                    random.randint(0, self.obstacle_min_spacing)
                spawn_obstacle_at(extra_spawn_z, self.lanes,
                                  level_manager.current_level, self.obstacles)
                next_spawn_z = extra_spawn_z

            self.last_obstacle_z = next_spawn_z
