"""
Class used to train feed-forward MLP classifiers to make predictions
"""

import tensorflow as tf
import pandas as pd
import urllib.request
import os
from datetime import date
import pathlib
from pathlib import Path
import uuid
import core.data_processing as dp

import warnings
from sklearn.exceptions import DataConversionWarning

warnings.filterwarnings(action = "ignore", category = DataConversionWarning)


class Train(object):

    def __init__(self, model_type):

        """
        :param model_type: str
                    one of "model 1", "model 2" or "model 3", see documentation for discussion on models
        """

        self.model_type = model_type
        self.path = str(pathlib.Path().absolute())

        data_dir = self.path + "/data/raw/"

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # grab the latest data
        urllib.request.urlretrieve("http://www.football-data.co.uk/mmz4281/2021/E0.csv", data_dir + "2021.csv")
        urllib.request.urlretrieve("https://www.football-data.co.uk/mmz4281/1920/E0.csv", data_dir + "1920.csv")
        urllib.request.urlretrieve("https://www.football-data.co.uk/mmz4281/1819/E0.csv", data_dir + "1819.csv")

        raw_data_18_19 = pd.read_csv(data_dir + "1920.csv")
        raw_data_19_20 = pd.read_csv(data_dir + "1819.csv")
        raw_data_20_21 = pd.read_csv(data_dir + "2021.csv")

        self.raw_data_combined = dp.preprocessing(raw_data_19_20, raw_data_20_21)

    def train(self, epochs, verbose):
        """
        Method to train model
        :param epochs: int
                number of epochs to train model for
        :param verbose: boolean
                verbose outputs or not
        :return: nothing
        """

        # unique id to label model with
        model_id = uuid.uuid1()
        model_id = str(model_id)

        # directory to output the model to, as well as various other files
        model_output_dir = self.path + "/saved_models/" + model_id + "/"
        if not os.path.exists(model_output_dir):
            os.makedirs(model_output_dir)

        # process and split the data, return the shape of the data plus coeffs used to scale the data
        train_raw, test_raw, input_shape, ord_cols_df, scaler_coeffs = dp.processing(self.raw_data_combined,
                                                                                     model_type = self.model_type,
                                                                                     test_size = 0.2)

        # preapre train data
        # remove the target
        train_labels = train_raw.pop("FTR")
        train = train_raw
        # turn raw data into tf dataset
        train_tensor = tf.data.Dataset.from_tensor_slices((train.values, train_labels.values))
        train_final = train_tensor.batch(5)

        # prepare test data
        test_labels = test_raw.pop("FTR")
        test_length = test_raw.shape[0]
        test_labels = test_labels.to_numpy()
        test = test_raw

        test = test.to_numpy()

        test = test.reshape(test_length, input_shape)
        test_labels = test_labels.reshape(test_length, 1)

        def get_compiled_model():
            """
            :return: compiled model
            """
            model = tf.keras.Sequential([
                tf.keras.Input(shape = (input_shape,)),
                tf.keras.layers.Dense(10),
                tf.keras.layers.Dense(3, activation = "softmax")
            ])

            model.compile(optimizer = "adam",
                          loss = tf.keras.losses.sparse_categorical_crossentropy,
                          metrics = ["accuracy"])
            return model

        model = get_compiled_model()

        if verbose:
            history = model.fit(train_final, epochs = epochs)
            print("\nhistory dict:", history.history)
        else:
            history = model.fit(train_final, epochs = epochs, verbose = 0)

        self.model_type = self.model_type.replace(" ", "")

        today = date.today().strftime("%Y%m%d")

        # output the model, the columns and scaler coeffs
        model.save(model_output_dir + model_id + ".h5")
        ord_cols_df.to_csv(model_output_dir + model_id + ".csv", index_label = False, index = False)
        scaler_coeffs.to_csv(model_output_dir + model_id + "_coeffs.csv", index_label = False, index = False)

        results = model.evaluate(test, test_labels, batch_size = 50, verbose = 0)

        if verbose:
            print("test loss, test acc:", results)

        log_output = self.path + "/saved_models/model_log.csv"
        log_entry = {'Model type': self.model_type[-1:], "Date": today, "Model ID": model_id, "Test Loss": [results[0]],
                     "Test Acc": [results[1]]}

        # update the log with results of test of model
        try:
            log = pd.read_csv(log_output)
            log_update = pd.DataFrame(data = log_entry)
            log = pd.concat([log, log_update], ignore_index = True)
        except FileNotFoundError:
            Path(log_output).touch()
            log = pd.DataFrame(data = log_entry)

        log.to_csv(log_output, index = False, index_label = False)
