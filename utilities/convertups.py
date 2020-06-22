"""
Script used to convert xlsx to csv
"""

import pandas as pd


df = pd.read_excel("~/Downloads/week31up.xlsx")
df.to_csv("~/Downloads/week31up.csv", index= False, index_label = False)

