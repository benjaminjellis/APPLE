import pandas as pd
from pathlib import Path
import plotly.express as px
from analytics.results import calculate_accuracy_transform


# /// --- BOX PLOT --- \\\
# This box plot uses the calculate_accuracy_transform def to
# transform the aggregated weekly results into a box plot that
# helps visualise the spread (or volatility) of predictions made

# loading data into memory
path = str(Path().absolute().parent)
data_dir = path + "/data"
aggregated_results_loc = data_dir + "/aggregated_results/20_21/predictions_and_results_log.csv"
aggregated_results = pd.read_csv(aggregated_results_loc)

# use calculate_accuracy_transform to transform aggregated_results
weekly_summed = calculate_accuracy_transform(aggregated_results, mode = "weekly")

fig = px.box(weekly_summed, y="Accuracy of Predictions (%)", x ="Predictor", points = "all" )
fig.show()
#fig.write_html(path + "/analytics/test.html")


