import pandas as pd
from pathlib import Path
import plotly.express as px
from analytics.results import calculate_accuracy_transform


# /// --- VIOLIN PLOT --- \\\
# This VIOLIN plot uses the calculate_accuracy_transform def to
# transform the aggregated weekly results into a box plot that
# helps visualise the spread (or volatility) of predictions made

# loading data into memory
path = str(Path().absolute().parent)
data_dir = path + "/data"
aggregated_results_loc = data_dir + "/aggregated_results/20_21/predictions_and_results_log.csv"
aggregated_results = pd.read_csv(aggregated_results_loc)

# use calculate_accuracy_transform to transform aggregated_results
weekly_summed = calculate_accuracy_transform(aggregated_results, mode = "weekly")

#fig = px.violin(weekly_summed, y="Accuracy of Predictions (%)", x ="Predictor", points = "all", box=True, hover_data=weekly_summed.columns, template="simple_white")
#fig.show()
#fig.write_html(path + "/analytics/test.html")


# /// --- TIME SERIES --- \\\
fig2 = px.line(weekly_summed, x="Week", y="Accuracy of Predictions (%)", color="Predictor", hover_name="Predictor")
fig2.show()



# /// --- POLAR PLOT --- \\\


top_6_teams = ["Arsenal", "Liverpool", "Chelsea", "Man City", "Man United", "Tottenham"]
newly_promoted_teams = ["Leeds", 'Fulham', "West Brom"]
f_df = aggregated_results[(aggregated_results["AwayTeam"].isin(newly_promoted_teams))| (aggregated_results["HomeTeam"].isin(newly_promoted_teams))]
f_df_accuracy_transform = calculate_accuracy_transform(f_df, mode = "overall")
fig = px.bar_polar(f_df_accuracy_transform, r="Accuracy of Predictions (%)", theta="Predictor", color = "Predictor", template="simple_white")
fig.show()

