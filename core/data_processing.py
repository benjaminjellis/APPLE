"""
Defs used to do some data processing before training of models
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from core.scaler import scale_df


def preprocessing(df1, df2):
    """
    :param df1: dataframe
    :param df2: dataframe
    :return: dataframe
             a combined dataframe made up of the union of columns in df1 and df2
    """

    dataframes = [df1, df2]
    common_cols = list(set.intersection(*(set(df.columns) for df in dataframes)))

    raw_data_combined = pd.concat([df[common_cols] for df in dataframes], ignore_index=True)

    result_cleanup = {"FTR": {"H": 0, "A": 1, "D": 2}}
    raw_data_combined.replace(result_cleanup, inplace=True)
    return raw_data_combined


def processing(input_df, model_type):
    """
    :param input_df: dataframe
            dataframe to process
    :param model_type: string
            which model type to process data for
    :return:
    train_raw: dataframe
            dataframe of the raw data to be used for training
    test_raw: dataframe
            a dataframe of the raw data to be used for testing,
    input_shape: tuple
            shape of the dataframes to be fed to model
    ord_cols_df: list of dtype str
            list of the order of the columns in train_raw and test_raw
    coeffs: dataframe
            the coeffs used in the scaling of the data
    """
    FTR = input_df["FTR"]
    input_df.drop(labels=["FTR"], axis=1, inplace=True)

    if model_type == "model 1":

        # remove all columns that aren"t odds or the final result "FTR"
        raw_data_combined = input_df.drop(["Div", "Date", "FTHG", "FTAG", "HTHG", "HTAG", "HTR", "HS",
                                           "AS", "HST", "AST", "HF", "AF", "HC", "AC", "HY", "AY",
                                           "HR", "AR", "HomeTeam", "AwayTeam", "Referee", "PSCA", "PSCD", "PSCH", "VCA",
                                           "VCD", "VCH"], axis=1)

        input_shape = raw_data_combined.shape[1]

    elif model_type == "model 2":
        raw_data_combined = input_df.drop(["Div", "Date", "FTHG", "FTAG", "HTHG", "HTAG", "HTR", "HS",
                                           "AS", "HST", "AST", "HF", "AF", "HC", "AC", "HY", "AY",
                                           "HR", "AR", "Referee", "PSCA", "PSCD", "PSCH", "VCA", "VCD", "VCH"], axis=1)

        # one hot encoding for away team and home team features
        ats = pd.get_dummies(raw_data_combined["AwayTeam"], prefix="at")
        hts = pd.get_dummies(raw_data_combined["HomeTeam"], prefix="ht")
        raw_data_combined = pd.concat([raw_data_combined, ats], axis=1, sort=False)
        raw_data_combined = pd.concat([raw_data_combined, hts], axis=1, sort=False)

        raw_data_combined.pop("AwayTeam")
        raw_data_combined.pop("HomeTeam")

        input_shape = raw_data_combined.shape[1]

    elif model_type == "model 3":
        raw_data_combined = input_df[["HomeTeam", "AwayTeam"]]

        # one hot encoding for away team and home team features
        ats = pd.get_dummies(raw_data_combined["AwayTeam"], prefix="at")
        hts = pd.get_dummies(raw_data_combined["HomeTeam"], prefix="ht")
        raw_data_combined = pd.concat([raw_data_combined, ats], axis=1, sort=False)
        raw_data_combined = pd.concat([raw_data_combined, hts], axis=1, sort=False)

        raw_data_combined.pop("AwayTeam")
        raw_data_combined.pop("HomeTeam")

        input_shape = raw_data_combined.shape[1]

    else:
        raise Exception("Not a valid model, please choose a valid model")

    # order columns a-z, these will be output to then be used to check that
    # whenever data is fed to the model it is passed correctly

    raw_data_combined = raw_data_combined.reindex(sorted(raw_data_combined.columns),
                                                  axis=1)
    ord_cols = {"columns": list(raw_data_combined.columns)}
    ord_cols_df = pd.DataFrame(data=ord_cols)

    # scale the data
    raw_data_combined_scaled, coeffs = scale_df(raw_data_combined)

    # add back the target column
    raw_data_combined_scaled.insert(0, "FTR", FTR)

    # split into test and train
    raw_data_combined_scaled = raw_data_combined_scaled.sample(frac=1).reset_index(drop=True)
    train_raw, test_raw = train_test_split(raw_data_combined_scaled, test_size=0.2)

    return train_raw, test_raw, input_shape, ord_cols_df, coeffs
