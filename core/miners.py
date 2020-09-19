"""
Miners are objects used to mine data that APPLE runs off
"""

from selenium import webdriver
import pandas as pd
import numpy as np
from pathlib import Path
from termcolor import colored
from core.data_processing import team_name_standardisation
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import re
from datetime import datetime
from datetime import timedelta
import os


def user_file_overwrite_check(filepath):
    """
    Def used to check if a user wants to overwrite a file
    :param filepath: str
            filepath
    :return: boolean
    """
    if os.path.exists(filepath):
        user_choice = input("The filepath {} already exists, do you want to overwrite it? (y/n)".format(filepath))
        user_choice = user_choice.lower()
        if user_choice == "y":
            return True
        elif user_choice == "n":
            return False
        else:
            user_file_overwrite_check(filepath)
    else:
        return True


def convert_to_decimal(odds):
    """
    Converts British style odds to decimal
    :param odds: list
            a list of the british style odds to convert (odds should be str)
    :return: list
            a list of the decimal odds (odds should be floats)
    """
    # catch "EVS" string that william hill sometimes use
    reformatted_odds = ['2.0' if x == "EVS" else x for x in odds]

    for i in range(0, len(reformatted_odds)):
        # if the odds are british in style
        if "/" in reformatted_odds[i]:
            n, d = reformatted_odds[i].split("/")
            n, d = int(n), int(d)
            val = float(n / d + 1)
        # if they're decimal
        else:
            val = float(reformatted_odds[i])
        reformatted_odds[i] = float(val)

    return reformatted_odds


def odds_missing_warnings(df):
    """
    def to audit warning if any data requested isn't mined
    """
    row_no, col_no = df.shape
    for i in range(0, row_no):
        home_team = df.iloc[i][0]
        away_team = df.iloc[i][1]
        match = "{} v {}".format(home_team, away_team)
        nulls = 0
        null_cols = []
        for j in range(2, col_no):
            null_check = pd.isnull(df.iloc[i][j])
            if null_check:
                nulls += 1
                colname_where_null = df.columns[j]
                null_cols.append(colname_where_null)
        if nulls > 0:
            print(colored(
                "WARNING: for match: {} there are {} null value(s) in the following columns: {}".format(match, nulls,
                                                                                                        null_cols),
                "red"))


