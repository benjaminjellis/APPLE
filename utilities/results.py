"""
Script used to evaluate the predictions made by APPLE and others
"""

import pandas as pd
import os
import glob
from pathlib import Path
from IPython.display import display
from termcolor import colored
import pathlib


def correct_pred(col1, col2):
    if col1 == col2:
        return 1
    else:
        return 0


class Predictions(object):

    def __init__(self, week):
        self.path = str(pathlib.Path().absolute())
        self.running_results_dir = self.path + "/data/predictions/running/"
        self.running_results_log = self.running_results_dir + "results_log.csv"
        self.week = week

        predictions_dir = self.path + "/data/predictions/" + week + "/"

        # load in the APPLE predictions
        for f in glob.glob(predictions_dir + "*_predicted_results.csv"):
            apple_pred = pd.read_csv(f)

        # load in user predictions
        uspred_loc = predictions_dir + week + "up.csv"
        upred = pd.read_csv(uspred_loc)
        upred["Fixture"] = upred["HomeTeam"] + " v " + upred["AwayTeam"]

        weekly_pred = apple_pred.copy()

        # aggregate weekly predictions
        weekly_pred["DD Prediction"] = upred["DD Prediction"]
        weekly_pred["JR Prediction"] = upred["JR Prediction"]
        weekly_pred["MW Prediction"] = upred["MW Prediction"]
        weekly_pred["Date"] = upred["Date"]

        # format df for display
        weekly_pred = weekly_pred[
            ["Fixture", "Date", "APPLE Prediction", "DD Prediction", "JR Prediction", "MW Prediction"]]

        self.weekly_pred = weekly_pred

    def show(self):
        display(self.weekly_pred)


class Results(Predictions):

    def aggregate(self):
        # load in actual resutls
        ftr_loc = self.path + "/data/results/" + self.week + "res.csv"
        ftr = pd.read_csv(ftr_loc)

        # add actual results to the weekly prediction table
        self.weekly_pred["FTR"] = ftr["FTR"]
        display(self.weekly_pred)
        no_matches = self.weekly_pred.shape[0]

        # export the results to a running log
        try:
            log = pd.read_csv(self.running_results_log)
            log_update = self.weekly_pred
            log = pd.concat([log, log_update], ignore_index=True)
            log.drop_duplicates(subset=None, keep='first', inplace=True)
            log.reset_index(drop=True)
        except FileNotFoundError:
            if not os.path.exists(self.running_results_dir):
                os.mkdir(self.running_results_dir)
            Path(self.running_results_log).touch()
            log = self.weekly_pred

        log.to_csv(self.running_results_log, index=False, index_label=False)

        # aggregate weekly results and sum to get accuracy of each person's predictions
        self.weekly_pred['APPLE'] = self.weekly_pred.apply(lambda x: correct_pred(x['APPLE Prediction'], x['FTR']),
                                                           axis=1)
        self.weekly_pred['DD'] = self.weekly_pred.apply(lambda x: correct_pred(x['DD Prediction'], x['FTR']), axis=1)
        self.weekly_pred['JR'] = self.weekly_pred.apply(lambda x: correct_pred(x['JR Prediction'], x['FTR']), axis=1)
        self.weekly_pred['MW'] = self.weekly_pred.apply(lambda x: correct_pred(x['MW Prediction'], x['FTR']), axis=1)

        b = self.weekly_pred.sum()
        b = b[['APPLE', 'DD', 'JR', "MW"]]

        weekly_res = pd.DataFrame({' ': b.index, 'Correct Predictions': b.values})
        weekly_res['Accuracy of Predictions (%)'] = (weekly_res['Correct Predictions'] / no_matches) * 100
        weekly_res = weekly_res.sort_values(by='Accuracy of Predictions (%)', ascending=False).reset_index(drop=True)

        print(colored(self.week + " results:", "green"))
        display(weekly_res)

        # find out who won each week and add that to a log
        firstw = weekly_res[' '].iloc[0]
        secondw = weekly_res[' '].iloc[1]
        thridw = weekly_res[' '].iloc[2]
        fourthw = weekly_res[' '].iloc[3]

        if firstw == secondw == thridw == fourthw:
            print("For " + self.week + " it's a four way tie \n\n\n")
            weekly_winner = firstw + ", " + secondw + ", " + thridw + ", " + ", " + fourthw
        if firstw == secondw == thridw:
            weekly_winner = firstw + ", " + secondw + ", " + thridw
            print("For " + self.week + " it's a three way tie between: " + weekly_winner + "\n\n\n")
        if firstw == secondw:
            weekly_winner = firstw + "& " + secondw
            print("For " + self.week + " it's a tie between: " + weekly_winner + "\n\n\n")
        else:
            print("For " + self.week + " the winner is " + firstw + "\n\n\n")
            weekly_winner = firstw

        winner_log_entry = {'Week': [self.week], "Winner": [weekly_winner]}
        log_output = self.running_results_dir + "/winners_log"

        try:
            winners_log = pd.read_csv(log_output)
            log_update = pd.DataFrame(data=winner_log_entry)
            winners_log = pd.concat([winners_log, log_update], ignore_index=True)
        except FileNotFoundError:
            Path(log_output).touch()
            winners_log = pd.DataFrame(data=winner_log_entry)

        winners_log.to_csv(log_output, index=False, index_label=False)

        # calc the overall accuracy of all predictions so far
        no_mathes_log = log.shape[0]

        log['APPLE'] = log.apply(lambda x: correct_pred(x['APPLE Prediction'], x['FTR']), axis=1)
        log['DD'] = log.apply(lambda x: correct_pred(x['DD Prediction'], x['FTR']), axis=1)
        log['JR'] = log.apply(lambda x: correct_pred(x['JR Prediction'], x['FTR']), axis=1)
        log['MW'] = log.apply(lambda x: correct_pred(x['MW Prediction'], x['FTR']), axis=1)

        c = log.sum()
        c = c[['APPLE', 'DD', 'JR', "MW"]]

        log_res = pd.DataFrame({' ': c.index, 'Total Correct Predictions': c.values})
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
