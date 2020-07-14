"""
Script used to convert xlsx to csv
"""

import pandas as pd


df = pd.read_excel("~/Downloads/week34.xlsx")
df.to_csv("~/Downloads/week34up.csv", index= False, index_label = False)

