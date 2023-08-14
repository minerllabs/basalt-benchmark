import torch as th

from stable_baselines3.common import policies

class NLayerFeedForwardPolicy(policies.ActorCriticPolicy):
    """Simple feedforward policy with n hidden layers of size hidden_dim"""
    def __init__(self, n_layers, hidden_dim, *args, **kwargs):
        super().__init__(*args, **kwargs, net_arch=[hidden_dim for _ in range(n_layers)])

def build_n_layer_mlp_policy(observation_space, action_space, hidden_dim, n_layers):
    return NLayerFeedForwardPolicy(
        observation_space=observation_space,
        action_space=action_space,
        hidden_dim=hidden_dim,
        n_layers=n_layers,
        # This trick is in imitation library for bc
        lr_schedule=lambda _: th.finfo(th.float32).max,
    )


def build_two_layer_mlp_policy(observation_space, action_space, hidden_dim):
    return build_n_layer_mlp_policy(observation_space, action_space, hidden_dim, n_layers=2)