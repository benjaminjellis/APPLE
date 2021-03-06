"""
Class used to predict results utilising saved models generated by train.py
"""

from core.nnet import NNet
import torch
import torch.nn as nn
import pandas as pd
from core.data_processing import formatting_for_passing_to_model
import pathlib

pd.options.mode.chained_assignment = None  # default='warn'


class Predict(object):

    def __init__(self, model_id):
        """
        :param model_id: str
                unique model id
        """

        self.path = str(pathlib.Path().absolute())
        self.model_id = model_id
        self.saved_models_dir = self.path + "/saved_models/"
        # load the selected trained model
        self.net = NNet()
        self.net.load_state_dict(torch.load(self.saved_models_dir + model_id + "/" + model_id + ".pth"))
        # load the list of expected features for the chosen model
        exp_cols_df = pd.read_csv(self.saved_models_dir + model_id + "/" + model_id + ".csv")
        self.exp_cols = exp_cols_df["columns"].to_list()

    def predict(self, data_and_fixtures):
        """
        :param data_and_fixtures: str
                name of file containing the fixtures to predict
        :return: dataframe
                dataframe of probabilities
        """

        home_teams_to_predict = data_and_fixtures["HomeTeam"].to_list()
        away_teams_to_predict = data_and_fixtures["AwayTeam"].to_list()
        fixture_ids = data_and_fixtures["FixtureID"].to_list()

        # try and format the data so that it can be passed to specified model
        features_tensor = formatting_for_passing_to_model(rawdata = data_and_fixtures,
                                                  exp_features = self.exp_cols,
                                                  saved_models_dir = self.saved_models_dir,
                                                  model_id = self.model_id)

        result = self.net(features_tensor)
        sm = nn.Softmax(dim = 1)
        result = sm(result)
        _, predicted = torch.max(result.data, 1)
        result = result.detach().numpy()

        final_prediction = []

        for i in range(0, len(predicted)):
            if predicted[i] == 0:
                final_prediction.append("H")
            elif predicted[i] == 1:
                final_prediction.append("A")
            elif predicted[i] == 2:
                final_prediction.append("D")

        predicted_result = pd.DataFrame(
            {'HomeTeam': home_teams_to_predict, "AwayTeam": away_teams_to_predict, "FixtureID": fixture_ids, 'p(H)': result[:, 0], 'p(A)': result[:, 1], 'p(D)': result[:, 2],
             "APPLE Prediction": final_prediction})
        return predicted_result
