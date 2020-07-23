"""
Script used to convert xlsx to csv
"""

import pandas as pd
from core.miners import team_cleaner

df = pd.read_excel("~/Downloads/week35up.xlsx")

df["HomeTeam"] = df.apply(lambda x: team_cleaner(x["HomeTeam"]), axis = 1)
df["AwayTeam"] = df.apply(lambda x: team_cleaner(x["AwayTeam"]), axis = 1)
df.to_csv("~/Downloads/week35up.csv", index= False, index_label = False)

