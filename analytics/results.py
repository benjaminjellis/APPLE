"""
Script used to evaluate the predictions made by APPLE and human predictors
"""

import pandas as pd
from pandas import DataFrame
from IPython.display import display
from termcolor import colored
from core.loaders import load_json_or_csv
import pathlib
from core.data_processing import team_name_standardisation


class Predictions(object):

    def __init__(self, user_predictions: str, apple_predictions: str) -> None:
        """
        :param user_predictions: str
                filepath for the user predictions input file
        :param apple_predictions: str
                filepath for the apple prediction input file
        """
        self.path = str(pathlib.Path().absolute())
        self.user_predictions = load_json_or_csv(user_predictions)
        self.apple_predictions = load_json_or_csv(apple_predictions)
        # convert date columns to datetime dtype to avoid any issues with
        self.user_predictions["Date"] = pd.to_datetime(self.user_predictions["Date"])

        # standardise team names in user predictions
        self.user_predictions["HomeTeam"] = self.user_predictions.apply(
                lambda x: team_name_standardisation(x["HomeTeam"]), axis = 1)
        self.user_predictions["AwayTeam"] = self.user_predictions.apply(
                lambda x: team_name_standardisation(x["AwayTeam"]), axis = 1)
        this_week_predictions = self.apple_predictions

        # get the user prediction columns
        user_prediction_cols_raw = self.user_predictions.columns.to_list()
        user_prediction_cols = [col for col in user_prediction_cols_raw if "Prediction" in col]
        # aggregate weekly predictions
        this_week_predictions = this_week_predictions.merge(self.user_predictions, how = "inner",
                                                            on = ["HomeTeam", "AwayTeam", "FixtureID"])
        weekly_pred_output_cols = ["HomeTeam", "AwayTeam", "Date", "FixtureID", "APPLE Prediction"] + user_prediction_cols

        # format df for display
        this_week_predictions = this_week_predictions[
            weekly_pred_output_cols]
        self.user_prediction_cols = user_prediction_cols
        self.this_week_predictions = this_week_predictions

    def show(self):
        display(self.this_week_predictions)


class Results(Predictions):

    def aggregate(self, aggregated_results_file: str, ftrs: str, winners_log: str) -> None:
        """
        :param aggregated_results_file:
        :param ftrs: str
                filepath for the full time results input file
        :param winners_log: str
                filepath for the winner log output file
        :return: nothing
        """

        # load in aggregated results file as the running log
        running_log = aggregated_results_file
        # load in full time results
        ftr = load_json_or_csv(ftrs)
        # cast date column as datetime dtype to avoid any merge issue on str representation of date
        ftr["Date"] = pd.to_datetime(ftr["Date"])
        self.this_week_predictions["Date"] = pd.to_datetime(self.this_week_predictions["Date"])

        # standardise team names in ftrs
        ftr["HomeTeam"] = ftr.apply(
            lambda x: team_name_standardisation(x["HomeTeam"]),
            axis = 1)
        ftr["AwayTeam"] = ftr.apply(
            lambda x: team_name_standardisation(x["AwayTeam"]),
            axis = 1)
        self.this_week_predictions.to_csv("~/Desktop/check_weekly_preds.csv")
        # merge the user predictions and the full time results
        results_and_predictions_df = self.this_week_predictions.merge(ftr, how = "inner", on = ["HomeTeam","AwayTeam","FixtureID"])

        # get number of matches were predicted for
        results_and_predictions_df_cols = ["Time", "Week", "HomeTeam", "AwayTeam","FixtureID", "APPLE Prediction"] + self.user_prediction_cols + ["FTR"]
        results_and_predictions_df = results_and_predictions_df[results_and_predictions_df_cols]
        display(results_and_predictions_df)

        # export the weekly user predictions and full time results to a running log
        try:
            log = load_json_or_csv(running_log)
            log_update = results_and_predictions_df
            log = pd.concat([log, log_update], ignore_index=True)
            log.drop_duplicates(subset=None, keep='first', inplace=True)
            log.reset_index(drop=True)
        except FileNotFoundError:
            log = results_and_predictions_df

        # export running log to file
        log.to_csv(running_log, index=False, index_label=False)

        summed_results_df = calculate_accuracy_transform(results_and_predictions_df, mode = "weekly")

        print(colored("\nLast week's results:", "green"))
        # sort by the accuracy for predictions for display
        summed_results_df = summed_results_df.sort_values(by = "Accuracy of Predictions (%)", ascending = False).reset_index(drop = True)
        display(summed_results_df)

        # find out who won each week
        weekly_winners = winners_from_dataframe(summed_results_df, find_max_of = "Accuracy of Predictions (%)", get_winners_from = "Predictor")
        # audit list of weekly winners
        print("This weeks' winner(s): {}".format(weekly_winners))
        # add weekly winners to a log
        winner_log_entry = {'Week': [results_and_predictions_df.loc[0,"Week"]], "Winner": [weekly_winners]}

        try:
            winners_log_df = load_json_or_csv(winners_log)
            log_update = pd.DataFrame(data=winner_log_entry)
            winners_log_df = pd.concat([winners_log_df, log_update], ignore_index=True)
        except FileNotFoundError:
            winners_log_df = pd.DataFrame(data=winner_log_entry)
        winners_log_df.to_csv(winners_log, index=False, index_label=False)

        # calc the overall accuracy of all predictions so far
        log_res = calculate_accuracy_transform(log, mode = "overall")
        print(colored("\nresults to date:", "green"))
        # sort by the accuracy for predictions for display
        log_res = log_res.sort_values(by = "Accuracy of Predictions (%)", ascending = False).reset_index(drop = True)
        display(log_res)

        # find out who won each week
        overall_leader = winners_from_dataframe(log_res, find_max_of = 'Accuracy of Predictions (%)', get_winners_from = "Predictor")
        # find out who has the total best prediction results
        print("Overall winner(s): {}".format(overall_leader))
