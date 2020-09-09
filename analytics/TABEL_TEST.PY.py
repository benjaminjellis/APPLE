import pandas as pd


d = {"Name": ["A", "B", "C", "D", "E", "F", "G"],
     "Result": [0.9, 0.8, 0.55, 0.67, 0.9, 0.4, 0.35]}

df = pd.DataFrame(data = d)


def winners_from_dataframe(dataframe):
    winners_str_to_return = ""
    max_val = dataframe["Result"].max()
    winners = dataframe[dataframe["Result"] == max_val]["Name"].to_list()
    for winner in winners:
        winners_str_to_return += winner + ", "
    return winners_str_to_return


winner_str = winners_from_dataframe(dataframe = df)
print(winner_str)
