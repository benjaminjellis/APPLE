"""
Script used to convert xlsx to csv
"""

import pandas as pd


df = pd.read_excel("~/Downloads/week33up.xlsx")
df.to_csv("~/Downloads/week33up.csv", index= False, index_label = False)

