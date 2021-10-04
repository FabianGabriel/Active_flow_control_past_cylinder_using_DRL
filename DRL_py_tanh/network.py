"""
	This file contains a neural network module for us to
	define our actor and critic networks in PPO.

	called in main.py
"""

import torch
from torch import nn
import torch.nn.functional as F

torch.set_default_tensor_type(torch.DoubleTensor)


class FCCA(nn.Module):
    """
        A standard in_dim-64-64-out_dim Feed Forward Neural Network for policy model(Actor).
    """

    def __init__(self, input_dim, hidden_dims, action_bounds):
        """
        The output layer dimensions are 2 neurons. 1st neuron in output layer represents mean value
        and 2nd neuron in output layer represents std value.

        Args:
            input_dim: input dimensions are equal to number of pressure sensors
                        sensors -> p values of patches at surface of cylinder.
            hidden_dims: 64x64
            activation_fc: neuron activation function = relu -> torch,nn.functional.F.relu
        """
        super(FCCA, self).__init__()
        self.linear_0 = torch.nn.Linear(input_dim, hidden_dims)
        self.linear_1 = torch.nn.Linear(hidden_dims, hidden_dims)
        self.linear_2 = torch.nn.Linear(hidden_dims, 2)
        self.env_min, self.env_max = action_bounds
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda:0"
        self.device = torch.device(device)
        self.env_min = torch.tensor(self.env_min,
                                    device=self.device, 
                                    dtype=torch.float32)

        self.env_max = torch.tensor(self.env_max,
                                    device=self.device, 
                                    dtype=torch.float32)
        self.nn_min = F.tanh(torch.Tensor([float('-inf')])).to(self.device)
        self.nn_max = F.tanh(torch.Tensor([float('inf')])).to(self.device)
        self.rescale_fn = lambda x: (x - self.nn_min) * (self.env_max - self.env_min) / \
                                    (self.nn_max - self.nn_min) + self.env_min
        self.descale_fn = lambda x: (x - self.env_min) * (self.nn_max - self.nn_min) / (self.env_max - self.env_min) + self.nn_min

    def forward(self, x):
        """
        Feed forwarding in NN net

        Args:
            x: array or tensor containing value of pressure of patches at the surface of cylinder
                    must be (n_sensors x 1) dimensions.

        Returns:
            x_mean: mean value from 1st neuron of output layer, mean value of taken action.
            x_std: std value from 2nd neuron of output layer, std value of taken action.

        """
        # feed forwards to layers
        x = F.relu(self.linear_0(x))
        x = F.relu(self.linear_1(x))
        return self.linear_2(x)

    @torch.jit.ignore
    def get_predictions(self, states, actions):
        """
        To compute log probability of taken action and entropy of taken action from the distribution.

        Args:
            states: input array, pressure array
            actions: action array

        Returns: tensors of log probability and tensor of entropy

        """

        # get mean and std of action for the supplied state
        output_layer = self.forward(torch.from_numpy(states))
        mean_ac, std_ac = output_layer[:, :, 0], output_layer[:, :, 1]
        mean_ac = mean_ac.squeeze()
        std_ac = std_ac.squeeze()
        # get distribution from mean and std by feed forward
        dist = torch.distributions.Normal(mean_ac, std_ac.exp())
        d_actions = self.descale_fn(torch.from_numpy(actions))
        atanh_d_actions = torch.atanh(d_actions)
        # compute log probabilities and entropy
        logpas = dist.log_prob(atanh_d_actions) - torch.log((1 - d_actions.pow(2)).clamp(0, 1) + 0.000001)
        entropies = dist.entropy()

        return logpas, entropies


class FCV(nn.Module):
    """
        A standard in_dim-64-64-out_dim Feed Forward Neural Network for value model(Critic).
    """

    def __init__(self, input_dim, hidden_dims):
        """
        The output layer dimensions are 1 neuron. The neuron in output layer represents value of the state.

        Args:
            input_dim: input dimensions are equal to number of pressure sensors
                        sensors -> p values of patches at surface of cylinder.
            hidden_dims: 64x64
            activation_fc: neuron activation function = relu -> torch,nn.functional.F.relu
        """
        super(FCV, self).__init__()
        self.linear_0 = torch.nn.Linear(input_dim, hidden_dims)
        self.linear_1 = torch.nn.Linear(hidden_dims, hidden_dims)
        self.linear_2 = torch.nn.Linear(hidden_dims, 1)

    def forward(self, x):
        """
         Feed forwarding in NN net.

        Args:
            x: array or tensor containing value of pressure of patches at the surface of cylinder
                    must be (n_sensors x 1) dimensions.

        Returns: Tensor of an state value(value is pi_theta)

        """
        x = F.relu(self.linear_0(x))
        x = F.relu(self.linear_1(x))
        return self.linear_2(x)
