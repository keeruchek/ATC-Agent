import gymnasium as gym
import numpy as np
import scipy.spatial as spatial

class ATCEnv(gym.Env):
    def __init__(self, config):
        self.max_dist = 50.0  # Interaction threshold
        self.observation_space = gym.spaces.Dict({
            "local_radar": gym.spaces.Box(-np.inf, np.inf, shape=(10,)),
            "adj_matrix": gym.spaces.Box(0, 1, shape=(20, 20)) # Max 20 planes
        })

    def _get_graph_data(self, positions):
        # Create Adjacency Matrix based on proximity
        dists = spatial.distance.cdist(positions, positions)
        adj = (dists < self.max_dist).astype(np.float32)
        return adj

    def step(self, action):
        # 1. Apply to BlueSky (Placeholder)
        # 2. Get new state
        # 3. Calculate Reward (Safety > Efficiency)
        reward = -1.0 # Base time penalty
        return obs, reward, False, False, {}
