"""
Class used to predict results utilising saved models generated by train.py
"""

import tensorflow as tf
import pandas as pd
import numpy as np
from core.scaler import scale_df_with_params
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
        self.loaded_model = tf.keras.models.load_model(self.saved_models_dir + model_id + "/" + model_id + ".h5")
        # load the list of expected features for the chosen model
        exp_cols_df = pd.read_csv(self.saved_models_dir + model_id + "/" + model_id + ".csv")
        self.exp_cols = exp_cols_df["columns"].to_list()

    def predict(self, fixtures_to_predict):
        """
        :param fixtures_to_predict: str
                name of file containing the fixtures to predict
        :return: dataframe
                dataframe of probabilities
        """

        fixtures_to_predict["fixture"] = fixtures_to_predict["HomeTeam"] + " v " + fixtures_to_predict["AwayTeam"]
        list_of_fixtures = fixtures_to_predict["fixture"].to_list()

        # one hot encoding for the teams
        ats = pd.get_dummies(fixtures_to_predict["AwayTeam"], prefix="at")
        hts = pd.get_dummies(fixtures_to_predict["HomeTeam"], prefix="ht")
        fixtures_to_predict = pd.concat([fixtures_to_predict, ats], axis=1, sort=False)
        fixtures_to_predict = pd.concat([fixtures_to_predict, hts], axis=1, sort=False)
        fixtures_to_predict.pop("AwayTeam")
        fixtures_to_predict.pop("HomeTeam")

        # try and format the data so that it can be passed to specified model
        data_in = formatting_for_passing_to_model(rawdata = fixtures_to_predict,
                                                  exp_features = self.exp_cols,
                                                  model_id = self.model_id)

        # scale
        data_in_sclaed = scale_df_with_params(data_in, self.saved_models_dir + self.model_id + "/" + self.model_id + "_coeffs.csv")
        data_in_sclaed = data_in_sclaed.to_numpy()
        m, n = data_in.shape
        prediction = self.loaded_model.predict(data_in_sclaed)

        final_prediction = []

        for i in range(0, m):
            if np.argmax(prediction[i]) == 0:
                final_prediction.append("H")
            elif np.argmax(prediction[i]) == 1:
                final_prediction.append("A")
            elif np.argmax(prediction[i]) == 2:
                final_prediction.append("D")

        predicted_result = pd.DataFrame(
            {'Fixture': list_of_fixtures, 'p(H)': prediction[:, 0], 'p(A)': prediction[:, 1], 'p(D)': prediction[:, 2],
             "APPLE Prediction": final_prediction})

        return predicted_result
