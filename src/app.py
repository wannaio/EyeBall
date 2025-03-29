from eye_tracking.eye_tracker import EyeTracker  # have to be imported before ursina...
from ursina import Ursina, camera, time, held_keys, destroy, scene, Text, color
from player import Player
from level import LevelManager
from ui import UIManager
from game_env import GameEnv
from game_controller import GameController
from rl.ai_controller import AIController
import sys
from pathlib import Path


# Define paths for RL model
rl_dir = str(Path(__file__).parent.absolute() / "RL")
model_path = f"{rl_dir}/models/best/best_model"
stats_path = f"{rl_dir}/models/vec_normalize.pkl"

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
    global ai_active
    for obstacle in game_controller.obstacles[:]:
        if player.intersects(obstacle).hit:
            game_controller.game_active = False
            game_over_text = Text(text=f"Game Over! Your Score: {int(game_controller.score)}",
                                  origin=(0, 0), scale=1.5, parent=camera.ui)

        if ai_active and ai_player.intersects(obstacle).hit:
            ai_game_over_text = Text(text=f"AI crashed! AI Score: {int(game_controller.ai_score)}",
                                     position=(0.3, -0.4), scale=1.5, color=color.red, parent=camera.ui)
            ai_active = False
            print("AI crashed!")

        # clean up obstacles behind player
        min_z = player.z - 10
        if obstacle.z < min_z:
            game_controller.obstacles.remove(obstacle)
            destroy(obstacle)


def reset_game():
    """Reset the game state to start a new game"""
    global ai_active, controls_text_shown

    game_controller.reset_game(player, ai_player)
    ai_active = True

    for entity in scene.entities:
        if isinstance(entity, Text):
            if ("Game Over" in getattr(entity, 'text', '') or
                "AI crashed" in getattr(entity, 'text', '') or
                    "Controls:" in getattr(entity, 'text', '')):
                destroy(entity, delay=2)

    restart_text = Text(text="Game Restarted!",
                        position=(-0.15, 0.3),
                        scale=1.2,
                        color=color.green,
                        parent=camera.ui)
    destroy(restart_text, delay=2)
    
    ai_indicator_exists = False
    for entity in scene.entities:
        if isinstance(entity, Text) and "AI Agent Running" in getattr(entity, 'text', ''):
            ai_indicator_exists = True
            break

    if not ai_indicator_exists:
        Text(text="AI Agent Running",
             position=(-0.7, -0.4),
             scale=1,
             color=color.red,
             parent=camera.ui)

    controls_text_shown = False


def update():
    """Main game loop"""
    global use_eye_tracking, ai_active, controls_text_shown

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

    if ai_active:
        ai_player.update_position(time.dt, current_speed, ball_radius)
        game_controller.ai_score += time.dt
        ai_action = ai_controller.process_action(time.dt, ai_player, game_controller.obstacles,
                                                 lanes, base_speed, level_speed, level_manager.current_level)
        game_controller.handle_ai_jumping(ai_player, ai_action)
    elif not ai_active and ai_player.z < player.z:
        ai_player.update_position(time.dt, current_speed, ball_radius)

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
                      game_controller.score, game_controller.ai_score)

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
ai_player = Player(lanes, color=color.red)
game_controller = GameController(lanes, base_speed, gravity, ball_radius, obstacle_min_spacing)
ai_controller = AIController(rl_dir, model_path, stats_path)
ai_active = True

ai_text = Text(text="AI Agent Running",
               position=(-0.7, -0.4),
               scale=1,
               color=color.red,
               parent=camera.ui)

camera.position = (0, 5, -10)
camera.rotation_x = 20

level_manager = LevelManager(level_length, max_level, level_speed)
ui_manager = UIManager(camera.ui)

if __name__ == '__main__':
    app.run()