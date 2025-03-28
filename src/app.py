from eye_tracking.eye_tracker import EyeTracker  # have to be imported before ursina...
from ursina import Ursina, camera, time, held_keys, destroy, scene, Text, color
from player import Player
from level import LevelManager
from ui import UIManager
from game_env import GameEnv
from game_controller import GameController
import sys


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

# Game state
use_eye_tracking = True
controls_text_shown = False


def check_collisions():
    for obstacle in game_controller.obstacles[:]:
        if player.intersects(obstacle).hit:
            game_controller.game_active = False
            game_over_text = Text(text=f"Game Over! Your Score: {int(game_controller.score)}",
                                  origin=(0, 0), scale=1.5, parent=camera.ui)

        # clean up obstacles behind player
        min_z = player.z - 10
        if obstacle.z < min_z:
            game_controller.obstacles.remove(obstacle)
            destroy(obstacle)


def reset_game():
    """Reset the game state to start a new game"""
    global controls_text_shown

    game_controller.reset_game(player)

    for entity in scene.entities:
        if isinstance(entity, Text):
            if ("Game Over" in getattr(entity, 'text', '') or
                    "Controls:" in getattr(entity, 'text', '')):
                destroy(entity, delay=2)

    restart_text = Text(text="Game Restarted!",
                        position=(-0.15, 0.3),
                        scale=1.2,
                        color=color.green,
                        parent=camera.ui)
    destroy(restart_text, delay=2)

    controls_text_shown = False


def update():
    """Main game loop"""
    global use_eye_tracking, controls_text_shown

    if held_keys['escape']:
        print("Exiting game...")
        app.destroy()
        sys.exit()

    # allow restart during gameplay with Shift+R
    if held_keys['r'] and held_keys['shift']:
        reset_game()
        return

    if not game_controller.game_active:
        if held_keys['r']:
            reset_game()
            return

        if not controls_text_shown:
            Text(text="Controls:\nR: Restart\nE: Toggle Eye Tracking\nEscape: Exit",
                 position=(-0.5, 0.2),
                 scale=1,
                 color=color.white,
                 parent=camera.ui)
            controls_text_shown = True
        return

    # toggle eye tracking with 'e' key
    if held_keys['e'] and game_controller.lane_switch_cooldown <= 0:
        use_eye_tracking = not use_eye_tracking
        eye_tracking_text = Text(text=f"Eye tracking: {'ON' if use_eye_tracking else 'OFF'}",
                                 origin=(0, 0.3), scale=1.2, parent=camera.ui)
        destroy(eye_tracking_text, delay=2)
        time.sleep(0.2)
        game_controller.lane_switch_cooldown = 0.3

    # update player
    current_speed = base_speed * level_speed[level_manager.current_level]
    player.update_position(time.dt, current_speed, ball_radius)

    camera.position = (player.x, player.y + 5, player.z - 10)

    # player movements
    game_controller.handle_lane_movement(
        player, eye_tracker, use_eye_tracking, held_keys)
    game_controller.handle_jumping(player, held_keys['space'])

    # game state
    game_controller.score += time.dt
    level_manager.check_progression(player.z, camera.ui)
    game_controller.ensure_obstacles_ahead(player, level_manager)
    check_collisions()

    # UI
    ui_manager.update(level_manager.current_level,
                      level_speed[level_manager.current_level],
                      game_controller.score)

app = Ursina(
    title="EyeBall Game",
    borderless=True,
    fullscreen=False,
    vsync=True,
    development_mode=True
)

try:
    eye_tracker = EyeTracker()
    eye_tracker.start()
    print("Eye tracker initialized successfully")
except Exception as e:
    print(f"Error initializing EyeTracker: {e}")
    use_eye_tracking = False

# Init game objects
game_env = GameEnv()
player = Player(lanes, color=color.white)
game_controller = GameController(lanes, base_speed, gravity, ball_radius, obstacle_min_spacing)

camera.position = (0, 5, -10)
camera.rotation_x = 20

level_manager = LevelManager(level_length, max_level, level_speed)
ui_manager = UIManager(camera.ui)

if __name__ == '__main__':
    app.run()