"""
Script used to train models on new data and predict upcoming fixtures, this is done on a weekly basis
"""

from core.train import Train
from core.predict import Predict
import pandas as pd
import os
from termcolor import colored
from utilities.cleanup import Cleanup

# which fixtures to predict
fixtures_file_name = "w31f.csv"

path = os.path.dirname(os.path.abspath(__file__))

models_to_train = ["model 1", "model 2", "model 3"]

# train all 3 models on the latest data
print(colored("Training models on new data....", "green"))
Train(model_type = "model 1").train(epochs = 22, verbose = True)
Train(model_type = "model 2").train(epochs = 22, verbose = True)
Train(model_type = "model 3").train(epochs = 22, verbose = True)
print(colored("Training completed", "green"))

# interrogate the model log to pick the best models compiled thus far
log_loc = path + "/saved_models/"
log = pd.read_csv(log_loc + "model_log.csv")

# sort, descnding on test acc and grab the top performing model
log = log.sort_values(by="Test Acc", ascending=False)
top = log[:1]

# then grab model id
models = top['Model ID'].to_list()

# where to store predictions made by the top performing model
res_dir = path + "/predictions/"
if not os.path.exists(res_dir):
    os.mkdir(res_dir)

# location and name of fixtures to predict
fixtures_file = path + "/fixtures/" + fixtures_file_name
name, file_extension = fixtures_file_name.split(".")

if file_extension == "csv":
    fixtures_to_predict = pd.read_csv(fixtures_file)
elif file_extension == "json":
    fixtures_to_predict = pd.read_json(fixtures_file)
else:
    raise Exception("File format " + file_extension + " not supported for fixtures to predict")

week = fixtures_to_predict['Week'].to_list()
week = list(set(week))

data_dir = path + "/data/backtesting/"

if not os.path.exists(data_dir):
    os.mkdir(data_dir)

fixtures_for_back_testing = fixtures_to_predict.copy()
fixtures_for_back_testing['FTR'] = "H"
fixtures_for_back_testing.to_csv(data_dir + "week" + str(week[0]) + ".csv", index=False, index_label=False)

if len(week) > 1:
    res_dir = res_dir + "various_weeks/"
if len(week) == 1:
    res_dir = res_dir + "week" + str(week[0]) + "/"

if not os.path.exists(res_dir):
    os.mkdir(res_dir)

for model in models:
    print(colored("Using model No. " + str(model) + " for prediction", "yellow"))
    predicted_results = Predict(model_id = model).predict(fixtures_to_predict = fixtures_to_predict)
    print(colored(predicted_results, "blue"))
    predicted_results.to_csv(res_dir + model + "_predicted_results.csv", index_label=False, index=False)

# cleanup the saved_models dir
# using try here as we've seen some errors in cleanup that are can't be explained, monitoring this
try:
    Cleanup()
except FileNotFoundError:
    raise Exception("Couldn't find a model cleanup is trying to remove")
