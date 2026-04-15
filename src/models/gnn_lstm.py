import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv

class GNN_LSTM_Brain(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.gnn = GCNConv(input_dim, hidden_dim)
        self.lstm = nn.LSTM(hidden_dim, hidden_dim, batch_first=True)
        self.actor = nn.Linear(hidden_dim, 3) # Heading, Speed, Alt

    def forward(self, obs, adj, hidden_state):
        x = self.gnn(obs, adj)
        x, new_hidden = self.lstm(x.unsqueeze(0), hidden_state)
        return self.actor(x), new_hidden
