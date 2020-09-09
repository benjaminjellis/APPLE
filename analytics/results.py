"""
Script used to evaluate the predictions made by APPLE and others
"""

import pandas as pd
from IPython.display import display
from termcolor import colored
from core.loaders import load_json_or_csv
import pathlib


def correct_pred(col1, col2):
    if col1 == col2:
        return 1
    else:
        return 0


def winners_from_dataframe(dataframe, find_max_of, get_winners_from):
    max_val = dataframe[find_max_of].max()
    winners = dataframe[dataframe[find_max_of] == max_val][get_winners_from].to_list()
    winners_str = ','.join(winners)
    return winners_str


class Predictions(object):

    def __init__(self, user_predictions, apple_predictions, aggregated_results_file):
        """
        :param user_predictions: str
                filepath for the user predictions input file
        :param apple_predictions: str
                filepath for the apple prediction input file
        :param aggregated_results_file: str
                filepath for the aggregated_results output file
        """
        self.path = str(pathlib.Path().absolute())
        self.running_log = aggregated_results_file
        self.user_predictions = load_json_or_csv(user_predictions)
        self.apple_predictions = load_json_or_csv(apple_predictions)

        # load in user predictions
        self.user_predictions["Fixture"] = self.user_predictions ["HomeTeam"] + " v " + self.user_predictions ["AwayTeam"]

        this_week_predictions = self.apple_predictions

        # get the user prediction columns
        user_prediction_cols_raw = self.user_predictions.columns.to_list()
        user_prediction_cols = []

        for col in user_prediction_cols_raw:
            if "Prediction" in col:
                user_prediction_cols.append(col)

        # aggregate weekly predictions
        for col in user_prediction_cols:
            this_week_predictions[col] = self.user_predictions[col]

        # get dates
        this_week_predictions["Date"] = self.user_predictions["Date"]

        weekly_pred_output_cols = ["Fixture", "Date", "APPLE Prediction"] + user_prediction_cols

        # format df for display
        this_week_predictions = this_week_predictions[
            weekly_pred_output_cols]
        self.user_prediction_cols = user_prediction_cols
        self.this_week_predictions = this_week_predictions

    def show(self):
        display(self.this_week_predictions)


class Results(Predictions):

    def aggregate(self, ftrs, winners_log):
        """
        :param ftrs: str
                filepath for the full time results input file
        :param winners_log: str
                filepath for the winner log output file
        :return: nothing
        """

        # load in full time results
        ftr = load_json_or_csv(ftrs)
        ftr["Fixture"] = ftr["HomeTeam"] + " v " + ftr["AwayTeam"]

        # merge the user predictions and the full time results
        results_and_predictions_df = self.this_week_predictions.merge(ftr, how = "inner")

        # get number of matches were predicted for
        no_matches = results_and_predictions_df.shape[0]
        results_and_predictions_df_cols = ["Date", "Time", "Week", "Fixture", "HomeTeam", "AwayTeam", "APPLE Prediction"] + self.user_prediction_cols + ["FTR"]
        results_and_predictions_df = results_and_predictions_df[results_and_predictions_df_cols]
        display(results_and_predictions_df)

        # export the weekly user predictions and full time results to a running log
        try:
            log = load_json_or_csv(self.running_log)
            log_update = results_and_predictions_df
            log = pd.concat([log, log_update], ignore_index=True)
            log.drop_duplicates(subset=None, keep='first', inplace=True)
            log.reset_index(drop=True)
        except FileNotFoundError:
            log = results_and_predictions_df

        # export running log to file
        log.to_csv(self.running_log, index=False, index_label=False)

        # find accuracy of each predictor
        results_and_predictions_df['APPLE'] = results_and_predictions_df.apply(lambda x: correct_pred(x['APPLE Prediction'], x['FTR']), axis=1)
        agg_out_col_name = []

        for col in self.user_prediction_cols:
            out_col_name = col.strip(" Prediction")
            agg_out_col_name.append(out_col_name)
            results_and_predictions_df[out_col_name] = results_and_predictions_df.apply(lambda x: correct_pred(x[col], x['FTR']), axis=1)

        # sum cols to get accuracies
        correct_res_df = results_and_predictions_df.sum()
        correct_res_df = correct_res_df[["APPLE"] + agg_out_col_name]
        summed_results_df = pd.DataFrame({' ': correct_res_df.index, 'Correct Predictions': correct_res_df.values})
        summed_results_df['Accuracy of Predictions (%)'] = (summed_results_df['Correct Predictions'] / no_matches) * 100
        summed_results_df = summed_results_df.sort_values(by='Accuracy of Predictions (%)', ascending=False).reset_index(drop=True)

        print(colored("\nLast week's results:", "green"))
        display(summed_results_df)

        # find out who won each week
        weekly_winners = winners_from_dataframe(summed_results_df, find_max_of = "Accuracy of Predictions (%)", get_winners_from = " ")
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
        no_mathes_log = log.shape[0]
        # load in
        agg_out_col_name = []
        log['APPLE'] = log.apply(lambda x: correct_pred(x['APPLE Prediction'], x['FTR']), axis=1)

        for col in self.user_prediction_cols:
            out_col_name = col.strip(" Prediction")
            agg_out_col_name.append(out_col_name)
            log[out_col_name] = log.apply(lambda x: correct_pred(x[col], x['FTR']), axis=1)

        log_summed = log.sum()
        log_summed = log_summed[["APPLE"] + agg_out_col_name]

        log_res = pd.DataFrame({' ': log_summed.index, 'Total Correct Predictions': log_summed.values})
        log_res['Accuracy of Total Predictions (%)'] = (log_res['Total Correct Predictions'] / no_mathes_log) * 100
        log_res = log_res.sort_values(by='Accuracy of Total Predictions (%)', ascending=False).reset_index(drop=True)

        print(colored("\nresults to date:", "green"))
        display(log_res)

        # find out who won each week
        overall_leader = winners_from_dataframe(log_res, find_max_of = 'Accuracy of Total Predictions (%)', get_winners_from = " ")
        # audit list of weekly winners
        print("Overall winner(s): {}".format(overall_leader))