class MineOdds(object):
    """"
    Miner to mine odds for that are used for predictions
    """
    def __str__(self):
        return "MineOdds Miner"

    def __init__(self, fixtures_file, mined_data_output):
        """
        :param fixtures_file: str
                filepath of the fixtures to mine odds for
        :param mined_data_output: str
                filepath of the location to output mined data to
        """
        self.mined_data_output = mined_data_output

        print(colored(
            "WARNING: Mine is currently undergoing testing an cannot be relied upon for data mining at present. Please do not use"))
        self.driver = webdriver.Safari()
        self.path = str(Path().absolute())

        # load fixtures to save odds for
        try:
            fixtures = pd.read_csv(
                self.path + "/" + fixtures_file, engine = "python")
            self.fixtures = fixtures[["HomeTeam", "AwayTeam"]]
        except FileNotFoundError:
            raise FileNotFoundError("User predictions file for week {} not found, try using MineFixtures".format(self.week))

        # we need to check that each of the HomeTeam and AwayTeam entries match the schema from raw data
        # use the team_cleaner def and a lambda function to do this
        self.fixtures["HomeTeam"] = self.fixtures.apply(lambda x: team_name_standardisation(x["HomeTeam"]), axis = 1)
        self.fixtures["AwayTeam"] = self.fixtures.apply(lambda x: team_name_standardisation(x["AwayTeam"]), axis = 1)

        self.WH = None
        self.B365 = None
        self.INTERWTTEN = None
        self.BWIN = None
        self.PINACLE = None

    def interwetten(self):
        pass

    def pinacle(self):
        url = "https://www.pinnacle.com/en/soccer/england-premier-league/matchups"
        self.driver.get(url)
        # wait until he css elements to scrape have loaded
        wait = WebDriverWait(self.driver, 30)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "span.style_participantName__vRjBw.ellipsis")))
        # grab the tags which the teams are in
        teams_tags = self.driver.find_elements_by_css_selector("span.style_participantName__vRjBw.ellipsis")
        # create list of the teams
        teams = []
        for t in teams_tags:
            team = t.text
            # place holder test and catch
            ph_test = re.match(".* Teams .*", team)
            if ph_test:
                pass
            else:
                teams.append(team_cleaner(team))

        # grab the tags which the odds are in
        odds = self.driver.find_elements_by_css_selector("span.price")

        # create list of the odds
        odds_clean = []
        for p in odds:
            odds_clean.append(p.text)

        # check that we're getting the right shape
        if int(len(teams) / 2) * 3 != len(odds_clean):
            print(colored(
                "WARNING: PINACLE: The number of odds collected does NOT match the expected number of fixtures collected. Please check this",
                'red'))

        # reshape for final table
        teams_np = np.reshape(teams, (int(len(teams) / 2), 2))
        odds_np = np.reshape(odds_clean, (int(len(teams) / 2), 3))
        combined = np.concatenate((teams_np, odds_np), axis = 1)

        # save to object instance
        self.PINACLE = pd.DataFrame(data = combined[0:, 0:], columns = ["HomeTeam", "AwayTeam", "PSH", "PSD", "PSA"])

    def bet365(self):
        pass

    def bwin(self):
        url = "https://sports.bwin.com/en/sports/football-4/betting/england-14/premier-league-46"
        self.driver.get(url)

        # wait until web page has loaded
        wait = WebDriverWait(self.driver, 30)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.participant")))

        # grab teams and clean names
        teams_tags = self.driver.find_elements_by_css_selector("div.participant")
        teams = []
        for t in teams_tags:
            teams.append(team_cleaner(t.text))

        # grab odds and clean names
        odds = self.driver.find_elements_by_css_selector("div.option.option-indicator")
        odds_clean = []

        for o in odds:
            odds_clean.append(o.text)

        odds_decimal = convert_to_decimal(odds_clean)

        # check that we're getting the right shape
        if int(len(teams) / 2) * 3 != len(odds_decimal):
            print(colored(
                "WARNING: BWIN: The number of odds collected does NOT match the expected number of fixtures collected. Please check this",
                'red'))

        teams_np = np.reshape(teams, (int(len(teams) / 2), 2))
        odds_np = np.reshape(odds_decimal, (int(len(teams) / 2), 3))
        combined = np.concatenate((teams_np, odds_np), axis = 1)

        self.BWIN = pd.DataFrame(data = combined[0:, 0:], columns = ["HomeTeam", "AwayTeam", "BWH", "BWD", "BWA"])

    def williamhill(self):
        url = "https://sports.williamhill.com/betting/en-gb/football/competitions/OB_TY295/English-Premier-League/matches/OB_MGMB/Match-Betting"
        self.driver.get(url)
        wait = WebDriverWait(self.driver, 30)
        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "main")))
        fixtures_tags = self.driver.find_elements_by_css_selector("main.sp-o-market__title")
        teams = []
        for f in fixtures_tags:
            home, away = f.text.split(" v ")
            home = team_cleaner(team = home)
            away = team_cleaner(team = away)
            teams.append(home)
            teams.append(away)

        odds = self.driver.find_elements_by_css_selector(
            "button.sp-betbutton:not(.sp-betbutton--enhanced):not(.sp-betbutton--super-odds")
        odds_clean = []
        for o in odds:
            odds_clean.append(o.text)

        # convert odds to deci
        odds_decimal = convert_to_decimal(odds_clean)

        # check that we're getting the right shape
        if int(len(teams) / 2) * 3 != len(odds_decimal):
            print(colored(
                "WARNING: WILLIAM HILL: The number of odds collected does NOT match the expected number of fixtures collected. Please check this",
                'red'))

        teams_np = np.reshape(teams, (int(len(teams) / 2), 2))
        odds_np = np.reshape(odds_decimal, (int(len(teams) / 2), 3))
        combined = np.concatenate((teams_np, odds_np), axis = 1)

        self.WH = pd.DataFrame(data = combined[0:, 0:], columns = ["HomeTeam", "AwayTeam", "WHH", "WHD", "WHA"])

    def all(self):
        """
        Method to mine from all sources at once
        :return:
        """
        self.williamhill()
        self.pinacle()
        self.bwin()
        self.interwetten()
        self.bet365()
        self.driver.close()

        # mergeing / joining DFs
        intermediate_1 = self.fixtures.merge(self.PINACLE, on = ["HomeTeam", "AwayTeam"], how = "left")
        intermediate_2 = intermediate_1.merge(self.BWIN, on = ["HomeTeam", "AwayTeam"], how = "left")
        output = intermediate_2.merge(self.WH, on = ["HomeTeam", "AwayTeam"], how = "left")

        # audit warnings about odds missing from mining
        odds_missing_warnings(df = output)

        output.to_json(self.path + "/" + self.mined_data_output)


class MineFixtures(object):

    def __str__(self):
        return "MineFixture Miner"

    def __init__(self, start_date, period, label):
        """
        :param start_date: str
                date in DD-MM-YYYY format, start_date is the first date you want to grab fixtures for
        :param period: int
                number of days you wnant to grab fixtures for i.e. if you want to get the next 10 days of fixtures after
                "20-07-2020" period should be 10 which will grab fixtures from 20-07-2020 -> 30-07-2020 inclusive
        :param label: str
                name of the directory you want to create to hold the mined fixtures, the filename will also use this label
        """
        self.start_date = datetime.strptime(start_date, "%d-%m-%Y")
        self.period = period
        self.label = label
        self.end_date = self.start_date + timedelta(days = self.period )
        self.url = "https://www.premierleague.com/fixtures"
        self.driver = webdriver.Safari()
        self.path = str(Path().absolute())
        self.fixtures_output_file_loc = label + "up.csv"

    def mine_fixtures(self):
        # if the file does exist already ask the user if they want to overwrite it
        if user_file_overwrite_check(self.fixtures_output_file_loc):
            self.driver.get(url = self.url)
            wait = WebDriverWait(self.driver, 30)
            wait.until(EC.visibility_of_element_located((By.TAG_NAME, "div.data-competition-matches-list")))
            dates = self.driver.find_elements_by_class_name("div.data-competition-matches-list")
            for i in dates:
                print(i.text)

        else:
            print("File will not be overwritten, shutting down miner")


