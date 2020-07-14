from selenium import webdriver
import pandas as pd
import numpy as np
from time import sleep
from termcolor import colored
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from fuzzywuzzy import process
import re


def convert_to_decimal(odds):
    """
    Converts brtish style odds to decimal
    :param odds: list of strings
    a list of the british style odds to convert to
    :return: list of floats
    a list of the decimal odds
    """
    new_odds = ['2.0' if x == "EVS" else x for x in odds]
    for i in range(0, len(new_odds)):
        if "/" in new_odds[i]:
            n, d = new_odds[i].split("/")
            n, d = int(n), int(d)
            val = float(n / d + 1)
        else:
            val = float(new_odds[i])
        new_odds[i] = float(val)

    return new_odds


def team_cleaner(team):
    """
    Returns a clean name of the passed team. Train data (also called raw) uses abbreviations or contractions for team
    name, some models use team name as a feature for prediction. Thus when mining data for weekly predictions the team
    name needs to be cleaned to match the team name in the train data.

    :param team: str
    name of a team
    :return: str
    cleaned name consistient with data used to train models.
    """
    teams_19_20 = ["Arsenal", "Aston Villa", "Bournemouth", "Brighton", "Burnley", "Chelsea", "Crystal Palace",
                   "Everton",
                   "Leicester", "Liverpool", "Man City", "Man United", "Newcastle", "Norwich", "Sheffield United",
                   "Southampton",
                   "Tottenham", "Watford", "West Ham", "Wolves"]

    return process.extractOne(team, teams_19_20)[0]


class Mine(object):
    """"
    Class to mine odds for that are used for predictions
    """

    def __init__(self, week):
        print(colored("WARNING: Mine is currently undergoing testing an cannot be relied upon for data mining at present. Please do not use"))
        self.driver = webdriver.Safari()
        self.week = week
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
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "span.style_participantName__vRjBw.ellipsis")))
        # grab the tags which the teams are in
        teams_tags = self.driver.find_elements_by_css_selector("span.style_participantName__vRjBw.ellipsis")
        # create list of the teams
        teams = []
        for t in teams_tags:
            team = t.text
            # place holder test and catch
            ph_test = re.match(".* Teams .*",team)
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
            self.warnings = True

        # reshape for final table
        teams_np = np.reshape(teams, (int(len(teams) / 2), 2))
        odds_np = np.reshape(odds_clean, (int(len(teams) / 2), 3))
        combined = np.concatenate((teams_np,odds_np),axis=1)

        # save to object instance
        self.PINACLE = pd.DataFrame(data = combined[0:, 0:], columns = ["HomeTeam", "AwayTeam", "PSH", "PSD", "PSA"])

    def bet365(self):
        pass

    def bwin(self):
        url = "https://sports.bwin.com/en/sports/football-4/betting/england-14/premier-league-46"
        self.driver.get(url)

        # sleep(20)
        # wait until web page has loaded
        wait = WebDriverWait(self.driver, 20)
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
            self.warnings = True

        teams_np = np.reshape(teams, (int(len(teams) / 2), 2))
        odds_np = np.reshape(odds_decimal, (int(len(teams) / 2), 3))
        combined = np.concatenate((teams_np, odds_np), axis = 1)

        self.BWIN = pd.DataFrame(data = combined[0:, 0:], columns = ["HomeTeam", "AwayTeam", "BWH", "BWD", "BWA"])

    def williamhill(self):
        url = "https://sports.williamhill.com/betting/en-gb/football/competitions/OB_TY295/English-Premier-League/matches/OB_MGMB/Match-Betting"
        self.driver.get(url)
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "main")))
        fixtures_tags = self.driver.find_elements_by_css_selector("main.sp-o-market__title")
        teams = []
        for f in fixtures_tags:
            home, away = f.text.split(" v ")
            home = team_cleaner(team = home)
            away = team_cleaner(team = away)
            teams.append(home)
            teams.append(away)

        odds = self.driver.find_elements_by_css_selector("button.sp-betbutton:not(.sp-betbutton--enhanced):not(.sp-betbutton--super-odds")
        odds_clean = []
        for o in odds:
            odds_clean.append(o.text)

        # convert odds to deci
        odds_decimal = convert_to_decimal(odds_clean)

        # check that we're getting shape
        if int(len(teams) / 2) * 3 != len(odds_decimal):
            print(colored(
                "WARNING: WILLIAM HILL: The number of odds collected does NOT match the expected number of fixtures collected. Please check this",
                'red'))
            self.warnings = True


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
        #self.interwetten()
        #self.bet365()
        self.driver.close()
        # load weekly user predictions

        fixtures = pd.read_csv("/Users/benjamin/PycharmProjects/APPLE/data/predictions/week" + str(self.week ) + "/week" + str(self.week ) + "up.csv")
        fixtures = fixtures[["HomeTeam", "AwayTeam"]]
        # find out how to mergre all of the dfs
        intermediate_1 = fixtures.merge(self.PINACLE, on = ["HomeTeam", "AwayTeam"], how = "left")
        intermediate_2 = intermediate_1.merge(self.BWIN, on = ["HomeTeam", "AwayTeam"], how = "left")
        output = intermediate_2.merge(self.WH, on = ["HomeTeam", "AwayTeam"], how = "left")
        output.to_json("/Users/benjamin/PycharmProjects/APPLE/data/mined_data/w"+str(self.week) + "f.json")
        # eventually return the mined data as a df that can be passed directly to
        # model preprocessing, but for now return to a dir
        # return output

