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

pd.options.mode.chained_assignment = None


def calculate_accuracy(df: DataFrame, user_prediction_cols: list, week: str = None) -> DataFrame:
    """
    Def used to calculate the accuracyt
    :param df: DataFrame to calculate accuracy for
    :param user_prediction_cols:
    :param week: str Optional
    :return: DataFrame
            Accuracy of user predictions
    """

    def correct_pred(col1: str, col2: str) -> int:
        """
        Def used to calculate if a predictor made a correct or incoorect prediction by comparing user
        predictions to FTR row by row.
        :param col1: str
                Name of user column for calculate if the prediction is correct
        :param col2: str
                Name of the FTR column used to calculate if prediction is correct
        :return: int
                1 if prediction is correct, 0 if not
        """
        if col1 == col2:
            return 1
        else:
            return 0

    # find the number of matches that were predicted that week
    no_matches = df.shape[0]
    # get the name of the predictors
    predictors = [col.replace(" Prediction", "") for col in user_prediction_cols]
    df.to_csv("~/Desktop/intermediate_check.csv")
    for i in range(0,len(predictors)):
        df[predictors[i]] = df.apply(lambda x: correct_pred(x[user_prediction_cols[i]], x['FTR']), axis = 1)
    summed_filtered_df = df.sum()
    summed_filtered_df = summed_filtered_df[predictors]
    summed_results_df = pd.DataFrame(
        {'Predictor': summed_filtered_df.index, 'Correct Predictions': summed_filtered_df.values})
    if week:
        summed_results_df["Week"] = week
    summed_results_df['Accuracy of Predictions (%)'] = (summed_results_df['Correct Predictions'] / no_matches) * 100
    return summed_results_df


def calculate_accuracy_transform(df: DataFrame, mode: str) -> DataFrame:
    """
    Def to perform accuracy transformed on passed DataFrame
    :param df: DataFrame
            DataFrame to transform
    :param mode: str
            One of weekly or "overall"
    :return: DateFrame
            Accuracy transformed DataFrame
    """
    # get the columns of the dataframe
    input_df_columns = df.columns.to_list()
    # get just the prediction columns
    user_prediction_cols = [column for column in input_df_columns if "Prediction" in column]

    if mode == "weekly":
        # define the empty transformed (and output) df
        accuracy_transform_df = pd.DataFrame(
            columns = ['Predictor', 'Correct Predictions', 'Week', 'Accuracy of Predictions (%)'])

        weeks_present = set(df["Week"].to_list())

        #  filter for each week
        for week in weeks_present:
            # filter to only show one week
            filtered_df = df[df["Week"] == week].reset_index()
            summed_results_df = calculate_accuracy(filtered_df, user_prediction_cols, week = week)
            accuracy_transform_df = pd.concat([accuracy_transform_df, summed_results_df], ignore_index = True)

    elif mode == "overall":
        accuracy_transform_df = pd.DataFrame(
            columns = ['Predictor', 'Correct Predictions', 'Accuracy of Predictions (%)'])
        summed_results_df = calculate_accuracy(df, user_prediction_cols)
        accuracy_transform_df = pd.concat([accuracy_transform_df, summed_results_df], ignore_index = True)

    else:
        raise Exception

    return accuracy_transform_df


def winners_from_dataframe(dataframe: DataFrame, find_max_of: str, get_winners_from: str) -> str:
    """
    :param dataframe: DataFrame
            DataFrame to get winner from
    :param find_max_of: str
            Column to find the max value for
    :param get_winners_from: str
            Which column to index for returning
    :return:
    """
    max_val = dataframe[find_max_of].max()
    winners = dataframe[dataframe[find_max_of] == max_val][get_winners_from].to_list()
    winners_str = ','.join(winners)
    return winners_str


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
                                                            on = ["HomeTeam", "AwayTeam"])

        weekly_pred_output_cols = ["HomeTeam", "AwayTeam", "Date", "APPLE Prediction"] + user_prediction_cols

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

        # standardise team names in ftrs
        ftr["HomeTeam"] = ftr.apply(
            lambda x: team_name_standardisation(x["HomeTeam"]),
            axis = 1)
        ftr["AwayTeam"] = ftr.apply(
            lambda x: team_name_standardisation(x["AwayTeam"]),
            axis = 1)

        # merge the user predictions and the full time results
        results_and_predictions_df = self.this_week_predictions.merge(ftr, how = "inner", on = ["HomeTeam", "AwayTeam", "Date"])

        # get number of matches were predicted for
        results_and_predictions_df_cols = ["Date", "Time", "Week", "HomeTeam", "AwayTeam", "APPLE Prediction"] + self.user_prediction_cols + ["FTR"]
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
