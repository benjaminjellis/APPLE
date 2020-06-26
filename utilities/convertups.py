"""
Script used to convert xlsx to csv
"""

import pandas as pd


df = pd.read_excel("~/Downloads/week32up.xlsx")
df.to_csv("~/Downloads/week32up.csv", index= False, index_label = False)

