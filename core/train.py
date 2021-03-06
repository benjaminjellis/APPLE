"""
Class used to train feed-forward MLP classifiers to make predictions
"""
from torch import nn, save
import torch.optim as optim

from core.nnet import NNet, train
import core.data_processing as dp

import pandas as pd
import urllib.request
import os
from datetime import date
import pathlib
from pathlib import Path
import uuid
from termcolor import colored
from http.client import RemoteDisconnected
from urllib.error import HTTPError

import warnings
from sklearn.exceptions import DataConversionWarning

warnings.filterwarnings(action = "ignore", category = DataConversionWarning)


class Train(object):

    def __init__(self):
        self.path = str(pathlib.Path().absolute())

        data_dir = self.path + "/data/raw/"

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # grab the latest data
        try:
            urllib.request.urlretrieve("http://www.football-data.co.uk/mmz4281/2021/E0.csv", data_dir + "2021.csv")
            urllib.request.urlretrieve("https://www.football-data.co.uk/mmz4281/1920/E0.csv", data_dir + "1920.csv")
            urllib.request.urlretrieve("https://www.football-data.co.uk/mmz4281/1819/E0.csv", data_dir + "1819.csv")
        except RemoteDisconnected:
            print(colored("Error connecting to remote when sourcing updated data, using data stored locally instead",
                          "red"))
        except HTTPError:
            print(colored("Error connecting to remote when sourcing updated data, using data stored locally instead",
                          "red"))

        raw_data_18_19 = pd.read_csv(data_dir + "1819.csv")
        raw_data_19_20 = pd.read_csv(data_dir + "1920.csv")
        raw_data_20_21 = pd.read_csv(data_dir + "2021.csv")

        self.raw_data_combined = dp.preprocessing(raw_data_19_20, raw_data_20_21, raw_data_18_19)

    def train(self, epochs: int, verbose: bool) -> None:
        """
        Method to train model
        :param epochs: int
                number of epochs to train model for
        :param verbose: boolean
                verbose outputs or not
        :return: nothing
        """

        # unique id to label model with
        model_id = uuid.uuid1()
        model_id = str(model_id)

        # directory to output the model to, as well as various other files
        model_output_dir = self.path + "/saved_models/" + model_id + "/"
        if not os.path.exists(model_output_dir):
            os.makedirs(model_output_dir)

        # process and split the data, coeffs used to scale the data
        train_dataloader, test_dataloder, ord_cols_df, coeffs = dp.processing(input_df = self.raw_data_combined,
                                                                              test_size = 0.2,
                                                                              train_batch_size = 5)
        lr = 0.001
        # create a neural net
        net = NNet()
        # loss function
        criterion = nn.CrossEntropyLoss()
        # optimiser
        optimiser = optim.AdamW(net.parameters(), lr = lr, weight_decay = 0.001)
        # lr scheduler
        lr_scheduler = optim.lr_scheduler.OneCycleLR(optimizer = optimiser,
                                                     max_lr = lr,
                                                     epochs = epochs,
                                                     steps_per_epoch = len(train_dataloader))
        history = train(nn = net,
                        train_dataloder = train_dataloader,
                        test_dataloder = test_dataloder,
                        epochs = epochs,
                        criterion = criterion,
                        optimiser = optimiser,
                        lr_scheduler = lr_scheduler,
                        verbose = verbose)

        today = date.today().strftime("%Y%m%d")

        # output the model, the columns and scaler coeffs
        save(net.state_dict(), model_output_dir + model_id + ".pth")
        ord_cols_df.to_csv(model_output_dir + model_id + ".csv", index_label = False, index = False)
        coeffs.to_csv(model_output_dir + model_id + "_coeffs.csv", index_label = False, index = False)

        log_output = self.path + "/saved_models/model_log.csv"
        log_entry = {"Model ID": model_id, "Date": today,
                     "Test Acc": [history[1][-1]], "Test F1": [history[2][-1]]}

        # update the log with results of test of model
        try:
            log = pd.read_csv(log_output)
            log_update = pd.DataFrame(data = log_entry)
            log = pd.concat([log, log_update], ignore_index = True)
        except FileNotFoundError:
            Path(log_output).touch()
            log = pd.DataFrame(data = log_entry)

        log.to_csv(log_output, index = False, index_label = False)
