"""
Script used to train models on new data, back-test saved models on new data, and predict upcoming fixtures, this is done on a weekly basis
"""

from core.train import Train
from core.predict import Predict
from core.data_mining import Mine
from core.backtest import Backtest
import pandas as pd
import os
from termcolor import colored
from utilities.cleanup import Cleanup
from pathlib import Path


# load in the fixtures
fixtures_file_name = "week33up.csv"
# name of mined_data file to load in
mined_data = "w33f.json"

path = str(Path().absolute())

models_to_train = ["model 1", "model 2", "model 3"]

# train all 3 models on the latest data
print(colored("Training models on new data....", "green"))
Train(model_type = "model 1").train(epochs = 22, verbose = True)
Train(model_type = "model 2").train(epochs = 22, verbose = True)
Train(model_type = "model 3").train(epochs = 22, verbose = True)
print(colored("Training completed", "green"))

# back test all saved models on new data
back_tester = Backtest()
back_tester.all()
back_tester.commit_log_updates()

# interrogate the model log to pick the best models compiled thus far
log_loc = path + "/saved_models/"
log = pd.read_csv(log_loc + "model_log.csv")

# sort, descending on test acc and grab the top performing model
log = log.sort_values(by = "Test Acc", ascending = False)
top = log[:1]

# then grab model id
models = top['Model ID'].to_list()

# where to store predictions (for this week, defined by the fixtures file) made by the top performing model
n = fixtures_file_name.strip("up.csv")
predictions_dir = path + "/data/predictions/" + n + "/"

if not os.path.exists(predictions_dir):
    os.mkdir(predictions_dir)

# location and name of fixtures to predict
fixtures_file = predictions_dir + fixtures_file_name
# load in the fixtures
fixtures_to_predict = pd.read_csv(fixtures_file)

# location and name of mined data
mined_data_dir = path + "/data/mined_data/"
mined_data_file = mined_data_dir + mined_data
name, file_extension = mined_data.split(".")
if file_extension == "csv":
    mined_data_to_merge = pd.read_csv(mined_data_file)
elif file_extension == "json":
    mined_data_to_merge = pd.read_json(mined_data_file)
else:
    raise Exception("File format " + file_extension + " not supported for mined data to predict")

# extract data for predictions from mined data by checking which fixtures
# to predict
fixtures_to_predict = fixtures_to_predict[["HomeTeam", "AwayTeam", "Week"]]
fixtures_and_data_for_prediction = fixtures_to_predict.merge(mined_data_to_merge, how = "inner")

week = fixtures_and_data_for_prediction['Week'].to_list()
week = list(set(week))

for model in models:
    print(colored("Using model No. " + str(model) + " for prediction", "yellow"))
    predicted_results = Predict(model_id = model).predict(fixtures_to_predict = fixtures_and_data_for_prediction)
    print(colored(predicted_results, "blue"))
    predicted_results.to_csv(predictions_dir + model + "_predicted_results.csv", index_label = False, index = False)

# cleanup the saved_models dir
Cleanup()
