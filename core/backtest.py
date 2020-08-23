"""
Backtest is a class used to backtest and thus evaluate saved models on data (mined_data) that is mined each week for predictions
The class then updates the model log with the backtesing results
"""

import tensorflow as tf
from pathlib import Path
import pandas as pd
from core.scaler import scale_df_with_params
from core.loaders import load_json_or_csv, load_or_aggregate
from core.data_processing import formatting_for_passing_to_model
from termcolor import colored
import numpy as np

pd.options.mode.chained_assignment = None  # default='warn'


def log_update(model_id, results, model_log):
    """
    Function used to update each model entry in the model log once the
    model has been backtested against new data
    :param model_id: str
            uniqe model id to update log for
    :param results: tuple
            tuple of length 2 with the test loss and test accuracy in that order
    :param model_log: dataframe
            the model log as a dataframe to update
    :return: nothing
    """
    # get the row number for the model
    row = model_log[model_log['Model ID'] == model_id].index
    # update test loos
    model_log.at[row, "Test Loss"] = results[0]
    model_log.at[row, "Test Acc"] = results[1]


class Backtest(object):

    def __init__(self, data_to_backtest_on, ftrs = None):
        """
        Constructor loads the model log, aggregates data to make backtesting dataset, maps locations of saved models
        """
        # load model log
        self.path = str(Path().absolute())
        # location of saved models
        self.saved_models_dir = self.path + "/saved_models/"
        self.model_log_loc = self.saved_models_dir + "model_log.csv"
        self.model_log = load_json_or_csv(self.model_log_loc)

        # load and aggregate all backtesting data to be used
        mined_data_aggregated = load_or_aggregate(data_to_backtest_on)

        if ftrs is not None:
            # load and aggreate all ftrs
            ftrs_aggregated = load_or_aggregate(ftrs)
            self.raw_backtesting_data = pd.merge(mined_data_aggregated, ftrs_aggregated, on = ["HomeTeam", "AwayTeam"])
        else:
            self.raw_backtesting_data = mined_data_aggregated
        # check here if the FTRs are provided

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
        # get model type for requested model
        model_type = int(model_details["Model type"].iloc[0])

        # load scaled
        sclaer_coeffs_loc = self.saved_models_dir + model_id + "/" + model_id + "_coeffs.csv"
        # grab the model
        loaded_model = tf.keras.models.load_model(self.saved_models_dir + model_id + "/" + model_id + ".h5")
        exp_features_df = pd.read_csv(self.saved_models_dir + model_id + "/" + model_id + ".csv")
        exp_features = exp_features_df["columns"].to_list()

        # add FTR to the list of expected features
        exp_features.append("FTR")
        rawdata = self.raw_backtesting_data

        # code below is replicated from predict.py, turn this into a def and use in both classes
        if model_type == 2 or model_type == 3:
            ats = pd.get_dummies(rawdata["AwayTeam"], prefix = "at")
            hts = pd.get_dummies(rawdata["HomeTeam"], prefix = "ht")
            rawdata = pd.concat([rawdata, ats], axis = 1, sort = False)
            rawdata = pd.concat([rawdata, hts], axis = 1, sort = False)

            rawdata.pop("AwayTeam")
            rawdata.pop("HomeTeam")

        backtesting_data = formatting_for_passing_to_model(rawdata = rawdata, exp_features = exp_features, model_id = model_id)

        # categorical encoding for FTR col
        result_cleanup = {"FTR": {"H": 0, "A": 1, "D": 2}}
        backtesting_data.replace(result_cleanup, inplace = True)

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
        self.model_log.to_csv(self.model_log_loc, index_label = False, index = False)
