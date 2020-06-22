"""
Scirpt used to collate odds and format them to json file for feeding to the model
"""

import pandas as pd
import pathlib

path = str(pathlib.Path().absolute().parent)

# load in user predictions
fix_cols_data = pd.read_csv(path + "/predictions/week32/week32up.csv")

# use user predictions to grab fixtures
Date = fix_cols_data['Date'].tolist()
Week = fix_cols_data['Week'].tolist()
Time = fix_cols_data['Time'].tolist()
HomeTeam = fix_cols_data['HomeTeam'].tolist()
AwayTeam = fix_cols_data['AwayTeam'].tolist()

fix_lists = [Date, Week, Time, HomeTeam, AwayTeam]
fix_cols = ['Date', 'Week', 'Time', 'HomeTeam', 'AwayTeam']

# input odds here for the fixtures
B365H = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
B365D =["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
B365A = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
BWH = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
BWD = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
BWA = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
IWH = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
IWD = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
IWA = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
PSH = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
PSD = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
PSA = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
WHH = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
WHD = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]
WHA = ["1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9", "1/9",  "1/9"]

odss_cols = ['B365A', 'B365D', 'B365H', 'BWA', 'BWD', 'BWH', 'IWA', 'IWD', 'IWH', 'PSA', 'PSD', 'PSH', 'WHA', 'WHD', 'WHH']
odss_lists = [B365A, B365D, B365H, BWA, BWD, BWH, IWA, IWD, IWH, PSA, PSD, PSH, WHA, WHD, WHH]

# convert all odds given
for x in odss_lists:
    for i in range(0,len(x)):
        if "/" in x[i]:
            n, d = x[i].split("/")
            n, d = int(n), int(d)
            val = n/d + 1
        else:
            pass
        x[i] = val

# turn into a df and output to json
out_lists = fix_lists + odss_lists
out_cols = fix_cols + odss_cols
outputs = {}
for i in range(len(out_lists)):
    outputs.update({out_cols[i]: out_lists[i]})

df = pd.DataFrame(data = outputs)
df.to_json(path + "fixtures/w32f.json")