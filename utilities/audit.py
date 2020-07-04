"""
Class to audit the state of models retained
"""

import pandas as pd
import numpy as np
import pathlib
import matplotlib.pyplot as plt


class Audit(object):

    def __init__(self):
        path = str(pathlib.Path().absolute())
        saved_models_dir = path + "/saved_models/"
        log_loc = saved_models_dir + "model_log.csv"
        log = pd.read_csv(log_loc)

        # some metrics on overal performance, based on model_log.csv
        acc_means = []
        acc_stdevs = []
        max_acc = []
        min_acc = []
        range = []

        model_numbers = [1, 2, 3]

        for i in model_numbers:
            model_log = log[log['Model type'] == i]
            model_acc = model_log["Test Acc"].to_list()
            max_acc.append(max(model_acc))
            min_acc.append(min(model_acc))
            acc_means.append(np.mean(model_acc))
            acc_stdevs.append(np.std(model_acc))
            range.append(max(model_acc) - min(model_acc))

        data = {'Model type': model_numbers, "Mean test accuracy": acc_means, "stdev acc": acc_stdevs, "max acc": max_acc,
                "min acc": min_acc, "range": range}

        df = pd.DataFrame(data=data)

        print(df)
