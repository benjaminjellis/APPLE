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
B365A = ["12/5", "3/4", "11/2", "21/10", "17/10", "4/6", "1/1", "11/5", "11/8", "11/2", "12/1", "11/5", "13/2", "6/4", "19/10", "1/3", "1/4"]
B365D = ["11/5", "5/2", "7/2", "11/5", "12/5", "3/1", "23/10", "13/5", "9/4", "3/1", "15/4", "12/5", "7/2", "11/5", "9/4", "4/1", "9/2"]
B365H = ["5/4", "15/4", "9/20", "11/8", "6/4", "15/4", "11/4", "11/10", "2/1", "8/15", "2/7", "6/5", "2/5", "9/5", "7/5", "7/1",  "12/1"]

BWH = ["5/4", "15/4", "1/2", "13/10", "31/20", "15/4", "27/10", "23/20", "2/1", "11/20", "13/50", "5/4", "21/50", "37/2", "29/20", "33/100", "9/1"]
BWD = ["11/5", "27/10", "18/5", "9/4", "12/5", "31/10", "12/5", "13/5", "23/10", "31/10", "9/2", "12/5", "18/5", "21/10", "23/10", "9/2", "9/2"]
BWA = ["12/5", "3/4", "5/1", "11/5", "7/4", "67/10", "21/20", "9/4", "7/5", "21/4", "25/2", "9/4", "13/2", "33/20", "39/20", "31/4", "3/10"]

IWH = ["2.35", "4.90", "1.50", "2.35", "2.55", "4.95", "3.9", "2.15", "3.05", "1.57", "1.27", "2.2", "1.45", "2.85", "2.50", "1.36", "9.2"]
IWD = ["3.10", "3.65", "4.40", "3.15", "3.30", "4.05", "3.35", "3.75", "3.30", "4.00", "5.7", "3.4", "4.55", "3.00", "3.3", "5.30", "5.30"]
IWA = ["3.35", "1.75", "6.30", "3.25", "2.8", "1.67", "2.0", "3.15", "2.35", "6.3", "11.5", "3.3", "7.00", "2.7", "2.85", "7.80", "1.32"]

PSH = ["2.4", "5.15", "1.505", "2.38", "2.58", "5.21", "4.06", "2.14", "3.28", "1.55", "1.254", "2.2", "1.409", "2.87", "2.58", "1.357", "10.21"]
PSD = ["3.14", "3.71", "4.5", "3.18", "3.36", "4.17", "3.44", "3.93", "3.37", "4.11", "6.28", "3.45", "4.77", "3.050", "3.32", "5.520", "5.49"]
PSA = ["3.4", "1.763", "6.7", "3.39", "2.9", "1.671", "2.03", "3.24", "2.39", "6.91", "13.44", "3.49", "8.93", "2.83", "2.92", "8.820", "1.331"]

WHH = ["13/10", "4/1", "47/100", "27/20", "31/20", "17/4", "3/1", "23/20", "2/1", "8/15", "1/4", "6/5", "42/100", "15/8", "1/3", "8/1", "9/1"]
WHD = ["21/10", "13/5", "17/5", "21/10", "23/10", "31/1", "23/10", "11/4", "23/10", "23/10", "24/5", "12/5", "18/5", "2/1", "23/10", "17/4", "17/4"]
WHA = ["12/5", "3/4", "6/1", "23/10", "9/5", "63/100", "2/1", "21/10", "7/5", "6/1", "12/1", "23/10", "7/1", "17/10", "15/8", "6/4", "32/100"]

odss_cols = ['B365A', 'B365D', 'B365H', 'BWA', 'BWD', 'BWH', 'IWA', 'IWD', 'IWH', 'PSA', 'PSD', 'PSH', 'WHA', 'WHD', 'WHH']
odss_lists = [B365A, B365D, B365H, BWA, BWD, BWH, IWA, IWD, IWH, PSA, PSD, PSH, WHA, WHD, WHH]

# check lens of all lsits

for a in odss_lists:
    check = len(a)
    if check != 17:
        raise Exception("List not the right length: " + str(a) + ". List has " + str(check) + " elements. Expected 17")


# convert all odds given
for x in odss_lists:
    for i in range(0,len(x)):
        if "/" in x[i]:
            n, d = x[i].split("/")
            n, d = int(n), int(d)
            val = n/d + 1
        else:
            val = float(x[i])
        x[i] = val

# turn into a df and output to json
out_lists = fix_lists + odss_lists
out_cols = fix_cols + odss_cols
outputs = {}

for i in range(len(out_lists)):
    outputs.update({out_cols[i]: out_lists[i]})

df = pd.DataFrame(data = outputs)
df.to_json(path + "/fixtures/w32f.json")