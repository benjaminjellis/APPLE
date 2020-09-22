import pandas as pd
from pathlib import Path
path = str(Path().absolute().parent)
data_dir = path + "/data"
aggregated_results_loc = data_dir + "/aggregated_results/20_21/predictions_and_results_log.csv"
print(aggregated_results_loc)
aggregated_results = pd.read_csv(aggregated_results_loc)

import plotly.express as px

def correct_pred(col1, col2):
    if col1 == col2:
        return 1
    else:
        return 0

# take the weeks present
weeks_present = set(aggregated_results["Week"].to_list())
# names of the predictors

user_prediction_cols = []
aggregated_results_cols = aggregated_results.columns.to_list()

for col in aggregated_results_cols:
    if "Prediction" in col:
        user_prediction_cols.append(col)

weekly_summed = pd.DataFrame(columns=['Predictor','Correct Predictions','Week','Accuracy of Predictions (%)'])

# filter for each week
for week in weeks_present:
    filtered_aggregated_results = aggregated_results[aggregated_results["Week"] == week].reset_index()
    no_matches = filtered_aggregated_results.shape[0]
    predictors = []
    for col in user_prediction_cols:
        predictors.append(col.strip(" Prediction"))
        filtered_aggregated_results[col.strip(" Prediction")] = filtered_aggregated_results.apply(lambda x: correct_pred(x[col], x['FTR']), axis=1)
    correct_res = filtered_aggregated_results.sum()
    correct_res = correct_res[predictors]
    summed_results_df = pd.DataFrame({'Predictor': correct_res.index, 'Correct Predictions': correct_res.values})
    summed_results_df["Week"] = week
    summed_results_df['Accuracy of Predictions (%)'] = (summed_results_df['Correct Predictions'] / no_matches) * 100
    weekly_summed = pd.concat([weekly_summed, summed_results_df], ignore_index=True)


fig = px.box(weekly_summed, y="Accuracy of Predictions (%)", x ="Predictor", points = "all" )
fig.show()
fig.write_html(path + "/analytics/test.html")
