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


def train(nn: nn.Module,
          train_dataloder: list,
          test_dataloder: list,
          epochs: int,
          criterion,
          optimiser,
          lr_scheduler,
          verbose: bool
          ) -> tuple:
    """
    Training loop

    :param lr_scheduler:
    :param nn: nn.Module
            Torch nn class
    :param train_dataloder: list
            list containing tuple: (Tenosr(batch), Tensor(labels))
    :param test_dataloder: list
            list containing tuple: (Tenosr(batch), Tensor(labels))
    :param epochs: int
            number of epcchs to train on
    :param criterion:
            a torch loss function
    :param optimiser:
            a torch optimiser
    :param verbose:
    :param lr_scheduler:
    :return: history
    """

    device = ("cuda" if torch.cuda.is_available() else "cpu")
    nn.to(device)

    epoch_counter = []
    test_accuracy = []
    test_f1_score = []

    for epoch in range(epochs):

        epoch_counter.append(epoch + 1)
        running_loss = 0.0

        train_dataloder = tqdm(train_dataloder)

        nn.train()

        for data in train_dataloder:
            inputs, labels = data
            inputs = inputs.to(device)
            labels = labels.to(device)
            # zero the parameter gradients
            optimiser.zero_grad()
            # forward + backward + optimize
            outputs = nn(inputs.float())
            loss = criterion(outputs, labels)
            loss.backward()
            optimiser.step()
            lr_scheduler.step()
            running_loss += loss.item()

        # calcuate test accuracy
        correct = 0
        total = 0

        with torch.no_grad():
            test_loss = 0
            nn.eval()
            for data in test_dataloder:
                test_inputs, test_labels = data

                test_inputs = test_inputs.to(device)
                test_labels = test_labels.to(device)

                test_outputs = nn(test_inputs)
                test_loss += criterion(test_outputs, test_labels).item()

                _, predicted = torch.max(test_outputs.data, 1)
                total += test_labels.size(0)
                correct += (predicted == test_labels).sum().item()

        test_accuracy_item = 100 * (correct / total)
        test_f1_score_item = f1_score(test_labels, predicted, average = 'weighted')
        if verbose:
            print(
                '\nEpoch [{}/{}] | Train Loss: {:.2f} | Test Loss {:.2f} | Test Accuracy: {:.2f}% | Test F1 Score: {:.2f}'.format(
                    epoch + 1,
                    epochs,
                    running_loss,
                    test_loss,
                    test_accuracy_item,
                    test_f1_score_item))
        test_accuracy.append(test_accuracy_item)
        test_f1_score.append(test_f1_score_item)

    history = (epoch_counter, test_accuracy, test_f1_score)

    return history
