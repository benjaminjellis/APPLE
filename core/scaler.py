"""
Function used to scale input data
"""

import pandas as pd


def scale_df(df):
    """
    :param df: dataframe to scale
    :return: the scaled dataframe and the coeffs of scaling
    """
    maxes = []
    mins = []
    for col in df.columns:
        a = df.min(axis = 0)[col]
        mins.append(a)
        b = df.max(axis = 0)[col]
        maxes.append(b)
        df[col] = (df[col] - a) / (b - a)
    d = {"maxes": maxes, "mins": mins}
    parameters = pd.DataFrame(data = d)
    return df, parameters


def scale_df_with_params(df, parameters_path):
    """
    :param df: dataframe to scale
    :param parameters_path: coeffs to use to scale
    :return: scaled dataframe
    """
    params = pd.read_csv(parameters_path)
    maxes = params["maxes"].to_list()
    mins = params["mins"].to_list()
    i = 0
    for col in df.columns:
        df[col] = (df[col] - mins[i]) / (maxes[i]-mins[i])
        i += 1
    return df
