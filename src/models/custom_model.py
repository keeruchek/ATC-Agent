# ATC-Agent/train.py

import ray
from ray.tune.registry import register_env
from src.env.atc_env import ATCEnv
from src.models.custom_model import CentralizedCriticModel

# 1. Register the environment so RLlib can find it
def env_creator(env_config):
    return ATCEnv(env_config)

register_env("atc-v0", env_creator)

# 2. Configure the algorithm
config = (
    PPOConfig()
    .environment("atc-v0")
    .training(
        model={
            "custom_model": CentralizedCriticModel, # Your GNN/LSTM Brain
        }
    )
    .multi_agent(
        policies={"atc_policy": ...},
        policy_mapping_fn=lambda agent_id, *a, **kw: "atc_policy",
    )
)

# 3. Build and Run
algo = config.build()
algo.train()
