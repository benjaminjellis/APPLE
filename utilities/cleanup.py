"""
Script used to clean the saved_models direcotry by deleteing low perfomring models
"""

import pandas as pd
from termcolor import colored
import shutil
from tqdm import tqdm
import pathlib


class cleanup():
    def __init__(self):
        path = str(pathlib.Path().absolute())

        #upper limit of models to retain
        upper_limit = 15
        #percenatage of model to remove
        prct_to_remove = 50

        if upper_limit < 15:
            raise ValueError("ValueError: upper limit must be at least 15")
        elif prct_to_remove > 80:
            raise ValueError("ValueError: percentage of models to remove can be no greater than 80")

        #load in the log of models
        saved_models_dir = path + "/saved_models/"
        log_loc = saved_models_dir + "model_log.csv"
        log = pd.read_csv(log_loc)

        #find the worst perfmoring models
        log = log.sort_values(by = "Test Acc", ascending = True)
        dimen = log.shape
        no_models_stored = dimen[0]
        number_to_remove = round((prct_to_remove / 100) * no_models_stored)

        if number_to_remove >= 1 and no_models_stored > 15:
            df_lowest_perf_models = log[0:number_to_remove]
            models_to_remove = df_lowest_perf_models['Model ID'].to_list()
            print(colored("Cleaning starting, " + str(len(models_to_remove)) + " model(s) to remove...", "red"))
            for model_id in tqdm(models_to_remove):
                shutil.rmtree(saved_models_dir + model_id)
                log = log[log["Model ID"] != model_id]
            log = log.reset_index(drop = True)
            log.to_csv(log_loc, index_label = False, index = False)
            print(colored("Cleaning completed, " + str(len(models_to_remove)) + " model(s) removed", "green"))
        else:
            print(colored("No cleaning required, 0 models deleted", "green"))
