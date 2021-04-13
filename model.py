import torch 
import torch.nn as nn
import torch.nn.functional as F

# Code copied from: https://github.com/kilianFatras/variance_reduced_neural_networks/blob/master/SAGA.ipynb
class CNN(nn.Module):
    def __init__(self, ):
        super(CNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        '''
        arg : neural net, data
        goal : predict x's classification
        return : classification
        '''
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 16 * 5 * 5)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

# Code copied from: https://github.com/kilianFatras/variance_reduced_neural_networks/blob/master/SAGA.ipynb
class MLP(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(MLP, self).__init__()
        self.fc1 = nn.Linear(input_dim, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, output_dim)

    def forward(self, x):
        '''
        arg : neural net, data
        goal : predict x's classification
        return : classification
        '''
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

class RNN(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers=2):
        super(RNN, self).__init__()
        self.rnn = nn.rnn(input_dim, hidden_dim, num_layers)
        self.fc1 = nn.Linear(hidden_dim, 10)

    def forward(self, x):
        x, _ = self.rnn(x)
        x = F.relu(self.fc1(x))
        return x