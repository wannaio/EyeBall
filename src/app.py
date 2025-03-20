from ursina import Entity, color
from ursina import Ursina, camera, time, held_keys, destroy, scene
from player import Player
from obstacle import spawn_obstacle_at
from level import LevelManager
from ui import UIManager
from utils import apply_gravity
from game_env import GameEnv
import random

app = Ursina()

# Game configuration
lanes = [-2, 0, 2]
base_speed = 5
ball_radius = 0.25
gravity = 9.8

# Level and obstacle settings
level_length = 300
max_level = 5
level_speed = {1: 1.0, 2: 1.2, 3: 1.4, 4: 1.6, 5: 1.8}
obstacle_min_spacing = 5

# Global game state
game_active = True
score = 0
obstacles = []
last_obstacle_z = 0
lane_switch_cooldown = 0
jumping = False

# Cameras    
camera.position = (0, 5, -10)
camera.rotation_x = 20

# Instantiate game env and managers
game_env = GameEnv()
player = Player(lanes)
level_manager = LevelManager(level_length, max_level, level_speed)
ui_manager = UIManager(camera.ui)


def handle_jumping():
    global jumping
    is_grounded = player.y <= 1.01
    if held_keys['space'] and is_grounded and not jumping:
        jumping = True
        player.y_velocity = 4  # jump_speed

    if jumping:
        player.y += player.y_velocity * time.dt
        player.y_velocity = apply_gravity(player.y_velocity, gravity, time.dt)
        if player.y <= 1.0 and player.y_velocity < 0:
            player.y = 1.0
            player.y_velocity = 0
            jumping = False
    if player.y < 1.0:
        player.y = 1.0


def handle_lane_movement():
    global lane_switch_cooldown
    if lane_switch_cooldown <= 0:
        if held_keys['a'] or held_keys['left']:
            if player.lane_index > 0:
                player.switch_lane(player.lane_index - 1)
                lane_switch_cooldown = 0.3
        if held_keys['d'] or held_keys['right']:
            if player.lane_index < len(lanes) - 1:
                player.switch_lane(player.lane_index + 1)
                lane_switch_cooldown = 0.3


def ensure_obstacles_ahead():
    global last_obstacle_z
    spawn_horizon = 60
    fixed_offset = 40
    
    if not obstacles or (last_obstacle_z < player.z + spawn_horizon):
        # ensure offset from last/player
        next_spawn_z = max(player.z + fixed_offset, last_obstacle_z + obstacle_min_spacing + random.randint(0, obstacle_min_spacing))
        spawn_obstacle_at(next_spawn_z, lanes, level_manager.current_level, obstacles)

        if random.random() < 0.1:  
            extra_spawn_z = next_spawn_z + obstacle_min_spacing + random.randint(0, obstacle_min_spacing)
            spawn_obstacle_at(extra_spawn_z, lanes, level_manager.current_level, obstacles)
            next_spawn_z = extra_spawn_z

        last_obstacle_z = next_spawn_z


def check_collisions():
    global game_active
    for obstacle in obstacles[:]:
        if player.intersects(obstacle).hit:
            game_active = False
            from ursina import Text
            game_over_text = Text(text=f"Game Over! Score: {int(score)}", 
                                  origin=(0, 0), scale=2, parent=camera.ui)
        if obstacle.z < player.z - 10:
            obstacles.remove(obstacle)
            destroy(obstacle)


def update():
    global score, lane_switch_cooldown
    if not game_active:
        return

    current_speed = base_speed * level_speed[level_manager.current_level]
    player.update_position(time.dt, current_speed, ball_radius)
    camera.position = (player.x, player.y + 5, player.z - 10)

    if lane_switch_cooldown > 0:
        lane_switch_cooldown -= time.dt

    handle_lane_movement()
    handle_jumping()

    score += time.dt
    level_manager.check_progression(player.z, camera.ui)
    ensure_obstacles_ahead()
    check_collisions()
    ui_manager.update(level_manager.current_level,
                      level_speed[level_manager.current_level], score)


app.run()
