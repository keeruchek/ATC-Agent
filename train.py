# ATC-Agent/train.py
from ray.rllib.algorithms.ppo import PPOConfig
from src.env.atc_env import ATCEnv

config = (
    PPOConfig()
    .environment(ATCEnv)
    .multi_agent(
        policies={"atc_policy"},
        policy_mapping_fn=lambda agent_id, *args, **kwargs: "atc_policy"
    )
    .training(model={"custom_model": "my_gnn_lstm_model"})
)

algo = config.build()

# The training loop orchestrates the interaction
for i in range(100):
    result = algo.train()
    print(f"Iteration {i}: mean_reward={result['episode_reward_mean']}")
