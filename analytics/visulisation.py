from pathlib import Path
import plotly.express as px
from analytics.results import calculate_accuracy_transform
from core.loaders import load_json_or_csv


class Visualisation(object):

    def __init__(self, aggregated_results_filepath):
        # define path
        self.path = str(Path().absolute())
        # user loader to load aggregated results file
        self.aggregated_results = load_json_or_csv(self.path + "/" + aggregated_results_filepath)
        # use calculate_accuracy_transform def to create the weekly summed
        self.weekly_summed = calculate_accuracy_transform(self.aggregated_results, mode = "weekly")

    def volatility(self, output_filepath = None):
        """
        This VIOLIN plot uses the calculate_accuracy_transform def to
        transform the aggregated weekly results into a box plot that
        helps visualise the spread (or volatility) of predictions made

        :param output_filepath:
        :return: nothing
        """
        fig_violin = px.violin(self.weekly_summed,
                               y = "Accuracy of Predictions (%)",
                               x = "Predictor", points = "all",
                               box = True,
                               hover_data = self.weekly_summed.columns,
                               template = "simple_white")
        # set range of axes
        fig_violin.update_yaxes(range = [0, 100])
        fig_violin.show()
        if output_filepath:
            fig_violin.write_html(self.path + "/analytics/test.html")

    def time_series(self, output_filepath = None):
        fig_ts = px.line(self.weekly_summed,
                         x = "Week",
                         y = "Accuracy of Predictions (%)",
                         color = "Predictor",
                         hover_name = "Predictor")
        fig_ts.show()
        if output_filepath:
            fig_ts.write_html(self.path + "/analytics/test.html")

    def stratified_performance(self, metric, output_filepath = None):
        if metric == "top 6 teams":
            sp_filter = ["Arsenal", "Liverpool", "Chelsea", "Man City", "Man United", "Tottenham"]
        elif metric == "newly promoted teams":
            sp_filter = ["Leeds", 'Fulham', "West Brom"]
        else:
            raise AttributeError("Metric not recognised. Please try 'top 6 teams' or 'newly promoted teams")
        # filter the df
        f_df = self.aggregated_results[(self.aggregated_results["AwayTeam"].isin(sp_filter)) | (
            self.aggregated_results["HomeTeam"].isin(sp_filter))]
        # calculate the accuracy transform
        f_df_accuracy_transform = calculate_accuracy_transform(f_df, mode = "overall")
        fig_sp = px.bar_polar(f_df_accuracy_transform,
                              r = "Accuracy of Predictions (%)",
                              theta = "Predictor",
                              color = "Predictor",
                              template = "simple_white")
        fig_sp.show()
        if output_filepath:
            fig_sp.write_html(self.path + "/analytics/test.html")
