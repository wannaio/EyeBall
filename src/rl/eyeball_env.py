"""
Environment similar to the Ursina game engine, but headless for RL training purposes.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import sys
from pathlib import Path
import random


parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils import apply_gravity

class HeadlessPlayer:
    def __init__(self, lanes):
        self.lanes = lanes
        self.lane_index = 1  # Start in middle lane
        self.x = lanes[self.lane_index]
        self.y = 0.0  # Starting height
        self.z = 0.0  # Starting position
        self.y_velocity = 0
        
    def update_position(self, dt, speed, radius=0.25):
        self.z += speed * dt
        
    def switch_lane(self, new_index, duration=0.2):
        self.lane_index = new_index
        self.x = self.lanes[self.lane_index]
    
    def intersects(self, obstacle):
        # X-axis collision
        dx = abs(obstacle.position[0] - self.x)
        x_overlap = dx < (obstacle.scale[0]/2 + 0.25)  # ball_radius = 0.25
        
        # Y-axis collision
        player_bottom = self.y - 0.25
        player_top = self.y + 0.25
        obstacle_bottom = obstacle.position[1] - obstacle.scale[1]/2
        obstacle_top = obstacle.position[1] + obstacle.scale[1]/2
        y_overlap = (player_bottom < obstacle_top) and (player_top > obstacle_bottom)
        
        # Z-axis collision
        dz = abs(obstacle.position[2] - self.z)
        z_overlap = dz < (obstacle.scale[2]/2 + 0.25)
        
        hit = x_overlap and y_overlap and z_overlap
        return type('Intersection', (), {'hit': hit})

class HeadlessObstacle:
    def __init__(self, position, scale):
        self.position = position  # (x, y, z)
        self.scale = scale        # (width, height, depth)

class HeadlessGameEnv:
    def __init__(self):
        self.platform_scale = (10, 1, 3000)
        self.platform_position = (0, -1, 0)

def headless_spawn_obstacle(z_pos, lanes, level, obstacles, spacing):
    open_lane = random.randint(0, len(lanes)-1)

    if level >= 1 and random.random() < 0.2:
        for lane in lanes:
            position = (lane, 0.5, z_pos)
            scale = (1.5, 0.6, 0.5)
            obstacle = HeadlessObstacle(position, scale)
            obstacles.append(obstacle)
        return

    for idx, lane in enumerate(lanes):
        if idx == open_lane:
            continue
        spawn_probability = 0.5 + (level - 1) * 0.1
        if random.random() < spawn_probability:
            position = (lane, 0.5, z_pos)
            scale = (1.5, 1, 0.5)
            obstacle = HeadlessObstacle(position, scale)
            obstacles.append(obstacle)

class HeadlessLevelManager:
    def __init__(self, level_length, max_level, level_speeds):
        self.current_level = 1
        self.max_level = max_level
        self.level_length = level_length
        self.level_speeds = level_speeds
        self.next_level_z = level_length
        
    def check_progression(self, player_z, ui=None):
        if player_z >= self.next_level_z and self.current_level < self.max_level:
            self.current_level += 1
            self.next_level_z += self.level_length
            return True
        return False

class EyeBallEnv(gym.Env):
    def __init__(self, headless=True):
        super(EyeBallEnv, self).__init__()
        
        # needed headless to train... 
        self.headless = headless
        
        self.previous_lane = 1
        
        # Action space: 0 = do nothing, 1 = move left, 2 = move right, 3 = jump
        self.action_space = spaces.Discrete(4)
        
        # Observation space with relevant game state:
        # [player_lane_index, player_y, player_y_velocity, 
        #  obstacle1_z, obstacle1_lane, obstacle1_height,
        #  obstacle2_z, obstacle2_lane, obstacle2_height,
        #  current_speed]
        self.observation_space = spaces.Box(
            low=np.array([0, 0, -10, 0, -1, 0, 0, -1, 0, 0]),
            high=np.array([2, 5, 10, 100, 3, 2, 100, 3, 2, 10]),
            dtype=np.float32
        )

        self.lanes = [-2, 0, 2]
        self.base_speed = 5
        self.gravity = 9.8
        self.ball_radius = 0.25
        self.jump_speed = 4
        self.obstacle_min_spacing = 5
        self.level_length = 300
        self.max_level = 5
        self.level_speed = {1: 1.0, 2: 1.2, 3: 1.4, 4: 1.6, 5: 1.8}
        self.dt = 0.1  # 100ms per step in game
        
        self.reset()
    
    def seed(self, seed=None):
        """Sets the seed for this env's random number generator."""
        self.np_random, seed = gym.utils.seeding.np_random(seed)
        return [seed]
        
    def reset(self, seed=None, options=None):
        if seed is not None:
            self.seed(seed)

        if self.headless:
            self.game_env = HeadlessGameEnv()
            self.player = HeadlessPlayer(self.lanes)
            self.level_manager = HeadlessLevelManager(self.level_length, self.max_level, self.level_speed)
        else:
            from player import Player
            from level import LevelManager
            from game_env import GameEnv
            
            self.game_env = GameEnv()
            self.player = Player(self.lanes)
            self.level_manager = LevelManager(self.level_length, self.max_level, self.level_speed)

        self.obstacles = []
        self.last_obstacle_z = 0
        self.jumping = False
        self.score = 0
        self.done = False
        self.time_alive = 0
        self.previous_lane = 1
        
        self._ensure_obstacles_ahead()
        return self._get_observation(), {}
        
    def step(self, action):
        if self.done:
            return self._get_observation(), 0, True, False, {}

        self.previous_lane = self.player.lane_index
        self._process_action(action)

        current_speed = self.base_speed * self.level_speed[self.level_manager.current_level]
        self.player.update_position(self.dt, current_speed, self.ball_radius)
        self.time_alive += self.dt
        self.score += self.dt

        self._handle_jumping()
        self.level_manager.check_progression(self.player.z, None)        
        self._ensure_obstacles_ahead()

        hit = self._check_collisions()
        if hit:
            self.done = True
            reward = -40
        else:
            reward = 0.5 * self.dt * self.level_speed[self.level_manager.current_level]
            
            # lane change reward/penalty
            if self.player.lane_index != self.previous_lane:
                lane_reward = self._calculate_lane_change_reward()
                reward += lane_reward

        self._clean_obstacles()
        return self._get_observation(), reward, self.done, False, {}

    def _calculate_lane_change_reward(self):
        has_obstacle_current = False
        has_obstacle_previous = False

        look_ahead_distance = 15

        for obstacle in self.obstacles:
            if 0 < obstacle.position[2] - self.player.z < look_ahead_distance:
                if obstacle.position[0] == self.lanes[self.player.lane_index]:
                    has_obstacle_current = True

                if obstacle.position[0] == self.lanes[self.previous_lane]:
                    has_obstacle_previous = True

        if has_obstacle_previous and not has_obstacle_current:
            return 5.0
        elif not has_obstacle_previous and has_obstacle_current:
            return -5.0

        return 0.0

    def _process_action(self, action):
        if action == 1 and self.player.lane_index > 0:
            self.player.switch_lane(self.player.lane_index - 1, duration=0)
        elif action == 2 and self.player.lane_index < len(self.lanes) - 1:
            self.player.switch_lane(self.player.lane_index + 1, duration=0)
        elif action == 3 and self.player.y <= 0.01 and not self.jumping:
            self.jumping = True
            self.player.y_velocity = self.jump_speed
    
    def _handle_jumping(self):
        if self.jumping:
            self.player.y += self.player.y_velocity * self.dt
            self.player.y_velocity = apply_gravity(self.player.y_velocity, self.gravity, self.dt)
            if self.player.y <= 0 and self.player.y_velocity < 0:
                self.player.y = 0
                self.player.y_velocity = 0
                self.jumping = False
        if self.player.y < 0:
            self.player.y = 0
            
    def _ensure_obstacles_ahead(self):
        spawn_horizon = 60
        fixed_offset = 40
        
        if not self.obstacles or (self.last_obstacle_z < self.player.z + spawn_horizon):
            next_spawn_z = max(
                self.player.z + fixed_offset,
                self.last_obstacle_z + self.obstacle_min_spacing + random.randint(0, self.obstacle_min_spacing)
            )

            if self.headless:
                headless_spawn_obstacle(next_spawn_z, self.lanes, self.level_manager.current_level, 
                                        self.obstacles, self.obstacle_min_spacing)

                if random.random() < 0.1:  
                    extra_spawn_z = next_spawn_z + self.obstacle_min_spacing + random.randint(0, self.obstacle_min_spacing)
                    headless_spawn_obstacle(extra_spawn_z, self.lanes, self.level_manager.current_level, 
                                          self.obstacles, self.obstacle_min_spacing)
                    next_spawn_z = extra_spawn_z
            else:
                from obstacle import spawn_obstacle_at
                spawn_obstacle_at(next_spawn_z, self.lanes, self.level_manager.current_level, self.obstacles)

                if random.random() < 0.1:  
                    extra_spawn_z = next_spawn_z + self.obstacle_min_spacing + random.randint(0, self.obstacle_min_spacing)
                    spawn_obstacle_at(extra_spawn_z, self.lanes, self.level_manager.current_level, self.obstacles)
                    next_spawn_z = extra_spawn_z

            self.last_obstacle_z = next_spawn_z

    def _check_collisions(self):
        for obstacle in self.obstacles:
            if hasattr(self.player, 'intersects'):
                if self.player.intersects(obstacle).hit:
                    return True
            else:
                # X-axis (lane) collision
                dx = abs(obstacle.position[0] - self.player.x)
                x_overlap = dx < (obstacle.scale[0]/2 + self.ball_radius)
                
                # Y-axis (height) collision
                player_bottom = self.player.y - self.ball_radius
                player_top = self.player.y + self.ball_radius
                obstacle_bottom = obstacle.position[1] - obstacle.scale[1]/2
                obstacle_top = obstacle.position[1] + obstacle.scale[1]/2
                y_overlap = (player_bottom < obstacle_top) and (player_top > obstacle_bottom)
                
                # Z-axis (depth) collision
                dz = abs(obstacle.position[2] - self.player.z)
                z_overlap = dz < (obstacle.scale[2]/2 + self.ball_radius)
                
                if x_overlap and y_overlap and z_overlap:
                    return True
        return False
        
    def _clean_obstacles(self):
        self.obstacles = [obs for obs in self.obstacles if obs.position[2] > self.player.z - 10]
            
    def _get_observation(self):
        """
        The input to the agent is 10-dimensional vector representing the game state.
        The vector includes:
        - Player lane index (0, 1, 2)
        - Player height
        - Player Y velocity (for jumping)
        - Distance to the nearest obstacle ahead
        - Lane index of the nearest obstacle ahead
        - Height of the nearest obstacle ahead
        - Distance to the second nearest obstacle ahead
        - Lane index of the second nearest obstacle ahead
        - Height of the second nearest obstacle ahead
        - Current game speed
        """

        obs = np.zeros(10, dtype=np.float32)
        obs[0] = self.player.lane_index
        obs[1] = self.player.y
        obs[2] = getattr(self.player, 'y_velocity', 0)

        obstacles_ahead = sorted(
            [o for o in self.obstacles if o.position[2] > self.player.z],
            key=lambda o: o.position[2]
        )

        if len(obstacles_ahead) > 0:
            o1 = obstacles_ahead[0]
            obs[3] = o1.position[2] - self.player.z
            obs[4] = self.lanes.index(o1.position[0]) if o1.position[0] in self.lanes else -1
            obs[5] = o1.scale[1]
        else:
            obs[3:6] = [100, -1, 0]

        if len(obstacles_ahead) > 1:
            o2 = obstacles_ahead[1]
            obs[6] = o2.position[2] - self.player.z
            obs[7] = self.lanes.index(o2.position[0]) if o2.position[0] in self.lanes else -1
            obs[8] = o2.scale[1]
        else:
            obs[6:9] = [100, -1, 0]

        obs[9] = self.base_speed * self.level_speed[self.level_manager.current_level]
        
        return obs
        
    def render(self, mode='human'):
        pass