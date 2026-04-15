from ray.rllib.algorithms.ppo import PPOConfig
from src.env.atc_env import ATCEnv

config = (
    PPOConfig()
    .environment(ATCEnv)
    .multi_agent(
        policies={"atc_policy"},
        policy_mapping_fn=lambda agent_id, *args, **kwargs: "atc_policy"
    )
    .training(model={"custom_model": "GNN_LSTM_Brain"})
)

algo = config.build()

for i in range(100):
    result = algo.train()
    print(f"Iteration {i}: Mean Reward: {result['episode_reward_mean']}")
