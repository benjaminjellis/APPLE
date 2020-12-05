"""
Def used across APPLE for data processing
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from core.scaler import scale_df
import numpy as np
from core.scaler import scale_df_with_params
from fuzzywuzzy import process
from pandas import DataFrame
from math import ceil
from torch import Tensor
from numpy import array


def create_batched_tensor_dataset(batch_size: int, features: array, labels: array) -> list:
    """
    def to create a list of tuples with batched tensors of features and lables
    :param batch_size: int
            size of batches to create in each tupple
    :param features: numpy array
            a numpy array of features
    :param labels: numpy array
            a numpy array of lables
    :return a list of tuples with batched tensors of features and lables
    """
    # labels should be (nx1) and features should be (nxm)
    features_rows = features.shape[0]
    lables_rows = labels.shape[0]
    if lables_rows != features_rows:
        raise ValueError("Number of lables does not match number of observed features: {} and {}".format(lables_rows,features_rows))
    elif labels.ndim != 1:
        raise ValueError("The lable array should be 1D, got {} dimensions".format(labels.ndim))
    else:
        # split the passed arrays into batches and save each batch as an entry in a list
        indices_or_sections = int(features_rows / batch_size)
        features = np.array_split(features, indices_or_sections)
        labels = np.array_split(labels, indices_or_sections)
        for i in range(0, len(features)):
            # convert the arrays in each entry of the lists into tensors
            features[i] = Tensor(features[i])
            labels[i] = Tensor(labels[i]).long()
        batched_tensor = [(features[i],labels[i]) for i in range(0,len(features))]
        # return the batched tesnor representation of the passed np arrays
        return batched_tensor


def correct_class_imbalance(train_dataset: DataFrame, final_multiplier: int) -> DataFrame:
    """
    Def to over-sample classes underrepresented in training dataset
    :param multiplier: int
            to increase size of dataset
    :param train_dataset: DataFrame
            dataset to be used for training
    :return: the over-sampled training dataset
    """
    # get a list of the classes and counts
    classes = list(set(train_dataset['FTR'].tolist()))
    counts = train_dataset['FTR'].value_counts().tolist()
    # create a list to be used to figure out how to over-sample
    index_to_oversample = [(classes[i], counts[i]) for i in range(0, len(classes))]

    maxcounts = max(counts)

    for i in range(0, len(index_to_oversample)):
        if maxcounts == index_to_oversample[i][1]:
            el2rem = index_to_oversample[i]

    index_to_oversample.remove(el2rem)

    for element in index_to_oversample:
        class_ = element[0]
        occur = element[1]
        delta = maxcounts - occur
        data_filtered = train_dataset[train_dataset["FTR"] == class_].reset_index(drop = True)
        if occur > delta:
            data_filtered = data_filtered.truncate(after = delta - 1)
        elif delta > occur:
            multiplier = ceil(delta / occur)
            data_filtered = pd.concat([data_filtered] * multiplier).reset_index(drop = True)
            data_filtered = data_filtered.truncate(after = delta - 1)
        train_dataset = pd.concat([train_dataset, data_filtered]).reset_index(drop = True)
    train_dataset = pd.concat([train_dataset] * final_multiplier).reset_index(drop = True)
    train_dataset = train_dataset.sample(frac = 1)
    return train_dataset


def convert_oods(x: str) -> float:
    """
    def used to convert British Style odds to European style
    :param x: str
            odd to convert
    :return: converted odd
    """
    x = str(x)
    n, d = x.split("/")
    n = int(n)
    d = int(d)
    div = n / d
    return div + 1


def clean_mined_data(dataframe: DataFrame):
    """
    Def to clean a dataframe so that all odds are european style
    :param dataframe: dataframe to convert
    :return: cleaned dataframe
    """

    # get columns
    cols = dataframe.columns.values.tolist()
    odds_cols = []
    # check the columns and refine only for the odds columns
    for col in cols:
        if col[-1] == "A" or "H" or "D":
            odds_cols.append(col)
    # go through the odd cols
    for odd_col in odds_cols:
        # check if the first value in the col has a slash in it
        check_cell = str(dataframe.iloc[0][odd_col])
        # if odds in the odd_col are british format convert the entire column to euro format
        if "/" in check_cell:
            dataframe.to_csv("~/Desktop/nan_df.csv")
            dataframe[odd_col] = dataframe.apply(lambda x: convert_oods(x[odd_col]), axis = 1)
    # standardise team names
    dataframe["HomeTeam"] = dataframe.apply(lambda x: team_name_standardisation(x["HomeTeam"]),
                                            axis = 1)
    dataframe["AwayTeam"] = dataframe.apply(lambda x: team_name_standardisation(x["AwayTeam"]),
                                            axis = 1)
    return dataframe


def preprocessing(df1: DataFrame, df2: DataFrame, df3: DataFrame) -> DataFrame:
    """
    :param df1: dataframe
    :param df2: dataframe
    :param df3: dataframe
    :return: dataframe
             a combined dataframe made up of the union of columns in df1, df2 and df3
    """

    dataframes = [df1, df2, df3]
    common_cols = list(set.intersection(*(set(df.columns) for df in dataframes)))

    raw_data_combined = pd.concat([df[common_cols] for df in dataframes], ignore_index = True)

    result_cleanup = {"FTR": {"H": 0, "A": 1, "D": 2}}
    raw_data_combined.replace(result_cleanup, inplace = True)
    return raw_data_combined


def processing(input_df: DataFrame, test_size: float, train_batch_size: int):
    """
    :param input_df: dataframe
            dataframe to process
    :param train_batch_size:
    :param test_size: float
            percentage of data to be used as train data
    :return:
    train_raw: dataframe
            dataframe of the raw data to be used for training
    test_raw: dataframe
            a dataframe of the raw data to be used for testing,
    ord_cols_df: list of dtype str
            list of the order of the columns in train_raw and test_raw
    coeffs: dataframe
            the coeffs used in the scaling of the data
    """
    FTR = input_df["FTR"]
    input_df.drop(labels = ["FTR"], axis = 1, inplace = True)

    # select just the desired features
    raw_data_combined = input_df[["B365A", "B365D", "B365H", "BWA", "BWD", "BWH", "PSA",
                                      "PSD", "PSH", "WHA", "WHD", "WHH"]]

    # order columns a-z, these will be output to then be used to check that
    # whenever data is fed to the model it is passed correctly
    raw_data_combined = raw_data_combined.reindex(sorted(raw_data_combined.columns),
                                                  axis = 1)
    ord_cols = {"columns": list(raw_data_combined.columns)}
    ord_cols_df = pd.DataFrame(data = ord_cols)

    # scale the data
    raw_data_combined_scaled, coeffs = scale_df(raw_data_combined)

    # add back the target column
    raw_data_combined_scaled.insert(0, "FTR", FTR)

    # split into test and train
    raw_data_combined_scaled = raw_data_combined_scaled.sample(frac = 1).reset_index(drop = True)
    train_raw, test_raw = train_test_split(raw_data_combined_scaled, test_size = test_size)
    # address class imbalance and increase size of training dataset
    train_raw = correct_class_imbalance(train_raw, final_multiplier = 50)
    # turn dataframes in np arrays
    train_labels = train_raw.pop("FTR").to_numpy()
    train_features = train_raw.to_numpy()
    test_labels = test_raw.pop("FTR").to_numpy()
    test_features = test_raw.to_numpy()
    # turn arrays into torch Tensros for passing to neural net
    train_tensor = create_batched_tensor_dataset(batch_size = train_batch_size,
                                                 features = train_features,
                                                 labels = train_labels)
    test_tensor = create_batched_tensor_dataset(batch_size = len(test_features),
                                                features = test_features,
                                                labels = test_labels)
    return train_tensor, test_tensor, ord_cols_df, coeffs


def formatting_for_passing_to_model(rawdata: DataFrame, exp_features, saved_models_dir: str, model_id: str):
    """
    def used to format rawdataset before it is passed to a model
    :param rawdata: dataframe
                    dataframe containing raw data
    :param exp_features: list
                        list of expected feature column names
    :param model_id: str
                    model id to create raw data for
    :return: wragnled dataframe
    """
    data_with_expected_features = rawdata[exp_features]
    data_in_sclaed = scale_df_with_params(data_with_expected_features,
                                          saved_models_dir + model_id+ "/" + model_id + "_coeffs.csv")
    features_tensor = Tensor(data_in_sclaed.to_numpy())
    return features_tensor


def team_name_standardisation(team: str) -> str:
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
                   "Leicester", "Liverpool", "Leeds", "Man City", "Man United", "Newcastle", "Norwich",
                   "Sheffield United",
                   "Southampton",
                   "Tottenham", "Watford", "West Ham", "Wolves", "Fulham", "West Brom"]

    return process.extractOne(team, teams_19_20)[0]
