from gymnasium.envs.registration import register

register(
    id='ATC-v0',
    entry_point='src.env.atc_env:ATCEnv',
)
