import numpy as np
import sys
from pathlib import Path


class AIController:
    def __init__(self, rl_dir, model_path, stats_path):
        self.rl_dir = rl_dir
        self.model_path = model_path
        self.stats_path = stats_path
        self.ai_model = None
        self.ai_stats = None
        self.ai_action = 0
        self.ai_action_cooldown = 0

        self.load_rl_agent()

    def load_rl_agent(self):
        """Load the reinforcement learning agent if available"""
        try:
            if self.rl_dir not in sys.path:
                sys.path.append(self.rl_dir)

            from stable_baselines3 import PPO
            from stable_baselines3.common.vec_env import VecNormalize, DummyVecEnv
            from rl.eyeball_env import EyeBallEnv

            dummy_env = DummyVecEnv([lambda: EyeBallEnv(headless=True)])

            try:
                self.ai_stats = VecNormalize.load(self.stats_path, dummy_env)
                print("RL agent normalization stats loaded.")
            except FileNotFoundError:
                print("Warning: Could not load RL normalization stats. Using unnormalized environment.")
                self.ai_stats = None

            self.ai_model = PPO.load(self.model_path)
            print("RL agent loaded successfully!")
            return True

        except Exception as e:
            print(f"Failed to load RL agent: {e}")
            return False

    def get_observation(self, ai_player, obstacles, lanes, base_speed, level_speed, current_level):
        """Create a normalized observation for the AI"""
        obs = np.zeros(10, dtype=np.float32)

        obs[0] = ai_player.lane_index  # Lane index (0, 1, 2)
        obs[1] = ai_player.y           # Height
        obs[2] = getattr(ai_player, 'y_velocity', 0)

        # two nearest obstacles ahead
        obstacles_ahead = sorted(
            [o for o in obstacles if o.z > ai_player.z],
            key=lambda o: o.z
        )

        # first obstacle info
        if len(obstacles_ahead) > 0:
            o1 = obstacles_ahead[0]
            obs[3] = o1.z - ai_player.z  # Distance
            obs[4] = lanes.index(o1.x) if o1.x in lanes else -1  # Lane
            obs[5] = o1.scale[1]  # Height
        else:
            obs[3:6] = [100, -1, 0]

        # second obstacle info
        if len(obstacles_ahead) > 1:
            o2 = obstacles_ahead[1]
            obs[6] = o2.z - ai_player.z
            obs[7] = lanes.index(o2.x) if o2.x in lanes else -1
            obs[8] = o2.scale[1]
        else:
            obs[6:9] = [100, -1, 0]

        current_speed = base_speed * level_speed[current_level]
        obs[9] = current_speed

        return obs

    def process_action(self, time_dt, ai_player, obstacles, lanes, base_speed, level_speed, current_level):
        if self.ai_action_cooldown <= 0 and self.ai_model:
            observation = self.get_observation(
                ai_player, obstacles, lanes, base_speed, level_speed, current_level).reshape(1, -1)

            if self.ai_stats and hasattr(self.ai_stats, 'normalize_obs'):
                observation = self.ai_stats.normalize_obs(observation)

            self.ai_action, _ = self.ai_model.predict(
                observation, deterministic=True)
            self.ai_action = self.ai_action[0]

            # lane movements
            if self.ai_action == 1 and ai_player.lane_index > 0:  # Move left
                ai_player.switch_lane(ai_player.lane_index - 1)
                self.ai_action_cooldown = 0.3
            # Move right
            elif self.ai_action == 2 and ai_player.lane_index < len(lanes) - 1:
                ai_player.switch_lane(ai_player.lane_index + 1)
                self.ai_action_cooldown = 0.3

            self.ai_action_cooldown = 0.1
        else:
            self.ai_action_cooldown -= time_dt

        return self.ai_action
