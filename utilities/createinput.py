"""
Scirpt used to collate odds and format them to json file for feeding to the model
"""

import pandas as pd
import pathlib

path = str(pathlib.Path().absolute().parent)

# load in user predictions
fix_cols_data = pd.read_csv(path + "/data/predictions/week33/week33up.csv")

# use user predictions to grab fixtures
Date = fix_cols_data['Date'].tolist()
Week = fix_cols_data['Week'].tolist()
Time = fix_cols_data['Time'].tolist()
HomeTeam = fix_cols_data['HomeTeam'].tolist()
AwayTeam = fix_cols_data['AwayTeam'].tolist()

fix_lists = [Date, Week, Time, HomeTeam, AwayTeam]
fix_cols = ['Date', 'Week', 'Time', 'HomeTeam', 'AwayTeam']

# input odds here for the fixtures
B365H = ["10/11","13/2", "13/20", "5/4", "1/8", "14/5", "1/1",      "5/1", "4/1",    "1/1", "8/1", "11/5",  "5/6",   "2/7",   "11/2", "17/2", "11/10", "5/4", "13/10",  "15/4"]
B365D = ["13/5", "10/3", "29/10", "5/2",  "8/1", "11/5", "12/5",     "10/3", "3/1",  "13/5", "9/2", "5/2",  "5/2",   "9/2",   "3/1", "17/4", "11/5", "23/10", "5/2",  "11/4"]
B365A = ["3/1" , "9/20", "17/4", "21/10",  "20/1", "11/10", "29/10", "8/15", "8/13", "5/2", "3/10", "23/20", "10/3",  "17/2", "8/15", "3/10", "13/5", "23/10", "15/8",  "7/10"]


IWH = ["1.95", "7.10", "1.67", "2.30", "1.13", "3.95", "2.00", "5.80", "5.00", "2.05", "8.90", "3.25", "1.87", "1.30", "6.20", "8.60", "2.15", "2.25", "2.35", "4.90" ]
IWD = ["3.55", "4.35", "3.85", "3.45", "8.50", "3.05", "3.35", "4.15", "4.00", "3.50", "5.1", "3.50", "3.50", "5.70", "4.00", "5.20", "3.29", "3.35", "3.50", "3.80" ]
IWA = ["3.90", "1.47", "5.30", "3.05", "20.00", "2.10", "3.90", "1.57", "1.67", "3.65", "1.35", "2.15", "4.25", "9.40", "1.57", "1.35", "3.60", "3.25", "2.90", "1.70" ]

odss_cols = ['B365A', 'B365D', 'B365H', 'IWA', 'IWD', 'IWH']
odss_lists = [B365A, B365D, B365H, IWA, IWD, IWH]

# check lens of all lsits

for a in odss_lists:
    check = len(a)
    if check != 20:
        print(check)
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
df.to_json(path + "/data/mined_data/w33f_incomp.json")