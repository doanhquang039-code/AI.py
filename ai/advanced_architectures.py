"""
Advanced Neural Architectures for Reinforcement Learning
Bao gồm: Transformer, Attention Mechanisms, Graph Neural Networks
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Optional
import math


# ============ TRANSFORMER FOR RL ============

class MultiHeadAttention(nn.Module):
    """Multi-Head Attention mechanism"""
    def __init__(self, d_model, num_heads, dropout=0.1):
        super().__init__()
        assert d_model % num_heads == 0
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(dropout)
        self.scale = math.sqrt(self.d_k)
    
    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)
        
        # Linear projections
        Q = self.W_q(query).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(value).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        
        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attention = F.softmax(scores, dim=-1)
        attention = self.dropout(attention)
        
        # Apply attention to values
        context = torch.matmul(attention, V)
        
        # Concatenate heads
        context = context.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        
        # Final linear projection
        output = self.W_o(context)
        
        return output, attention


class PositionalEncoding(nn.Module):
    """Positional encoding for sequence data"""
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        return x + self.pe[:, :x.size(1)]


class TransformerEncoderLayer(nn.Module):
    """Single Transformer encoder layer"""
    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()
        
        self.attention = MultiHeadAttention(d_model, num_heads, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model)
        )
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x, mask=None):
        # Multi-head attention
        attn_output, _ = self.attention(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_output))
        
        # Feed-forward
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))
        
        return x


class TransformerRL(nn.Module):
    """
    Transformer-based RL Agent
    Sử dụng attention để xử lý sequential observations
    """
    def __init__(self, state_dim, action_dim, d_model=256, num_heads=8, num_layers=6, d_ff=1024, dropout=0.1):
        super().__init__()
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.d_model = d_model
        
        # Input embedding
        self.input_embedding = nn.Linear(state_dim, d_model)
        self.positional_encoding = PositionalEncoding(d_model)
        
        # Transformer encoder
        self.encoder_layers = nn.ModuleList([
            TransformerEncoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        
        # Output heads
        self.value_head = nn.Linear(d_model, 1)
        self.policy_head = nn.Linear(d_model, action_dim)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, states, mask=None):
        """
        Args:
            states: (batch_size, seq_len, state_dim)
            mask: (batch_size, seq_len)
        """
        # Embed states
        x = self.input_embedding(states)
        x = self.positional_encoding(x)
        x = self.dropout(x)
        
        # Pass through transformer layers
        for layer in self.encoder_layers:
            x = layer(x, mask)
        
        # Get last hidden state
        last_hidden = x[:, -1, :]
        
        # Compute value and policy
        value = self.value_head(last_hidden)
        policy_logits = self.policy_head(last_hidden)
        
        return policy_logits, value
    
    def get_action(self, states, mask=None):
        """Get action from policy"""
        policy_logits, value = self.forward(states, mask)
        probs = F.softmax(policy_logits, dim=-1)
        action = torch.multinomial(probs, 1)
        return action, probs, value


# ============ ATTENTION MECHANISMS ============

class SelfAttention(nn.Module):
    """Self-attention layer"""
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.query = nn.Linear(input_dim, hidden_dim)
        self.key = nn.Linear(input_dim, hidden_dim)
        self.value = nn.Linear(input_dim, hidden_dim)
        self.scale = math.sqrt(hidden_dim)
    
    def forward(self, x):
        Q = self.query(x)
        K = self.key(x)
        V = self.value(x)
        
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale
        attention = F.softmax(scores, dim=-1)
        
        output = torch.matmul(attention, V)
        return output, attention


class AttentionAgent(nn.Module):
    """
    RL Agent with Attention mechanism
    Tập trung vào các phần quan trọng của state
    """
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super().__init__()
        
        self.state_encoder = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        self.attention = SelfAttention(hidden_dim, hidden_dim)
        
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
        
        self.value_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self, state):
        # Encode state
        encoded = self.state_encoder(state)
        
        # Apply attention
        if len(encoded.shape) == 2:
            encoded = encoded.unsqueeze(1)
        
        attended, attention_weights = self.attention(encoded)
        attended = attended.squeeze(1)
        
        # Compute policy and value
        policy_logits = self.policy_head(attended)
        value = self.value_head(attended)
        
        return policy_logits, value, attention_weights


# ============ GRAPH NEURAL NETWORKS ============

class GraphConvolution(nn.Module):
    """Graph Convolutional Layer"""
    def __init__(self, in_features, out_features):
        super().__init__()
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        self.bias = nn.Parameter(torch.FloatTensor(out_features))
        self.reset_parameters()
    
    def reset_parameters(self):
        stdv = 1. / math.sqrt(self.weight.size(1))
        self.weight.data.uniform_(-stdv, stdv)
        self.bias.data.uniform_(-stdv, stdv)
    
    def forward(self, x, adj):
        """
        Args:
            x: Node features (num_nodes, in_features)
            adj: Adjacency matrix (num_nodes, num_nodes)
        """
        support = torch.mm(x, self.weight)
        output = torch.mm(adj, support)
        return output + self.bias


class GNNAgent(nn.Module):
    """
    Graph Neural Network for RL
    Xử lý structured state spaces (graphs)
    """
    def __init__(self, node_features, action_dim, hidden_dim=256, num_layers=3):
        super().__init__()
        
        self.num_layers = num_layers
        
        # GCN layers
        self.gcn_layers = nn.ModuleList()
        self.gcn_layers.append(GraphConvolution(node_features, hidden_dim))
        
        for _ in range(num_layers - 1):
            self.gcn_layers.append(GraphConvolution(hidden_dim, hidden_dim))
        
        # Readout layer (aggregate node features)
        self.readout = nn.Linear(hidden_dim, hidden_dim)
        
        # Policy and value heads
        self.policy_head = nn.Linear(hidden_dim, action_dim)
        self.value_head = nn.Linear(hidden_dim, 1)
    
    def forward(self, node_features, adjacency_matrix):
        """
        Args:
            node_features: (num_nodes, node_features)
            adjacency_matrix: (num_nodes, num_nodes)
        """
        x = node_features
        
        # Apply GCN layers
        for i, gcn in enumerate(self.gcn_layers):
            x = gcn(x, adjacency_matrix)
            if i < self.num_layers - 1:
                x = F.relu(x)
        
        # Global pooling (mean)
        graph_embedding = torch.mean(x, dim=0)
        graph_embedding = F.relu(self.readout(graph_embedding))
        
        # Compute policy and value
        policy_logits = self.policy_head(graph_embedding)
        value = self.value_head(graph_embedding)
        
        return policy_logits, value


# ============ RELATIONAL NETWORKS ============

class RelationalModule(nn.Module):
    """Relational reasoning module"""
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        
        self.g_theta = nn.Sequential(
            nn.Linear(input_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        self.f_phi = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
    
    def forward(self, objects):
        """
        Args:
            objects: (batch_size, num_objects, object_dim)
        """
        batch_size, num_objects, object_dim = objects.shape
        
        # Compute pairwise relations
        relations = []
        for i in range(num_objects):
            for j in range(num_objects):
                if i != j:
                    pair = torch.cat([objects[:, i], objects[:, j]], dim=-1)
                    relation = self.g_theta(pair)
                    relations.append(relation)
        
        # Aggregate relations
        relations = torch.stack(relations, dim=1)
        aggregated = torch.sum(relations, dim=1)
        
        # Final processing
        output = self.f_phi(aggregated)
        
        return output


class RelationalAgent(nn.Module):
    """
    Relational RL Agent
    Học relationships giữa các objects trong environment
    """
    def __init__(self, object_dim, num_objects, action_dim, hidden_dim=256):
        super().__init__()
        
        self.object_encoder = nn.Sequential(
            nn.Linear(object_dim, hidden_dim),
            nn.ReLU()
        )
        
        self.relational_module = RelationalModule(hidden_dim, hidden_dim)
        
        self.policy_head = nn.Linear(hidden_dim, action_dim)
        self.value_head = nn.Linear(hidden_dim, 1)
    
    def forward(self, objects):
        """
        Args:
            objects: (batch_size, num_objects, object_dim)
        """
        # Encode objects
        batch_size, num_objects, object_dim = objects.shape
        objects_flat = objects.view(-1, object_dim)
        encoded = self.object_encoder(objects_flat)
        encoded = encoded.view(batch_size, num_objects, -1)
        
        # Relational reasoning
        relational_output = self.relational_module(encoded)
        
        # Compute policy and value
        policy_logits = self.policy_head(relational_output)
        value = self.value_head(relational_output)
        
        return policy_logits, value


# ============ TESTING ============

if __name__ == "__main__":
    print("🧠 Testing Advanced Neural Architectures\n")
    
    # Test Transformer
    print("1. Testing Transformer RL Agent...")
    batch_size, seq_len, state_dim, action_dim = 4, 10, 8, 4
    transformer = TransformerRL(state_dim, action_dim, d_model=64, num_heads=4, num_layers=2)
    
    states = torch.randn(batch_size, seq_len, state_dim)
    policy_logits, value = transformer(states)
    
    print(f"   Input shape: {states.shape}")
    print(f"   Policy logits shape: {policy_logits.shape}")
    print(f"   Value shape: {value.shape}")
    print(f"   ✅ Transformer working\n")
    
    # Test Attention Agent
    print("2. Testing Attention Agent...")
    attention_agent = AttentionAgent(state_dim, action_dim, hidden_dim=64)
    
    state = torch.randn(batch_size, state_dim)
    policy_logits, value, attention = attention_agent(state)
    
    print(f"   Input shape: {state.shape}")
    print(f"   Policy logits shape: {policy_logits.shape}")
    print(f"   Attention shape: {attention.shape}")
    print(f"   ✅ Attention Agent working\n")
    
    # Test GNN Agent
    print("3. Testing GNN Agent...")
    num_nodes, node_features = 5, 8
    gnn_agent = GNNAgent(node_features, action_dim, hidden_dim=64, num_layers=2)
    
    nodes = torch.randn(num_nodes, node_features)
    adj = torch.rand(num_nodes, num_nodes)
    adj = (adj + adj.t()) / 2  # Make symmetric
    
    policy_logits, value = gnn_agent(nodes, adj)
    
    print(f"   Node features shape: {nodes.shape}")
    print(f"   Adjacency matrix shape: {adj.shape}")
    print(f"   Policy logits shape: {policy_logits.shape}")
    print(f"   ✅ GNN Agent working\n")
    
    # Test Relational Agent
    print("4. Testing Relational Agent...")
    num_objects, object_dim = 6, 8
    relational_agent = RelationalAgent(object_dim, num_objects, action_dim, hidden_dim=64)
    
    objects = torch.randn(batch_size, num_objects, object_dim)
    policy_logits, value = relational_agent(objects)
    
    print(f"   Objects shape: {objects.shape}")
    print(f"   Policy logits shape: {policy_logits.shape}")
    print(f"   ✅ Relational Agent working\n")
    
    print("✅ All Advanced Architectures tested successfully!")
    
    # Count parameters
    print("\n📊 Model Statistics:")
    print(f"   Transformer: {sum(p.numel() for p in transformer.parameters()):,} parameters")
    print(f"   Attention Agent: {sum(p.numel() for p in attention_agent.parameters()):,} parameters")
    print(f"   GNN Agent: {sum(p.numel() for p in gnn_agent.parameters()):,} parameters")
    print(f"   Relational Agent: {sum(p.numel() for p in relational_agent.parameters()):,} parameters")
