"""
Loaders to load in and aggregated data files
"""
import pandas as pd


def load_json_or_csv(filepath):
    path_ignore, extension = filepath.split(".")
    if extension == "json":
        read_df = pd.read_json(filepath)
        return read_df
    elif extension == "csv":
        read_df = pd.read_csv(filepath)
        return read_df
    else:
        raise ValueError("Mined data file type not recognised: " + str(filepath))


def load_and_aggregate(backtesting_data):

    """
    Used to load all data files from specified dir and aggregate them into one dataframe
    :param backtesting_data:

    :return: dataframe
            dataframe of the loaded and aggregated data files
    """

    # check if we've got a list of a str
    if type(backtesting_data) is list:
        # load in the first data file
        aggregated_backtesting_dataset = load_json_or_csv(backtesting_data[0])
        # remove first file from the list data files to load in
        backtesting_data.pop(0)
        # loop through remaining data files and append them to self.mined_data
        for file in backtesting_data:
            loaded_file = load_json_or_csv(file)
            aggregated_backtesting_dataset = pd.concat([aggregated_backtesting_dataset, loaded_file],
                                                       ignore_index = True)
        return aggregated_backtesting_dataset

    elif type(backtesting_data) is str:
        # just load in single backtestinf data file
        backtesting_dataset = load_json_or_csv(backtesting_data)
        return backtesting_dataset
    else:
        raise ValueError("Backtesting data not recognised!")

