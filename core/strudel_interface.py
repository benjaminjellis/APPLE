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


def validate_date(date: str):
    """
    Def used to validate that passed date is in ISO format (YYYY-MM-DD), if not ValueError raised
    :param date: str
            Date to validate
    :return: nothing
    """
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")


def query_fixtures_endpoint_csv(start_date: str, end_date: str, week: int, output_loc: str, include_predictions: bool,
                                authentication: dict):
    """
    Def to query STRUDEL fixtures endpoint and return fixtures with or without user predictions for specified date range
    :param include_predictions: bool
            whether to include user predictions
    :param authentication: dict[str]
            token to pass in request
    :param output_loc: str
            filepath specifying output location for csv
    :param week: int
            week number, used to display data to end users
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
    print(colored("Requesting user predictions for fixtures between {} and {}".format(start_date, end_date), "red"))
    response = requests.get(end_point, headers = authentication)
    # check response
    if response.status_code == 200:
        print(colored("Successfully obtained predictions for fixtures between {} and {}".format(start_date, end_date),
                      "green"))
        user_predictions_content = response.content
        user_predictions_raw = pd.read_csv(io.StringIO(user_predictions_content.decode('utf-8')))
        user_predictions_raw["Week"] = week
        # rename columns
        user_predictions_raw.rename(
            {'homeTeamName': 'HomeTeam', 'awayTeamName': 'AwayTeam', "date": "Date", "time": "Time", "fixtureId": "FixtureID"}, axis = 1,
            inplace = True)
        # rearrange cols
        base_cols = ["Date", "Week", "Time", "HomeTeam", "AwayTeam", "FixtureID"]
        if include_predictions:
            user_predictions_output = user_predictions_raw[
                base_cols + [c for c in user_predictions_raw if c not in base_cols]]
            user_predictions_output = user_predictions_output.sort_values(by = ["Date", "Time"], axis = 0)
            # append " Prediction" to header of each user prediction column
            user_predictions_cols = list(user_predictions_output.columns)
            user_prediction_columns = [col for col in user_predictions_cols if col not in base_cols]
            if "Ben" in user_prediction_columns:
                # take out my test predictions
                user_prediction_columns.remove("Ben")
                user_predictions_output = user_predictions_output.drop(["Ben"], axis = 1)
            if "APPLE" in user_prediction_columns:
                # take out my APPLE predictions
                user_prediction_columns.remove("APPLE")
                user_predictions_output = user_predictions_output.drop(["APPLE"], axis = 1)

            user_prediction_col_formatting_dict = {}
            for i in user_prediction_columns :
                user_prediction_col_formatting_dict[i] = i + " Prediction"
            user_predictions_output.rename(user_prediction_col_formatting_dict, axis = 1, inplace = True)
        else:
            user_predictions_output = user_predictions_raw[base_cols]
        output_dir = Path(output_loc)
        output_dir = output_dir.parent
        if not output_dir.exists():
            output_dir.mkdir(parents = True)
        user_predictions_output.to_csv(output_loc, index_label = False, index = False)
    else:
        raise ValueError(
            "Unsuccessful in obtaining user predictions for fixtures between {} and {}".format(start_date, end_date))


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

    def get_fixtures_and_user_predictions(self, start_date: str, end_date: str, week: int, output_loc: str):
        """
        Method to get the fixtures and predictions from the STRUDEL endpoint for specified date range
        :param output_loc: str
                filepath specifying output location for csv
        :param week: int
                week number, used to display data to end users
        :param start_date: str
                Date, format YYYY-MM-DD, for the start date of fixtures window
        :param end_date: str
                Date, format YYYY-MM-DD, for the end date of fixtures window
        :return: nothing
        """
        query_fixtures_endpoint_csv(start_date = start_date,
                                    end_date = end_date,
                                    week = week,
                                    output_loc = output_loc,
                                    include_predictions = True,
                                    authentication = self._token_header)

    def get_fixtures(self, start_date: str, end_date: str, week: int, output_loc: str):
        """
        Method to get the fixtures from the STRUDEL endpoint for specified date range
        :param output_loc: str
                filepath specifying output location for csv
        :param week: int
                week number, used to display data to end users
        :param start_date: str
                Date, format YYYY-MM-DD, for the start date of fixtures window
        :param end_date: str
                Date, format YYYY-MM-DD, for the end date of fixtures window
        :return: nothing
        """
        query_fixtures_endpoint_csv(start_date = start_date,
                                    end_date = end_date,
                                    week = week,
                                    output_loc = output_loc,
                                    include_predictions = False,
                                    authentication = self._token_header)

    def return_predictions(self, prediction_details: dict):
        end_point = "https://beatthebot.co.uk/iapi/predictions"
        response = requests.put(end_point, headers = self._token_header, json = prediction_details)
        if response.status_code == 200:
            print(colored("APPLE prediction for fixture with id {} exported to Strudel".format(prediction_details["fixture"]), "green"))

    def return_visualisations(self, html_filepath: str, visualisation_title: str, notes: str) -> None:
        """
        Def to upload plotly html visualisations to STRUDEL where they are displayed
        :param html_filepath: str
                filepath for the HTML file to upload
        :param visualisation_title: str
                title of the visualisation to upload
        :param notes: str
                comma separated list of notes to display along with the plot on STRUDEL
        :return:
        """
        end_point = "https://beatthebot.co.uk/iapi/analytics"
        # read in html file as a string
        html_file = codecs.open(html_filepath, 'r')
        html_contents = html_file.read()
        today = datetime.today().strftime("%Y_%m_%d")
        visualisation_name = visualisation_title + "_" + today
        body = {
            "name": visualisation_name,
            "heading": visualisation_title,
            "html": html_contents,
            "tagLineList": notes
        }
        """
        html_contents = html_contents.replace("<html>", "")
        html_contents = html_contents.replace("</html>", "")
        html_contents = html_contents.replace('head><meta charset="utf-8" /></head>', "")
        html_contents = html_contents.replace("<body>", "")
        html_contents = html_contents.replace("</body>", "")
        print(html_contents)
        """
        response = requests.put(end_point, headers = self._token_header, json = body)
        if response.status_code == 200:
            print(colored("Visualisation with title {} successfully uploaded ".format(visualisation_title), "green"))
        else:
            print(colored("Visualisation with title {} failed to upload ".format(visualisation_title), "red"))
            print(response.status_code)
            print(response.content)

