from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.env_util import make_vec_env
from eyeball_env import EyeBallEnv
from pathlib import Path
import os


def make_eyeball_env():
    return EyeBallEnv(headless=True)


parent_dir = str(Path(__file__).parent.absolute())
models_dir = f"{parent_dir}/models"
logs_dir = f"{parent_dir}/logs"
os.makedirs(models_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

# vectorization and normalization of the environment
env = make_vec_env(make_eyeball_env, n_envs=4)  # nr parallel envs to train in
env = VecNormalize(env, norm_obs=True, norm_reward=True)

# callbacks for evaluation and checkpointing
eval_env = make_vec_env(make_eyeball_env, n_envs=1)
eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=True)

eval_callback = EvalCallback(
    eval_env,
    best_model_save_path=f"{models_dir}/best",
    log_path=logs_dir,
    eval_freq=10000,
    deterministic=True,
    render=False
)

checkpoint_callback = CheckpointCallback(
    save_freq=50000,
    save_path=f"{models_dir}/checkpoints",
    name_prefix="eyeball_model"
)

model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    learning_rate=1e-3,
    n_steps=4096,
    batch_size=128,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    tensorboard_log=logs_dir
)

# train
total_timesteps = 1_000_000
model.learn(
    total_timesteps=total_timesteps,
    callback=[eval_callback, checkpoint_callback]
)

model.save(f"{models_dir}/eyeball_final_model")
env.save(f"{models_dir}/vec_normalize.pkl")
print("Training completed!")