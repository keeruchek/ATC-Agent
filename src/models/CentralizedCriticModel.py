class CentralizedCriticModel(TorchModelV2, nn.Module):
    def __init__(self, *args, **kwargs):
        # 1. Define Actor (Local observation input)
        self.actor = GNN_Encoder(...) 
        
        # 2. Define Critic (Global observation input)
        self.critic = MLP(input_dim=global_state_dim, ...)

    def forward(self, input_dict, state, seq_lens):
        # During training, RLlib provides global state in 'obs'
        # Actor branch uses the local part of the observation
        # Critic branch uses the full global state
        ...
