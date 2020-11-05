"""
Class used to interface with STRUDEL to get fixtures with or without user predictions
"""
import requests
import json
import datetime
import io
import pandas as pd
from pathlib import Path
from termcolor import colored
from datetime import datetime
import codecs


path = str(Path().absolute().parent)


def validate_date(date: str) -> None:
    """
    Def used to validate that passed date is in ISO format (YYYY-MM-DD), if not ValueError raised
    :param date: str
            Date to validate
    :return: nothing if date is correct, raises an error if date is wrong
    """
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")


def query_fixtures_endpoint_csv(start_date: str, end_date: str, output_loc: str, include_user_predictions: bool,
                                authentication: dict, include_apple_predictions: bool, include_ftrs: bool) -> None:
    """
    Def to query STRUDEL fixtures endpoint and return fixtures with or without user predictions for specified date range
    :param include_apple_predictions: bool
            whether to include prediction made by APPLE
    :param include_ftrs: bool
            whether to include full time results 
    :param include_user_predictions: bool
            whether to include user predictions
    :param authentication: dict[str]
            token to pass in request
    :param output_loc: str
            filepath specifying output location for csv
    :param start_date: str
            Date, format YYYY-MM-DD, for the start date of fixtures window
    :param end_date: str
            Date, format YYYY-MM-DD, for the end date of fixtures window
    :return: nothing
    """
    # catch incorrect date formats
    validate_date(start_date)
    validate_date(end_date)
    # defined endpoint
    end_point = "https://beatthebot.co.uk/iapi/fixtures/bydate?startDate=" + start_date + "&endDate=" + end_date + "&format=csv"
    # send GET request
    print(colored("Requesting data for fixtures between {} and {}".format(start_date, end_date), "red"))
    response = requests.get(end_point, headers = authentication)
    # check response
    if response.status_code == 200:
        print(colored("Successfully obtained predictions for fixtures between {} and {}".format(start_date, end_date),
                      "green"))
        response_content = response.content
        response_raw = pd.read_csv(io.StringIO(response_content.decode('utf-8')))
        response_raw.to_csv("~/Desktop/test123.csv")
        # rename some columns
        response_raw.rename(
            {'homeTeamName': 'HomeTeam', 'awayTeamName': 'AwayTeam', "date": "Date", "time": "Time", "fixtureId": "FixtureID", 'week': 'Week'}, axis = 1,
            inplace = True)
        all_columns = list(response_raw.columns)
        base_cols = ["Date", "Time", "Week", "HomeTeam", "AwayTeam", "FixtureID"]
        if include_ftrs:
            base_cols = base_cols + ["FTR"]
        else:
            if "FTR" in all_columns:
                # drop FTRs from DF
                all_columns.remove("FTR")
                response_raw = response_raw.drop(["FTR"], axis = 1)
        if include_user_predictions:
            response_output = response_raw[
                base_cols + [c for c in response_raw if c not in base_cols]]
            response_output = response_output.sort_values(by = ["Date", "Time"], axis = 0)
            # append " Prediction" to header of each user prediction column
            user_predictions_cols = list(response_output.columns)
            user_prediction_columns = [col for col in user_predictions_cols if col not in base_cols]
            if "Ben" in user_prediction_columns:
                # take out my test predictions
                user_prediction_columns.remove("Ben")
                response_output = response_output.drop(["Ben"], axis = 1)
            if "APPLE" in user_prediction_columns and not include_apple_predictions:
                # take out APPLE predictions
                user_prediction_columns.remove("APPLE")
                response_output = response_output.drop(["APPLE"], axis = 1)

            user_prediction_col_formatting_dict = {}
            for i in user_prediction_columns :
                user_prediction_col_formatting_dict[i] = i + " Prediction"
            response_output.rename(user_prediction_col_formatting_dict, axis = 1, inplace = True)
        else:
            response_output = response_raw[base_cols]
        output_dir = Path(output_loc)
        output_dir = output_dir.parent
        if not output_dir.exists():
            output_dir.mkdir(parents = True)
        response_output.to_csv(output_loc, index_label = False, index = False)
    else:
        raise ValueError(
            "Unsuccessful in obtaining requested data for fixtures between {} and {}".format(start_date, end_date))


