"""
Def used to transform data for various analytics outputs
"""

from pandas import DataFrame
import pandas as pd


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
            One of "weekly" or "overall"
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
