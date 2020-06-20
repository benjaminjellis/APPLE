"""
Scirpt to audit the state of models retained and reevaluate their performance by taking a subset of the train data
"""

import pandas as pd
import os
import numpy as np
import tensorflow as tf
from core.scaler import scale_df_with_params
import pathlib

path = pathlib.Path().absolute()
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

# evaluation of models based on weekly restuls

# load backtesting data
backtesting_dir = path + "/data/backtesting/"
backtesting_data = pd.read_csv(backtesting_dir + "week1.csv")

result_cleanup = {"FTR": {"H": 0, "A": 1, "D": 2}}
backtesting_data.replace(result_cleanup, inplace=True)
FTR = backtesting_data["FTR"]
backtesting_data.drop(labels=["FTR"], axis=1, inplace=True)

# pick a model
model_id = "4be02294-9d52-11ea-8c78-20c9d083a48b"
# load the selected, trained model
loaded_model = tf.keras.models.load_model("saved_models/" + model_id + "/" + model_id + ".h5")
model_sel = log[log['Model ID'] == model_id]

model_type = model_sel['Model type'].values
model_type = str(model_type[0])
model_type = "model " + model_type

# load the expected cols
exp_cols = pd.read_csv("saved_models/" + model_id + "/" + model_id + ".csv")
exp_cols = exp_cols["columns"].to_list()

try:
    backtesting_data = backtesting_data[exp_cols]
except KeyError:
    raise KeyError('Shite, no good!!!')

backtesting_data_scaled = scale_df_with_params(backtesting_data,
                                                      "saved_models/" + model_id + "/" + model_id + "_coeffs.csv")

# add back the target column
test_labels = FTR
test_labels = test_labels.to_numpy()
test_labels = test_labels.astype("float64")
test = backtesting_data_scaled.to_numpy()

results = loaded_model.evaluate(test, test_labels, batch_size=50)
