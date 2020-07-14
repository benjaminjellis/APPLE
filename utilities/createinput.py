"""
Scirpt used to collate odds and format them to json file for feeding to the model
"""

import pandas as pd
import pathlib

path = str(pathlib.Path().absolute().parent)

# load in user predictions
fix_cols_data = pd.read_csv(path + "/data/predictions/week34/week34up.csv")

# use user predictions to grab fixtures
Date = fix_cols_data['Date'].tolist()
Week = fix_cols_data['Week'].tolist()
Time = fix_cols_data['Time'].tolist()
HomeTeam = fix_cols_data['HomeTeam'].tolist()
AwayTeam = fix_cols_data['AwayTeam'].tolist()

fix_lists = [Date, Week, Time, HomeTeam, AwayTeam]
fix_cols = ['Date', 'Week', 'Time', 'HomeTeam', 'AwayTeam']

# input odds here for the fixtures
B365H = ["2/7", "1/8", "7/2", "1/7" , "7/2",  "11/4", "19/20", "19/20", "17/2",  "11/8"]
B365D = ["2/7", "17/2", "12/5", "8/1", "11/4", "14/5","13/5", "23/10", "4/1", "2/1" ]
B365A = ["2/7", "16/1", "5/6", "14/1", "3/4",  "17/20","11/4", "3/1" , "1/3",  "9/4" ]


IWH = ["1.30", "1.12", "4.70", "1.15", "4.50", "3.80", "2.00", "2.00", "9.30", "2.40"]
IWD = ["5.60", "9.00", "3.25", "8.40", "3.70", "3.85", "3.55", "3.30", "4.85", "3.00"]
IWA = ["9.50", "20.00", "1.87", "15.50", "1.80", "1.90", "3.70", "3.95", "1.36", "3.30"]

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
print(out_lists)
for i in range(len(out_lists)):
    print(out_cols[i])
    print(len(out_cols[i]))
    print(len(out_lists[i]))
    outputs.update({out_cols[i]: out_lists[i]})

df = pd.DataFrame(data = outputs)
df.to_json(path + "/data/mined_data/w44f_incomp.json")