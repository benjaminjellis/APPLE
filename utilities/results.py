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


class Predictions(object):

    def __init__(self, user_predictions, apple_predictions, aggregated_results):
        """
        :param user_predictions: str
                filepath for the user predictions input file
        :param apple_predictions: str
                filepath for the apple prediction input file
        :param aggregated_results: str
                filepath for the aggregated_results output file
        """
        self.path = str(pathlib.Path().absolute())
        self.running_log = aggregated_results
        self.user_predictions = load_json_or_csv(user_predictions)
        self.apple_predictions = load_json_or_csv(apple_predictions)

        # load in user predictions
        self.user_predictions["Fixture"] = self.user_predictions ["HomeTeam"] + " v " + self.user_predictions ["AwayTeam"]

        week_predictions = self.apple_predictions

        # get the user prediction columns
        user_prediction_cols_raw = self.user_predictions.columns.to_list()
        user_prediction_cols = []

        for col in user_prediction_cols_raw:
            if "Prediction" in col:
                user_prediction_cols.append(col)

        # aggregate weekly predictions
        for col in user_prediction_cols:
            week_predictions[col] = self.user_predictions[col]

        week_predictions["Date"] = self.user_predictions["Date"]

        weekly_pred_output_cols = ["Fixture", "Date", "APPLE Prediction"] + user_prediction_cols

        # format df for display
        week_predictions = week_predictions[
            weekly_pred_output_cols]
        self.user_prediction_cols = user_prediction_cols
        self.week_predictions = week_predictions

    def show(self):
        display(self.week_predictions)


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
        results_and_predictions_df = self.week_predictions.merge(ftr, how = "outer")
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

        # export running log
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

        print(colored("Last week's results:", "green"))
        display(summed_results_df)

        # find out who won each week and add that to a log
        firstw = summed_results_df[' '].iloc[0]
        secondw = summed_results_df[' '].iloc[1]
        thridw = summed_results_df[' '].iloc[2]
        fourthw = summed_results_df[' '].iloc[3]
        fifthw = summed_results_df[' '].iloc[4]

        if firstw == secondw == thridw == fourthw == fifthw:
            print("Last week it was a five-way tie \n\n\n")
        if firstw == secondw == thridw == fourthw:
            print("Last week it was a f four-way tie \n\n\n")
        if firstw == secondw == thridw:
            weekly_winner = firstw + ", " + secondw + ", " + thridw
            print("Last week it was a fthree-way tie between: " + weekly_winner + "\n\n\n")
        if firstw == secondw:
            weekly_winner = firstw + "& " + secondw
            print("Last week it was a tie between: " + weekly_winner + "\n\n\n")
        else:
            print("Last week the winner was " + firstw + "\n\n\n")
            weekly_winner = firstw

        winner_log_entry = {'Week': [results_and_predictions_df.loc[0,"Week"]], "Winner": [weekly_winner]}

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

        print(colored("results to date:", "green"))
        display(log_res)

        firstr = log_res[' '].iloc[0]
        secondr = log_res[' '].iloc[1]
        thridr = log_res[' '].iloc[2]
        fourthr = log_res[' '].iloc[3]

        if firstr == secondr == thridr == fourthr:
            print("Overall it's a four way tie")
        if firstr == secondr == thridr:
            running_winner = firstr + ", " + secondr + ", " + thridr
            print("Overall it's a three way tie between: " + running_winner)
        if firstr == secondr:
            running_winner = firstr + "& " + secondr
            print("Overall it's a tie between: " + running_winner)
        else:
            print("Overall the most accurate predictor is " + firstr)