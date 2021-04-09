import torch
import pandas as pd
from torch import nn
from tqdm import tqdm
from torch import optim
import basic_sag
import basic_saga
import basic_sgd
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import Dataset, DataLoader

from neural_network import Network


class TitanicDataset(Dataset):

    def __init__(self, csvpath, mode='train'):
        self.mode = mode
        df = pd.read_csv(csvpath)
        """       
        <------Some Data Preprocessing---------->
        Removing Null Values, Outliers and Encoding the categorical labels etc
        """
        if self.mode == 'train':
            df['Sex'] = LabelEncoder().fit_transform(df['Sex'])
            df['Ticket'] = LabelEncoder().fit_transform(df['Ticket'])
            df['Cabin'] = LabelEncoder().fit_transform(df['Cabin'])
            df['Embarked'] = LabelEncoder().fit_transform(df['Embarked'])
            df = df.drop('Name', 1)
            df = df.fillna(0)
            print(df.dtypes)
            self.inp = df.iloc[:, 2:].values
            self.oup = df.iloc[:, 1].values.reshape(891, 1)
        else:
            self.inp = df.values

    def __len__(self):
        return len(self.inp)

    def __getitem__(self, idx):
        if self.mode == 'train':
            inpt = torch.Tensor(self.inp[idx])
            oupt = torch.Tensor(self.oup[idx])
            return {'inp': inpt, 'oup': oupt}
        else:
            inpt = torch.Tensor(self.inp[idx])
        return {'inp': inpt}


def train(model, x, y, optimizer, criterion):
    model.zero_grad()
    output = model(x)
    loss = criterion(output, y)
    loss.backward()
    optimizer.step()
    return loss, output


net = Network()

EPOCHS = 200
BATCH_SIZE = 1
data = TitanicDataset('data/train.csv')
data_train = DataLoader(dataset=data, batch_size=BATCH_SIZE, shuffle=False)

criterion = nn.MSELoss()
# optm = optim.Adam(net.parameters(), lr=0.01)
# optm = optim.SGD(net.parameters(), lr=0.01)
# optm = basic_sgd.SGD(net.parameters(), use_numba=False, lr=0.01)
# optm = basic_sag.SAG(net.parameters(), N=data.inp.shape[0], use_numba=False, lr=0.01)
optm = basic_saga.SAGA(net.parameters(), N=data.inp.shape[0], use_numba=False, lr=0.01)

for epoch in range(EPOCHS):
    epoch_loss = 0
    correct = 0
    for bidx, batch in tqdm(enumerate(data_train)):
        x_train, y_train = batch['inp'], batch['oup']
        x_train = x_train.view(-1, 9)
        loss, predictions = train(net, x_train, y_train, optm, criterion)
        for idx, i in enumerate(predictions):
            i = torch.round(i)
            if i == y_train[idx]:
                correct += 1
        acc = (correct/len(data))
        epoch_loss += loss
    print('Epoch {} Accuracy : {}'.format(epoch+1, acc*100))
    print('Epoch {} Loss : {}'.format((epoch+1), epoch_loss))