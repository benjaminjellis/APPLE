"""
Class to create and def to train PyTorch NeuralNetwork
"""
import torch
from torch import nn
from tqdm import tqdm
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score


seed = 42
torch.manual_seed(seed)


class NNet(nn.Module):
    def __init__(self):
        super(NNet, self).__init__()
        self.lin1 = nn.Linear(12, 10)
        self.lin2 = nn.Linear(10, 3)

    def forward(self, x):
        x = self.lin1(x)
        x = self.lin2(x)
        return x


def train(nn: nn.Module, train_tensor: list, test_tensor: list, epochs: int, criterion, optimiser, verbose: bool) -> tuple:
    """
    Training loop
    :param nn: nn.Module
            Torch nn class
    :param train_tensor: list
            list containing tuple: (Tenosr(batch), Tensor(labels))
    :param test_tensor: list
            list containing tuple: (Tenosr(batch), Tensor(labels))
    :param epochs: int
            number of epcchs to train on
    :param criterion:
            a torch loss function
    :param optimiser:
            a torch optimiser
    :return: history
    """

    epoch_counter = []
    test_accuracy = []
    test_f1_score = []

    for epoch in range(epochs):

        epoch_counter.append(epoch+1)
        running_loss = 0.0

        for data in tqdm(train_tensor):
            inputs, labels = data
            # zero the parameter gradients
            optimiser.zero_grad()
            # forward + backward + optimize
            outputs = nn(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimiser.step()
            running_loss += loss.item()

        # calcuate test accuracy
        correct = 0
        total = 0
        with torch.no_grad():
            for data in test_tensor:
                inputs, labels = data
                outputs = nn(inputs)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        if verbose:
            print('\nEpoch(s): {} | Accuracy: {}% | F1 Score: '.format(epoch + 1, 100 * correct / total), f1_score(labels, predicted, average='weighted'))
        test_accuracy.append(100 * correct / total)
        test_f1_score.append(f1_score(labels, predicted, average='weighted'))

    history = (epoch_counter, test_accuracy, test_f1_score)

    return history

