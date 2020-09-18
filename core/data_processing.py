"""
Defs used to do some data processing before training of models
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from core.scaler import scale_df
import numpy as np
from termcolor import colored
from fuzzywuzzy import process


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


def processing(input_df, model_type, test_size):
    """
    :param input_df: dataframe
            dataframe to process
    :param model_type: string
            which model type to process data for
    :param model_type: float
            fraction, size of the test dataset returned
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
    train_raw, test_raw = train_test_split(raw_data_combined_scaled, test_size = test_size)

    return train_raw, test_raw, input_shape, ord_cols_df, coeffs


def formatting_for_passing_to_model(rawdata, exp_features, model_id):
    try:
        backtesting_data = rawdata[exp_features]
        return backtesting_data
    except KeyError:
        key_present = list(rawdata.columns)
        keys_missing = []

        for key in exp_features:
            if key not in key_present:
                keys_missing.append(key)

        length = len(keys_missing)
        track = 0
        shape = rawdata.shape

        for keys in keys_missing:
            if keys[:2] == "at" or "ht":
                track += 1

        print(colored("Attempting to deal with missing datapoint(s)....", 'red'))

        entry = np.zeros((shape[0], 1))

        if length == track:
            print(colored("Fixing input data....", 'red'))
            for key in keys_missing:
                rawdata[key] = entry
            try:
                backtesting_data = rawdata[exp_features]
                print(colored("Input data fixed", 'green'))
                return backtesting_data
            except KeyError:
                print(colored("ERROR - Missing datapoint(s): ", 'red'))
                print(colored("Attempt was made to fix input data, but it wasn't possible", 'red'))

        else:
            print(colored("ERROR - input data cannot be handled", 'red'))
            print(
                colored(model_id + " can't be used to make predicitons wihtout the above, datapoint(s)",
                        "red"))
            raise Exception


def team_name_standardisation(team):
    """
    Returns a standardised name of the passed team using fuzzy string matching. Train data (also called raw) uses abbreviations or contractions for team
    name, some models use team name as a feature for prediction. Thus when mining data for weekly predictions the team
    name needs to be cleaned to match the team name in the train data. The team names in

    :param team: str
            name of a team
    :return: str
            cleaned name consistent with data used to train models.
    """
    teams_19_20 = ["Arsenal", "Aston Villa", "Bournemouth", "Brighton", "Burnley", "Chelsea", "Crystal Palace",
                   "Everton",
                   "Leicester", "Liverpool", "Leeds", "Man City", "Man United", "Newcastle", "Norwich", "Sheffield United",
                   "Southampton",
                   "Tottenham", "Watford", "West Ham", "Wolves", "Fulham", "West Brom"]

    return process.extractOne(team, teams_19_20)[0]