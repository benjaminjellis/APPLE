"""
API to use APPLE
"""

from core.train import Train
from core.predict import Predict
from core.miners import user_file_overwrite_check
from core.cleanup import Cleanup
from core.backtest import Backtest
from core.loaders import load_json_or_csv
import pandas as pd
import os
from termcolor import colored
from pathlib import Path


class APPLE(object):

    def __init__(self, fixtures_to_predict, data_for_predictions, job_name):
        """
        :param fixtures_to_predict: str
                filepath of the file that contains the fixtures you want to predict
        :param data_for_predictions: str
                filepath for the data a model will use for predictions
        :param job_name: str
                name / ID of the job, this will determine the name of the output directory
        """
        # define path for making dirs and navigating
        self.path = str(Path().absolute())

        fixtures_to_predict = self.path + "/" + fixtures_to_predict
        data_for_predictions = self.path + "/" + data_for_predictions
        # load in the fixtures to predict, these are also user predictions
        self.fixtures_to_predict = load_json_or_csv(filepath = fixtures_to_predict)

        # load in the data to use to make predictions
        data_for_predictions_to_merge = load_json_or_csv(filepath = data_for_predictions)

        # extract data for predictions from mined data by checking which fixtures
        # to predict
        fixtures_to_predict = self.fixtures_to_predict[["HomeTeam", "AwayTeam", "Week"]]
        self.fixtures_and_data_for_prediction = fixtures_to_predict.merge(data_for_predictions_to_merge, how = "inner")

        # results directory
        self.results_dir = self.path + "/results/20_21/"

        if not os.path.exists(self.results_dir):
            os.mkdir(self.results_dir)

        self.job_result_dir = self.results_dir + "/" + job_name + "/"
        if not os.path.exists(self.job_result_dir):
            os.mkdir(self.job_result_dir)

    def run(self):
        """
        Used to make predictions on data passed as instance
        :return: Nothing, produces predictions and outputs them to file
        """

        # train a model of all three 3 model types  on the latest data
        print(colored("Training models on new data....", "green"))
        Train(model_type = "model 1").train(epochs = 22, verbose = True)
        Train(model_type = "model 2").train(epochs = 22, verbose = True)
        Train(model_type = "model 3").train(epochs = 22, verbose = True)
        print(colored("Training completed", "green"))

        # interrogate the model log to pick the best models compiled thus far
        log_loc = self.path + "/saved_models/"
        log = pd.read_csv(log_loc + "model_log.csv")

        # sort, descending on test acc and grab the top performing model
        log = log.sort_values(by = "Test Acc", ascending = False)
        top = log[:1]

        # then grab model id
        models = top['Model ID'].to_list()

        # use the top performing saved model to predict the fixtures
        for model in models:
            print(colored("Using model No. " + str(model) + " for prediction", "yellow"))
            predicted_results = Predict(model_id = model).predict(
                fixtures_to_predict = self.fixtures_and_data_for_prediction)
            print(colored(predicted_results, "blue"))
            predictions_file_output_loc = self.job_result_dir + model + "_predicted_results.csv"
            if user_file_overwrite_check(predictions_file_output_loc):
                predicted_results.to_csv(predictions_file_output_loc, index_label = False, index = False)

    def backtest(self, data_to_backtest_on, ftrs = None):
        """
        :param ftrs: str
                filepath to full time results file, used to evaluate predictions
        :param data_to_backtest_on: list of str or str
                filepath of single data file or list of filepaths to data that will be used for backtesting
        :return:
        """
        back_tester = Backtest(data_to_backtest_on = data_to_backtest_on, ftrs = ftrs)
        back_tester.all()
        back_tester.commit_log_updates()

    def cleanup(self, upper_limit = None, prct_to_remove = None):
        # cleanup the saved_models dir
        Cleanup(upper_limit = upper_limit, prct_to_remove = prct_to_remove)
