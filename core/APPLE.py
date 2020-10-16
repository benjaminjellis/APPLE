"""
APPLE API
"""

from core.train import Train
from core.predict import Predict
from core.miners import user_file_overwrite_check
from core.cleanup import cleanup
from core.backtest import Backtest
from core.loaders import load_json_or_csv
from core.strudel_interface import StrudelInterface
from core.data_processing import team_name_standardisation, clean_mined_data
import pandas as pd
import os
from termcolor import colored
from pathlib import Path


class APPLE(object):

    def __init__(self, use_strudel: bool, fixtures_to_predict: str, data_for_predictions: str, job_name: str, week: int, start_date: str = None, end_date: str = None):
        """
        Constructor loads file into memory, creates file paths, results directories and merges data and fixtures file
        :param use_strudel: bool
                whether to get fixtures to predict from STRUDEL or not
        :param fixtures_to_predict: str
                filepath of the file that contains the fixtures to predict, or if using STRUDEL the filepath where
                obtained user predictions are saved
        :param data_for_predictions: str
                filepath for the data a model will use for predictions, file should be json or csv
        :param job_name: str
                name / ID of the job, this will determine the name of the output directory
        :param week: int
                week number
        :param start_date: str
                OPTIONAL, required if use_strudel is TRUE
                Date in ISO format, YYYY-MM-DD, for the start date of fixtures window
        :param end_date: str
                OPTIONAL, required if use_strudel is TRUE
                Date in ISO format, YYYY-MM-DD, for the end date of fixtures window
        """
        # define path for making dirs and navigating
        self.path = str(Path().absolute())
        fixtures_to_predict = self.path + "/" + fixtures_to_predict
        data_for_predictions = self.path + "/" + data_for_predictions

        if use_strudel:
            # import user predictions from STRUDEL
            if start_date is None or end_date is None:
                # check that start_date and end_date are specified
                raise ValueError("Using STRUDEL to get user predictions requires start_date and end_date to be specified")
            else:
                strudel_connection = StrudelInterface(credentials_filepath = self.path + '/credentials/credentials.json')
                strudel_connection.get_fixtures_and_user_predictions(start_date = start_date,
                                                                     end_date = end_date,
                                                                     week = week,
                                                                     output_loc = fixtures_to_predict)

        # load in the fixtures to predict, these are also user predictions
        self.fixtures_to_predict = load_json_or_csv(filepath = fixtures_to_predict)

        # load in the data to use to make predictions
        data_for_predictions_to_merge = load_json_or_csv(filepath = data_for_predictions)

        # clean data_for_predictions_to_merge
        data_for_predictions_to_merge = clean_mined_data(data_for_predictions_to_merge)

        # extract data for predictions from mined data by checking which fixtures
        # to predict
        fixtures_to_predict = self.fixtures_to_predict[["HomeTeam", "AwayTeam", "Week"]]
        # standardise team names to make sure merge happens correctly
        fixtures_to_predict["HomeTeam"] = fixtures_to_predict.apply(lambda x: team_name_standardisation(x["HomeTeam"]),
                                                                    axis = 1)
        fixtures_to_predict["AwayTeam"] = fixtures_to_predict.apply(lambda x: team_name_standardisation(x["AwayTeam"]),
                                                                    axis = 1)
        # merge the fixtures and data
        self.fixtures_and_data_for_prediction = fixtures_to_predict.merge(data_for_predictions_to_merge, how = "inner")

        # results directory
        self.results_dir = self.path + "/results/20_21/"
        if not os.path.exists(self.results_dir):
            os.mkdir(self.results_dir)

        # output files directory
        self.job_result_dir = self.results_dir + "/" + job_name + "/"
        if not os.path.exists(self.job_result_dir):
            os.mkdir(self.job_result_dir)

        # private variables
        self._data_to_backtest_on = None
        self._ftrs = None
        self._upper_limit = None
        self._prct_to_remove = None

    def run(self):
        """
        Method to make predictions on passed data
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

    def backtest(self, data_to_backtest_on: list, ftrs: str = None):
        """
        Method to backtest all models on specified data
        :param data_to_backtest_on: list of str or str
                Filepath of single data file or list of filepaths to data that will be used for backtesting
        :param ftrs: str
                OPTIONAL - required if FTRs are not present in data_to_backtest_on
                Filepath to full time results file, used to evaluate predictions
        :return: nothing
        """
        self._data_to_backtest_on = data_to_backtest_on
        self._ftrs = ftrs

        back_tester = Backtest(data_to_backtest_on = data_to_backtest_on, ftrs = ftrs)
        back_tester.all()
        back_tester.commit_log_updates()

    def cleanup(self, upper_limit: int = None, prct_to_remove: int = None):
        """
        Method to clean up saved models directory
        :param upper_limit: int
                OPTIONAL
                Threshold number of models to retain. Once this value is exceeded this method will start to
                delete the lowest performing models. Default and minimum value is 15.
        :param prct_to_remove: int
                OPTIONAL
                Percentage of models to remove. Once upper_limit is exceeded by the number of models retained
                in the saved model directory the lowest performing n% of models are deleted, where n is prct_to_remove.
                Default value is 50 and maximum value is 80.
        :return: Nothing
        """

        self._upper_limit = upper_limit
        self._prct_to_remove = prct_to_remove
        cleanup(upper_limit = upper_limit, prct_to_remove = prct_to_remove)
