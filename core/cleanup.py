"""
Script used to clean the saved_models direcotry by deleteing low perfomring models
"""

import pandas as pd
from termcolor import colored
import shutil
from tqdm import tqdm
import pathlib


def cleanup(upper_limit = None, prct_to_remove = None):
    """
    Def to clean up saved models directory
    :param upper_limit: int
            Optional - Threshold number of models to retain. Once this value is exceeded this method will start to delete
            the lowest performing models. Default and minimum value is 15.
    :param prct_to_remove:int
            Optional - Percentage of models to remove. Once upper_limit is exceeded by the number of models retained
            in the saved model directory the lowest performing n% of models are deleted, where n is prct_to_remove.
            Default value is 50 and maximum value is 80.
    :return Nothing
    """

    path = str(pathlib.Path().absolute())

    # upper limit of models to retain
    if upper_limit is None:
        upper_limit = 15
    # percentage of models to remove if upper_limit is exceeded
    if prct_to_remove is None:
        prct_to_remove = 50

    # limits on values
    if upper_limit < 15:
        raise ValueError("ValueError: upper limit must be at least 15")
    elif prct_to_remove > 80:
        raise ValueError("ValueError: percentage of models to remove can be no greater than 80")

    # load in the log of models
    saved_models_dir = path + "/saved_models/"
    log_loc = saved_models_dir + "model_log.csv"
    log = pd.read_csv(log_loc)

    # find the worst performing models
    log = log.sort_values(by="Test Acc", ascending=True)
    dimen = log.shape
    no_models_stored = dimen[0]
    number_to_remove = round((prct_to_remove / 100) * no_models_stored)

    # if meets requirements delete models and remove from the model log
    if number_to_remove >= 1 and no_models_stored > 15:
        df_lowest_perf_models = log[0:number_to_remove]
        models_to_remove = df_lowest_perf_models['Model ID'].to_list()
        print(colored("Cleaning starting, " + str(len(models_to_remove)) + " model(s) to remove...", "red"))
        for model_id in tqdm(models_to_remove):
            shutil.rmtree(saved_models_dir + model_id)
            log = log[log["Model ID"] != model_id]
        log = log.reset_index(drop=True)
        log.to_csv(log_loc, index_label=False, index=False)
        print(colored("Cleaning completed, " + str(len(models_to_remove)) + " model(s) removed", "green"))
    else:
        print(colored("No cleaning required, 0 models deleted", "green"))
