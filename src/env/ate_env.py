import gymnasium as gym
import numpy as np

class ATCEnv(gym.Env):
    """
    Custom Environment for Multi-Agent Air Traffic Control
    """
    def __init__(self, blue_sky_connection):
        super(ATCEnv, self).__init__()
        self.bs = blue_sky_connection
        
        # Action Space: [Heading Change, Speed Change, Altitude Change]
        # Discrete or Continuous depending on your RL choice
        self.action_space = gym.spaces.Box(low=-1, high=1, shape=(3,), dtype=np.float32)
        
        # Observation Space: Local radar, own flight data, neighbors' data
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(N_FEATURES,), dtype=np.float32)

    def reset(self, seed=None):
        # Reset BlueSky simulator to initial scenario state
        self.bs.reset()
        return self._get_obs(), {}

    def step(self, action):
        # 1. Apply Action to simulator
        self.bs.apply_control(action)
        
        # 2. Step Simulator forward
        self.bs.step()
        
        # 3. Calculate Reward
        reward = self._calculate_reward()
        
        # 4. Check Termination/Safety
        terminated, truncated = self._check_safety_limits()
        
        return self._get_obs(), reward, terminated, truncated, {}

    def _get_obs(self):
        # Extract features for GNN nodes
        # Raw Data -> Normalized Tensors
        pass
