"""
Script used to train models on new data, back-test saved models, and predict upcoming fixtures
"""

from core.train import Train
from core.predict import Predict
from core.miners import user_file_overwrite_check
from core.cleanup import Cleanup
import pandas as pd
import os
from termcolor import colored
from pathlib import Path


def load(filepath):
    """
    Def to load eitheir csv or json
    :param filepath: str
            filepath of file to load
    :return: a dataframe of the file pointed to in filepath
    """
    name, file_extension = filepath.split(".")
    if file_extension == "csv":
        loaded_file = pd.read_csv(filepath)
    elif file_extension == "json":
        loaded_file = pd.read_json(filepath)
    else:
        raise Exception("File format " + file_extension + " not supported for mined data to predict")
    return loaded_file


class WeeklyBatch(object):

    def __init__(self, fixtures_to_predict, data_for_predictions, job_name):
        """
        :param fixtures_to_predict: str
                filepath of the file that contaions the fixtures you want to predict
        :param data_for_predictions: str
                filepath for the data the model will use for predictions
        :param job_name: str
                name / ID of the job, this will determine the name of the output dir
        """
        # define path for making dirs and navigating
        self.path = str(Path().absolute())

        fixtures_to_predict = self.path + "/" + fixtures_to_predict
        data_for_predictions = self.path + "/" + data_for_predictions
        # load in the fixtures to predict, these are also user predictions
        self.fixtures_to_predict = load(filepath = fixtures_to_predict)

        # load in the data to use to make predictions
        data_for_predictions_to_merge = load(filepath = data_for_predictions)

        # extract data for predictions from mined data by checking which fixtures
        # to predict
        fixtures_to_predict = self.fixtures_to_predict[["HomeTeam", "AwayTeam", "Week"]]
        self.fixtures_and_data_for_prediction = fixtures_to_predict.merge(data_for_predictions_to_merge, how = "inner")

        # results directory
        self.results_dir = self.path + "/Results/"

        if not os.path.exists(self.results_dir):
            os.mkdir(self.results_dir)

        self.job_result_dir = self.results_dir + "/" + job_name + "/"
        if not os.path.exists(self.job_result_dir):
            os.mkdir(self.job_result_dir)

    def run(self, backtest = True, cleanup = True, upper_limit = None, prct_to_remove = None):
        """
        :param prct_to_remove:
        :param upper_limit:
        :param backtest: boolean
                Whether or not to run backtest of all saved models on new data
        :param cleanup: boolean
                Whether or not to
        :return:
        """
        # train a model of all three 3 model types  on the latest data
        print(colored("Training models on new data....", "green"))
        Train(model_type = "model 1").train(epochs = 22, verbose = True)
        Train(model_type = "model 2").train(epochs = 22, verbose = True)
        Train(model_type = "model 3").train(epochs = 22, verbose = True)
        print(colored("Training completed", "green"))

        # no backtesting for the moment, needs to be rewritten
        """
        if backtest:
            # back test all saved models on new data
            back_tester = Backtest(week = week_number)
            back_tester.all()
            back_tester.commit_log_updates()
        """

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

        if cleanup:
            # cleanup the saved_models dir
            Cleanup(upper_limit = upper_limit, prct_to_remove = prct_to_remove)
