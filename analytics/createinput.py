"""
Scirpt used to collate odds and format them to json file for feeding to the model
"""

import pandas as pd
import pathlib

path = str(pathlib.Path().absolute().parent)

# load in user predictions
fix_cols_data = pd.read_csv(path + "data/user_predictions/20_21/week1/week1userpredictions.csv")

# use user predictions to grab fixtures
Date = fix_cols_data['Date'].tolist()
Week = fix_cols_data['Week'].tolist()
Time = fix_cols_data['Time'].tolist()
HomeTeam = fix_cols_data['HomeTeam'].tolist()
AwayTeam = fix_cols_data['AwayTeam'].tolist()

fix_lists = [Date, Week, Time, HomeTeam, AwayTeam]
fix_cols = ['Date', 'Week', 'Time', 'HomeTeam', 'AwayTeam']

# input odds here for the fixtures
B365H = ["10/11", "13/10", "17/20", "5/1",  "6/5" ,  "2/1",   "1/12", "13/2", "23/20",  "2/1"]
B365D = ["14/5", "12/5",   "14/5",  "16/5",  "29/10", "10/1", "10/1", "17/4", "5/2",    "13/5"]
B365A = ["14/5", "21/10",  "3/1",   "11/20", "19/10", "25/1", "25/1", "4/11",  "23/10", "13/10"]


IWH = ["1.95", "2.30", "1.95", "6.00", "2.25", "3.20", "1.05", "7.00", "2.15", "3.00"]
IWD = ["3.80", "3.30", "3.45", "3.95", "3.35", "3.30", "14.0", "4.80", "3.35", "3.40"]
IWA = ["3.75", "3.05", "4.00", "1.57", "3.00", "2.25", "35.0", "1.43", "3.40", "2.30"]

odss_cols = ['B365A', 'B365D', 'B365H', 'IWA', 'IWD', 'IWH']
odss_lists = [B365A, B365D, B365H, IWA, IWD, IWH]

# check lens of all lsits

for a in odss_lists:
    check = len(a)
    if check != 10:
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
        x[i] = str(val)

# turn into a df and output to json
out_lists = fix_lists + odss_lists
out_cols = fix_cols + odss_cols
outputs = {}

for i in range(len(out_lists)):
    outputs.update({out_cols[i]: out_lists[i]})

df = pd.DataFrame(data = outputs)
df.to_json(path + "/data/mined_data/w35f_incomp.json")