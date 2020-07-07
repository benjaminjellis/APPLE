"""
Backtest is a class used to backtest and thus evaluate saved models on new data.
Models are tested on a randomly selected 70% of 19/20 season data, the class then updates
the model log
"""


import tensorflow as tf
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from core.scaler import scale_df_with_params
from termcolor import colored
import numpy as np
pd.options.mode.chained_assignment = None  # default='warn'


def log_update(model_id, results, model_log):
    """
    Function used to update each model entry in the model log once the
    model has been backtested against new data
    :param model_id: str
            - uniqe model id to update log for
    :param results: tuple
            - tuple of length 2 with the test loss and test accuracy in that order
    :param model_log: dataframe
            - the model log as a dataframe to update
    :return: nothing
    """
    # get the row number for the model
    row = model_log[model_log['Model ID'] == model_id].index
    # update test loos
    model_log.at[row, "Test Loss"] = results[0]
    model_log.at[row, "Test Acc"] = results[1]


class Backtest(object):

    def __init__(self):
        """
        Constructor loads the model log and 19/20 season data, maps location of daved models
        """
        # load model log
        self.path = str(Path().absolute())
        self.model_log_loc = self.path + "/saved_models/"
        self.model_log_path = self.model_log_loc + "model_log.csv"
        self.model_log = pd.read_csv(self.model_log_path)
        # get location of saved models
        self.saved_models_dir = self.path + "/saved_models/"
        # load in data that's used to train / test the models just for the 19/20 season
        self.data_19_20 = pd.read_csv(self.path + "/data/raw/1920.csv")

    def model(self, model_id):
        """
        Method to backtest a single model
        :param model_id:  str
            - uniqe model id to backtest
        :return: nothing
        """
        print("Backtesting model " + str(model_id))
        # grab entry for requested model
        model_details = self.model_log[self.model_log["Model ID"] == model_id]
        # get model type for re
        model_type = int(model_details["Model type"].iloc[0])

        # load scaled
        sclaer_coeffs_loc = self.saved_models_dir + model_id + "/" + model_id + "_coeffs.csv"
        # grab the model
        loaded_model = tf.keras.models.load_model(self.saved_models_dir + model_id + "/" + model_id + ".h5")
        # load the expected features for the loaded model
        exp_features_df = pd.read_csv(self.saved_models_dir + model_id + "/" + model_id + ".csv")
        exp_features = exp_features_df["columns"].to_list()
        # add FTR to the list of expected features
        exp_features.append("FTR")
        rawdata = self.data_19_20

        # code below is replicated from predict.py, turn this into a def and use in both classes
        if model_type == 2 or model_type == 3:
            ats = pd.get_dummies(rawdata["AwayTeam"], prefix = "at")
            hts = pd.get_dummies(rawdata["HomeTeam"], prefix = "ht")
            rawdata = pd.concat([rawdata, ats], axis = 1, sort = False)
            rawdata = pd.concat([rawdata, hts], axis = 1, sort = False)

            rawdata.pop("AwayTeam")
            rawdata.pop("HomeTeam")
        # this block is also used in predict.py, this should be packed up into a function and stored
        # somewhere in core
        try:
            reduced_data = rawdata[exp_features]
        except KeyError:
            key_present = list(rawdata.columns)
            keys_missing = []

            for key in exp_features:
                if key not in key_present:
                    keys_missing.append(key)

            length = len(keys_missing)
            track = 0
            shape = rawdata.shape

            for keys in keys_missing:
                if keys[:2] == "at" or "ht":
                    track += 1

            print(colored("Attempting to deal with missing datapoint(s)....", 'red'))

            entry = np.zeros((shape[0], 1))

            if length == track:
                print(colored("Fixing input data....", 'red'))
                for key in keys_missing:
                    rawdata[key] = entry
                try:
                    reduced_data = rawdata[exp_features]
                    print(colored("Input data fixed", 'green'))
                except KeyError:
                    print(colored("ERROR - Missing datapoint(s): ", 'red'))
                    print(colored("Attempt was made to fix input data, but it wasn't possible", 'red'))

            else:
                print(colored("ERROR - input data cannot be handled", 'red'))
                print(
                    colored(model_id + " can't be used to make predicitons wihtout the above, datapoint(s)",
                            "red"))
                raise Exception

        # categorical encoding for FTR col
        result_cleanup = {"FTR": {"H": 0, "A": 1, "D": 2}}
        reduced_data.replace(result_cleanup, inplace = True)
        # split the 19/20 data
        data_not_used, backtesting_data = train_test_split(reduced_data, test_size = 0.7, shuffle = True)
        backtesting_data = backtesting_data[exp_features]

        # remove labels
        backtesting_data_labels = backtesting_data.pop("FTR")

        # scale the features
        backtesting_data = scale_df_with_params(backtesting_data, sclaer_coeffs_loc)

        # turn labels and features in numpy arrays for passing to model
        backtesting_data_labels = backtesting_data_labels.to_numpy()
        backtesting_data = backtesting_data.to_numpy()
        # use model to evaluate
        results = loaded_model.evaluate(backtesting_data, backtesting_data_labels, batch_size = 50)
        # now update the log with the results
        log_update(model_id = model_id, results = results, model_log = self.model_log)

    def models(self, models):
        """
        Method to backtest one of more models
        :param models: list of str
                - a list of models to backtest
        :return: nothing
        """
        for model in models:
            self.model(model_id = model)

    def all(self):
        """
        Method to backtest all models
        :return: nothing
        """
        # get all the mode ids as a list
        models = self.model_log["Model ID"].to_list()
        # perform back testing on all models
        for model in models:
            self.model(model_id = model)

    def commit_log_updates(self):
        """
        Method to commit log updates made by any instance to file
        :return: nothing
        """
        self.model_log.to_csv(self.model_log_path, index_label = False, index = False)