class StrudelInterface(object):

    def __init__(self, credentials_filepath: str):
        """
        Constructor is used to log in to STRUDEL endpoint
        :param credentials_filepath: str
                filepath of json file containing credentials for log in
        """
        # use the constructor of the class to login
        print(colored("Attempting to log into STRUDEL....", "red"))
        # load in log in credentials
        with open(credentials_filepath) as json_file:
            credentials = json.load(json_file)
        _login_url = "https://beatthebot.co.uk/login"
        # log in
        login_response = requests.post(_login_url, json = credentials)
        # check REST response
        if login_response.status_code == 200:
            print(colored("Successful log in", "green"))
            login_response_content_json = login_response.json()
            self._token_header = {'Authorization': login_response_content_json["token"]}
        else:
            raise ValueError("Incorrect Log in details, log in unsuccessful")

    def get_fixtures_and_user_predictions(self, start_date: str, end_date: str, output_loc: str) -> None:
        """
        Method to get the fixtures and predictions from the STRUDEL endpoint for specified date range
        :param output_loc: str
                filepath specifying output location for csv
        :param start_date: str
                Date, format YYYY-MM-DD, for the start date of fixtures window
        :param end_date: str
                Date, format YYYY-MM-DD, for the end date of fixtures window
        :return: nothing
        """
        query_fixtures_endpoint_csv(start_date = start_date,
                                    end_date = end_date,
                                    output_loc = output_loc,
                                    include_user_predictions = True,
                                    include_apple_predictions = False,
                                    include_ftrs = False,
                                    authentication = self._token_header)

    def get_fixtures(self, start_date: str, end_date: str, output_loc: str) -> None:
        """
        Method to get the fixtures from the STRUDEL endpoint for specified date range
        :param output_loc: str
                filepath specifying output location for csv
        :param start_date: str
                Date, format YYYY-MM-DD, for the start date of fixtures window
        :param end_date: str
                Date, format YYYY-MM-DD, for the end date of fixtures window
        :return: nothing
        """
        query_fixtures_endpoint_csv(start_date = start_date,
                                    end_date = end_date,
                                    output_loc = output_loc,
                                    include_user_predictions = False,
                                    include_apple_predictions = False,
                                    include_ftrs = False,
                                    authentication = self._token_header)

    def return_predictions(self, prediction_details: dict) -> None:
        """
        Def to upload APPLE predictions to STRUDEL
        :param prediction_details: dict
                Details of each prediction to return
        :return: nothing
        """
        end_point = "https://beatthebot.co.uk/iapi/predictions"
        response = requests.put(end_point, headers = self._token_header, json = prediction_details)
        if response.status_code == 200:
            print(colored("APPLE prediction for fixture with id {} exported to Strudel".format(prediction_details["fixture"]), "green"))
        else:
            print(colored("APPLE prediction for fixture with id {} failed to export to Strudel".format(prediction_details["fixture"]), "green"))
            print(response.status_code)
            print(response.content)

    def return_visualisations(self, html_filepath: str, visualisation_title: str, notes: str, request_id: str) -> bool:
        """
        Def to upload plotly html visualisations to STRUDEL where they are displayed
        :param request_id: str
                ID of the request
        :param html_filepath: str
                filepath for the HTML file to upload
        :param visualisation_title: str
                title of the visualisation to upload
        :param notes: str
                comma separated list of notes to display along with the plot on STRUDEL
        :return: bool
                Returns True if upload is successful, False if not
        """
        end_point = "https://beatthebot.co.uk/iapi/analytics"
        # read in html file as a string
        html_file = codecs.open(html_filepath, 'r')
        html_contents = html_file.read()
        today = datetime.today().strftime("%Y_%m_%d")
        visualisation_heading = visualisation_title
        visualisation_title = visualisation_title + "_" + today + "_" + request_id
        body = {
            "name": visualisation_title,
            "heading": visualisation_heading,
            "html": html_contents,
            "tagLineList": notes
        }
        response = requests.put(end_point, headers = self._token_header, json = body)
        if response.status_code == 200:
            print(colored("Visualisation with title '{}' successfully uploaded ".format(visualisation_title), "green"))
            return True
        else:
            print(colored("Visualisation with title '{}' failed to upload ".format(visualisation_title), "red"))
            print(response.status_code)
            print(response.content)
            return False

    def get_predictions_and_ftrs(self, start_date: str, end_date: str, output_loc: str) -> None:
        query_fixtures_endpoint_csv(start_date = start_date,
                                    end_date = end_date,
                                    output_loc = output_loc,
                                    include_user_predictions = True,
                                    include_ftrs = True,
                                    include_apple_predictions = True,
                                    authentication = self._token_header)

    def get_ftrs(self, start_date: str, end_date: str, output_loc: str) -> None:
        query_fixtures_endpoint_csv(start_date = start_date,
                                    end_date = end_date,
                                    output_loc = output_loc,
                                    include_user_predictions = False,
                                    include_apple_predictions = False,
                                    include_ftrs = True,
                                    authentication = self._token_header)
